import logging
from core import db

logger = logging.getLogger(__name__)

def dispatch(action: str, params: dict, id_account: int) -> dict | list | str | None:
    try:
        return _route(action, params, id_account)
    except Exception as e:
        logger.error(f"Dispatcher error pada action '{action}': {e}")
        return None


def _route(action: str, params: dict, id_account: int) -> dict | list | str | None:
    if action == "static":
        return params.get("content", "")

    if action == "create_eskalasi":
        pesan = params.get("pesan_eskalasi", "").strip()
        if not pesan:
            return {"status": "error", "message": "Pesan tidak boleh kosong."}
        return db.handle_eskalasi(pesan, id_account)

    if action == "get_jadwal_terdekat":
        return db.get_jadwal_terdekat()

    if action == "get_jadwal_mendatang":
        return db.get_jadwal_pertandingan(status="Akan Datang")

    if action == "get_jadwal_selesai":
        return db.get_jadwal_pertandingan(status="Selesai")

    if action == "get_jadwal_by_lawan":
        nama_lawan = params.get("nama_lawan", "").strip()
        return db.get_jadwal_by_lawan(nama_lawan)

    if action == "get_stok_tiket_terdekat":
        return db.get_stok_tiket_terdekat()

    if action == "get_stok_tiket_by_lawan":
        nama_lawan = params.get("nama_lawan", "").strip()
        return db.get_stok_tiket_by_lawan(nama_lawan)

    if action == "check_merch_stock":
        name = params.get("name", "").strip()
        return db.check_merch_stock(name)

    if action == "get_all_merch":
        return db.get_all_merch()

    if action == "get_pemain_by_nama":
        nama = params.get("nama_pemain", "").strip()
        return db.get_pemain_by_nama(nama)

    if action == "get_pemain_by_posisi":
        posisi = params.get("posisi", "").strip()
        return db.get_pemain_by_posisi(posisi)

    if action == "get_pemain_by_status":
        status = params.get("status", "").strip()
        return db.get_pemain_by_status(status)

    logger.warning(f"Action tidak dikenal: '{action}'")
    return None