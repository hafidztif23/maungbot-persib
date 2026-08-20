import pytest
from unittest.mock import patch, MagicMock

from core.loader import _validate
from core.engine import _execute_menu_state, _execute_transitional, _execute_terminal
from core import db
from core.dispatcher import dispatch


def test_ut01_load_state_menu_state_tidak_lengkap():
    """UT-01: Memuat node menu_state tanpa field message atau options."""
    # user_menu_utama tidak lengkap (hanya ada type)
    nodes = {"user_menu_utama": {"id": "user_menu_utama", "type": "menu_state"}} 
    
    with pytest.raises(RuntimeError, match="Validasi data.json gagal"):
        _validate(nodes)


def test_ut02_load_state_menu_state_lengkap():
    """UT-02: Memuat node menu_state dengan field lengkap."""
    nodes = {
        "user_menu_utama": {
            "id": "user_menu_utama", 
            "type": "menu_state", 
            "message": "Menu Utama", 
            "options": {"1": "jadwal"}
        },
        "jadwal": {
            "id": "jadwal", 
            "type": "menu_state", 
            "message": "Menu Jadwal", 
            "options": {}
        }
    }
    # Fungsi _validate tidak akan mengembalikan error (lulus validasi)
    _validate(nodes)


def test_ut03_load_state_transitional_tidak_lengkap():
    """UT-03: Memuat node transitional tanpa field wajib (misal action/back_to)."""
    nodes = {
        "user_menu_utama": {"id": "user_menu_utama", "type": "menu_state", "message": "Pilih:", "options": {"1": "input"}},
        "input": {"id": "input", "type": "transitional_state", "message": "Ketik:"}
    }
    
    with pytest.raises(RuntimeError, match="Validasi data.json gagal"):
        _validate(nodes)


def test_ut04_load_state_terminal_tidak_lengkap():
    """UT-04: Memuat node terminal_state tanpa field wajib."""
    nodes = {
        "user_menu_utama": {"id": "user_menu_utama", "type": "menu_state", "message": "Pilih:", "options": {"1": "hasil"}},
        "hasil": {"id": "hasil", "type": "terminal_state"}
    }
    
    with pytest.raises(RuntimeError, match="Validasi data.json gagal"):
        _validate(nodes)


@patch("core.engine.save_session")
def test_ut05_handle_menu_state(mock_save_session):
    """UT-05: Memanggil fungsi _execute_menu_state dan menyimpan sesi."""
    node = {"message": "Menu Utama", "options": {}}
    
    response = _execute_menu_state(1, "user_menu_utama", node)
    
    mock_save_session.assert_called_once_with(1, "user_menu_utama")
    assert "Menu Utama" in response


@patch("core.engine.save_session_waiting")
def test_ut06_handle_transitional_state(mock_save_waiting):
    """UT-06: Memanggil fungsi _execute_transitional pada node input."""
    node = {
        "message": "Masukkan nama lawan:",
        "action": "get_jadwal_by_lawan",
        "param_key": "nama_lawan",
        "back_to": "jadwal"
    }
    
    response = _execute_transitional(1, "jadwal_by_lawan_input", node)
    
    mock_save_waiting.assert_called_once_with(
        id_account=1,
        current_node="jadwal_by_lawan_input",
        pending_action="get_jadwal_by_lawan",
        pending_param_key="nama_lawan",
        pending_back_to="jadwal"
    )
    assert response == "Masukkan nama lawan:"


@patch("core.engine.save_session_waiting")
@patch("core.engine.dispatch")
@patch("core.engine.save_session")
def test_ut07_handle_terminal_state_static(mock_save, mock_dispatch, mock_save_waiting):
    """UT-07: Action 'static' mengembalikan teks statis, transisi ke menu_state biasa."""
    node = {
        "action": "static",
        "content": "Info Sejarah Persib",
        "back_to": "sejarah"
    }
    nodes_mock = {
        "sejarah": {"type": "menu_state", "message": "Kembali ke Menu Sejarah"}
    }
    mock_dispatch.return_value = "Info Sejarah Persib"

    response = _execute_terminal(1, "sejarah_singkat", node, nodes_mock)

    mock_dispatch.assert_called_once_with("static", {"content": "Info Sejarah Persib"}, 1)
    mock_save.assert_called_once_with(1, "sejarah")
    mock_save_waiting.assert_not_called()
    assert "Info Sejarah Persib" in response
    assert "Kembali ke Menu Sejarah" in response


@patch("core.engine.save_session_waiting")
@patch("core.engine.dispatch")
@patch("core.engine.save_session")
def test_ut08_handle_terminal_state_db(mock_save, mock_dispatch, mock_save_waiting):
    """UT-08: Action query DB memanggil dispatcher dan menerima hasil, transisi ke menu_state biasa."""
    node = {
        "action": "get_jadwal_terdekat",
        "back_to": "jadwal"
    }
    nodes_mock = {
        "jadwal": {"type": "menu_state", "message": "Menu Jadwal"}
    }

    mock_dispatch.return_value = [{"lawan": "Persija", "lokasi": "GBLA", "status_pertandingan": "Akan Datang"}]

    response = _execute_terminal(1, "cek_jadwal", node, nodes_mock)

    mock_dispatch.assert_called_once_with("get_jadwal_terdekat", {}, 1)
    mock_save.assert_called_once_with(1, "jadwal")
    mock_save_waiting.assert_not_called()
    assert "Menu Jadwal" in response


def test_ut09_dispatch_action_terdaftar():
    """UT-09: Menguji fungsi dispatcher untuk aksi yang ada."""
    mock_result = {"lawan": "Persija", "tanggal_jam": "10 Agustus 2025"}
    
    with patch("core.dispatcher.db.get_jadwal_terdekat", return_value=mock_result):
        result = dispatch("get_jadwal_terdekat", {}, id_account=1)
    
    assert result == mock_result


def test_ut10_dispatch_action_tidak_terdaftar():
    """UT-10: Menguji fungsi dispatcher untuk aksi yang tidak terdaftar."""
    result = dispatch("action_yang_tidak_ada", {}, id_account=1)
    assert result is None  


@patch("core.db.engine.connect")
def test_ut11_get_jadwal_terdekat(mock_connect):
    """UT-11: Mengembalikan satu data jadwal dari PostgreSQL."""
    mock_conn = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    
    mock_row = {
        "id_jadwal": 1, 
        "lawan": "Persija", 
        "tanggal_jam": MagicMock(), 
        "lokasi": "GBLA", 
        "kompetisi": "Liga 1", 
        "status_pertandingan": "Akan Datang"
    }
    mock_row["tanggal_jam"].strftime.return_value = "10 Agustus 2025, 15:30 WIB"
    
    mock_conn.execute.return_value.mappings.return_value.fetchone.return_value = mock_row
    
    result = db.get_jadwal_terdekat()
    
    assert result is not None
    assert result["lawan"] == "Persija"
    assert result["tanggal_jam"] == "10 Agustus 2025, 15:30 WIB"


@patch("core.db.engine.connect")
def test_ut12_get_jadwal_by_lawan(mock_connect):
    """UT-12: Mengembalikan jadwal pertandingan berdasarkan string tim lawan."""
    mock_conn = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    
    mock_row = {
        "id_jadwal": 1, "lawan": "Persebaya", "tanggal_jam": MagicMock(),
        "lokasi": "GBLA", "kompetisi": "Liga 1", "status_pertandingan": "Akan Datang"
    }
    mock_row["tanggal_jam"].strftime.return_value = "12 Agustus 2025, 15:30 WIB"
    
    mock_conn.execute.return_value.mappings.return_value.all.return_value = [mock_row]
    
    result = db.get_jadwal_by_lawan("Persebaya")
    assert len(result) > 0
    assert result[0]["lawan"] == "Persebaya"


@patch("core.db.engine.connect")
def test_ut13_get_pemain_by_posisi(mock_connect):
    """UT-13: Mengembalikan daftar pemain dengan posisi spesifik."""
    mock_conn = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    
    mock_row = {
        "id_pemain": 1, "nama_pemain": "Kevin Mendoza", "nomor_punggung": 1,
        "posisi": "Kiper", "kewarganegaraan": "Filipina", 
        "tanggal_lahir": None, "status": "Aktif"
    }
    
    mock_conn.execute.return_value.mappings.return_value.all.return_value = [mock_row]
    
    result = db.get_pemain_by_posisi("Kiper")
    for player in result:
        assert player["posisi"] == "Kiper"


@patch("core.db.engine.connect")
def test_ut14_get_pemain_by_status(mock_connect):
    """UT-14: Mengembalikan daftar pemain berdasarkan status."""
    mock_conn = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    
    mock_row = {
        "id_pemain": 13, "nama_pemain": "Febri Hariyadi", "nomor_punggung": 13,
        "posisi": "Gelandang", "kewarganegaraan": "Indonesia", "status": "Cedera"
    }
    
    mock_conn.execute.return_value.mappings.return_value.all.return_value = [mock_row]
    
    result = db.get_pemain_by_status("Cedera")
    for player in result:
        assert player["status"] == "Cedera"


@patch("core.db.engine.connect")
def test_ut15_check_merch_stock(mock_connect):
    """UT-15: Mengembalikan jumlah stok produk."""
    mock_conn = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    
    mock_row = {"name": "Jersey Persib 2025", "stock": 50, "harga_merchandise": 400000}
    mock_conn.execute.return_value.mappings.return_value.fetchone.return_value = mock_row
    
    result = db.check_merch_stock("Jersey Persib 2025")
    assert result["name"] == "Jersey Persib 2025"
    assert result["stock"] == 50