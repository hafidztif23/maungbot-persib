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
        lawan = item.get("tim_lawan", "-")
        tanggal = item.get("tanggal", "-")
        waktu = item.get("waktu", "-")
        stadion = item.get("stadion", "-")
        kompetisi = item.get("kompetisi", "-")
        status = item.get("status", "-")
        lines.append(
            f" vs {lawan}\n"
            f"   {tanggal} | {waktu}\n"
            f"   {stadion}\n"
            f"   {kompetisi} | Status: {status}"
        )
    return "\n\n".join(lines)


def _format_stok_tiket(result) -> str:
    if not result:
        return "Tidak ada data tiket yang ditemukan."

    if isinstance(result, dict):
        result = [result]

    lines = ["Stok Tiket Pertandingan:\n"]
    for item in result:
        lawan = item.get("tim_lawan", "-")
        tribun = item.get("tribun", "-")
        stok = item.get("stok", 0)
        harga = item.get("harga", 0)
        lines.append(
            f" vs {lawan}\n"
            f" Tribun  : {tribun}\n"
            f" Stok    : {stok} tiket\n"
            f" Harga   : Rp {harga:,.0f}"
        )
    return "\n\n".join(lines)


def _format_harga_tiket(result) -> str:
    if not result:
        return "Tidak ada data harga tiket."

    if isinstance(result, dict):
        result = [result]

    lines = ["Daftar Harga Tiket Persib:\n"]
    for item in result:
        tribun = item.get("tribun", "-")
        harga = item.get("harga", 0)
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
        status = "Tersedia" if stock > 0 else "Tidak tersedia"
        lines.append(f"   {status} {name} — Rp {harga:,.0f} (stok: {stock})")
    return "\n".join(lines)


def _format_pemain(result) -> str:
    if not result:
        return "Tidak ada data pemain yang ditemukan."

    if isinstance(result, dict):
        result = [result]

    lines = ["Data Pemain Persib:\n"]
    for item in result:
        nama = item.get("name", "-")
        posisi = item.get("posisi", "-")
        no_punggung = item.get("no_punggung", "-")
        status = item.get("status", "-")
        lines.append(
            f"   {no_punggung}. {nama}\n"
            f"      Posisi : {posisi} | Status: {status}"
        )
    return "\n\n".join(lines)