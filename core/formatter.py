from typing import Any

def format_response(action: str, result: Any) -> str:
    if result is None:
        return "Maaf, data tidak ditemukan atau terjadi kesalahan sistem."

    if action == "static":
        return str(result)

    if action in ("get_jadwal_terdekat", "get_jadwal_mendatang",
                  "get_jadwal_selesai", "get_jadwal_by_lawan", "get_jadwal_pertandingan"):
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

    lines = ["📅 Jadwal Pertandingan Persib Bandung:\n"]
    for idx, item in enumerate(result, 1):
        lawan = item.get("lawan") or item.get("tim_lawan") or "-"
        tanggal_jam = item.get("tanggal_jam")
        if not tanggal_jam:
            tanggal = item.get("tanggal", "-")
            waktu = item.get("waktu", "-")
            waktu_str = f"{tanggal} | {waktu}"
        else:
            waktu_str = tanggal_jam

        lokasi = item.get("lokasi") or item.get("stadion") or "-"
        kompetisi = item.get("kompetisi", "-")
        status = item.get("status_pertandingan") or item.get("status") or "-"
        lines.append(
            f"{idx}. ⚽ PERSIB vs {lawan}\n"
            f"   📅 Waktu    : {waktu_str}\n"
            f"   🏟️ Stadion  : {lokasi}\n"
            f"   🏆 Kompetisi: {kompetisi}\n"
            f"   📌 Status   : {status}"
        )
    return "\n\n".join(lines)


def _format_stok_tiket(result) -> str:
    if not result:
        return "Tidak ada data tiket yang ditemukan."

    if isinstance(result, dict):
        result = [result]

    lines = ["Stok Tiket Pertandingan:\n"]
    for item in result:
        lawan = item.get("lawan") or item.get("tim_lawan") or "-"
        tanggal_jam = item.get("tanggal_jam") or "-"
        status = item.get("status_pertandingan") or "-"
        lines.append(f" vs {lawan} ({tanggal_jam}) [{status}]")
        
        tribun_list = item.get("tribun", [])
        if isinstance(tribun_list, list):
            for t in tribun_list:
                nama_t = t.get("nama_tribun") or t.get("tribun") or "-"
                stok = t.get("stok", 0)
                harga = t.get("harga_tiket") or t.get("harga") or 0
                lines.append(f"   Tribun: {nama_t} | Stok: {stok} | Rp {harga:,.0f}")
        else:
            lines.append(f"   Tribun: {tribun_list} | Stok: {item.get('stok', 0)} | Rp {item.get('harga', 0):,.0f}")

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

    lines = ["🏃 Data Pemain Persib Bandung:\n"]
    for item in result:
        nama = item.get("nama_pemain") or item.get("nama") or item.get("name") or "-"
        posisi = item.get("posisi", "-")
        no_punggung = item.get("nomor_punggung") or item.get("no_punggung") or "-"
        kewarganegaraan = item.get("kewarganegaraan", "")
        status = item.get("status", "-")
        
        kwg_str = f" ({kewarganegaraan})" if kewarganegaraan else ""
        lines.append(
            f"   #{no_punggung} {nama}{kwg_str}\n"
            f"      Posisi : {posisi} | Status: {status}"
        )
    return "\n\n".join(lines)