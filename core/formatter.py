from typing import Any

def format_response(action: str, result: Any) -> str:
    if result is None:
        return "Maaf, data tidak ditemukan atau terjadi kesalahan sistem."

    if action == "static":
        return str(result)

    if action == "create_eskalasi":
        if isinstance(result, dict) and result.get("status") == "error":
            return f"{result['message']}"
        return (
            "Pertanyaan anda telah kami teruskan ke tim CS Persib Bandung.\n"
            "Kami akan menghubungi anda secepatnya."
        )

    if action in ("get_jadwal_terdekat", "get_jadwal_mendatang",
                  "get_jadwal_selesai", "get_jadwal_by_lawan"):
        return _format_jadwal(result)

    if action in ("get_stok_tiket_terdekat", "get_stok_tiket_by_lawan"):
        return _format_stok_tiket(result)

    if action == "get_harga_tiket":
        return _format_harga_tiket(result)

    if action == "check_merch_stock":
        return _format_merch_single(result)

    if action == "get_all_merch":
        return _format_merch_all(result)

    if action in ("get_pemain_by_nama", "get_pemain_by_posisi",
                  "get_pemain_by_status"):
        return _format_pemain(result)

    return str(result)

def _format_jadwal(result) -> str:
    if not result:
        return "Tidak ada data jadwal yang ditemukan."

    # Kalau single dict (jadwal terdekat)
    if isinstance(result, dict):
        result = [result]

    lines = ["Jadwal Pertandingan Persib:\n"]
    for item in result:
        lawan = item.get("lawan", "-")
        tanggal_jam = item.get("tanggal_jam", "-")
        lokasi = item.get("lokasi", "-")
        kompetisi = item.get("kompetisi", "-")
        status = item.get("status_pertandingan", "-")
        lines.append(
            f"vs {lawan}\n"
            f"{tanggal_jam}\n"
            f"{lokasi}\n"
            f"{kompetisi} | Status: {status}"
        )
    return "\n\n".join(lines)


def _format_stok_tiket(result) -> str:
    if not result:
        return "Tidak ada data tiket yang ditemukan."

    lawan = result.get("lawan", "-")
    tanggal = result.get("tanggal_jam", "-")
    status = result.get("status_pertandingan", "-")
    tribuns = result.get("tribun", [])
    total = result.get("total_stok", 0)

    lines = [
        f" Stok Tiket Persib vs {lawan}\n"
        f" {tanggal} | Status: {status}\n"
    ]
    for t in tribuns:
        nama_tribun = t.get("nama_tribun", "-")
        stok = t.get("stok", 0)
        harga = t.get("harga_tiket", 0)
        lines.append(
            f"   {nama_tribun}: {stok} tiket — Rp {harga:,.0f}"
        )
    lines.append(f"\n Total stok: {total} tiket")
    return "\n".join(lines)

def _format_harga_tiket(result) -> str:
    if not result:
        return "Tidak ada data harga tiket."

    if isinstance(result, dict):
        result = [result]

    lines = ["Daftar Harga Tiket Persib:\n"]
    for item in result:
        tribun = item.get("nama_tribun", item.get("tribun", "-"))
        harga = item.get("harga_tiket", item.get("harga", 0))
        lines.append(f"   {tribun}: Rp {harga:,.0f}")
    return "\n".join(lines)


def _format_merch_single(result) -> str:
    if not result:
        return "Maaf, data merchandise tidak ditemukan."

    name = result.get("name", "-")
    stock = result.get("stock", 0)
    harga = result.get("harga", 0)
    status = "Tersedia" if stock > 0 else "Habis"

    return (
        f"{name}\n"
        f" Stok   : {stock} pcs | {status}\n"
        f" Harga  : Rp {harga:,.0f}"
    )


def _format_merch_all(result) -> str:
    if not result:
        return "Tidak ada data merchandise."

    lines = ["Semua Merchandise Persib:\n"]
    for item in result:
        name = item.get("name", "-")
        stock = item.get("stock", 0)
        harga = item.get("harga", 0)
        status = "Tersedia" if stock > 0 else "Habis"
        lines.append(f"   {status} {name} — Rp {harga:,.0f} (stok: {stock})")
    return "\n".join(lines)


def _format_pemain(result) -> str:
    if not result:
        return "Tidak ada data pemain yang ditemukan."

    if isinstance(result, dict):
        result = [result]

    lines = ["Data Pemain Persib:\n"]
    for item in result:
        nama = item.get("nama_pemain", "-")
        posisi = item.get("posisi", "-")
        no_punggung = item.get("nomor_punggung", "-")
        status = item.get("status", "-")
        lines.append(
            f"   {no_punggung}. {nama}\n"
            f"      Posisi : {posisi} | Status: {status}"
        )
    return "\n\n".join(lines)