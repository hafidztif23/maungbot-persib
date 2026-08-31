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

    if action == "get_jadwal_terdekat":
        return db.get_jadwal_terdekat()

    if action in ("get_jadwal_pertandingan", "get_jadwal_mendatang", "get_jadwal_selesai"):
        kompetisi = params.get("kompetisi")
        status = params.get("status")
        return db.get_jadwal_pertandingan(kompetisi=kompetisi, status=status)

    if action == "get_jadwal_by_lawan":
        nama_lawan = params.get("nama_lawan", "").strip()
        return db.get_jadwal_by_lawan(nama_lawan)

    if action == "get_stok_tiket_terdekat":
        return db.get_stok_tiket_terdekat()

    if action in ("get_harga_tiket_by_tribun", "get_harga_tiket"):
        res = db.get_stok_tiket_terdekat()
        if res and isinstance(res, dict) and "tribun" in res:
            return [
                {"tribun": t["nama_tribun"], "harga": t["harga_tiket"]}
                for t in res["tribun"]
            ]
        return res

    if action == "get_stok_tiket_by_lawan":
        nama_lawan = params.get("nama_lawan", "").strip()
        return db.get_stok_tiket_by_lawan(nama_lawan)

    if action == "get_produk_by_kategori":
        kode_kategori = params.get("kode_kategori", "").strip()
        return db.get_produk_by_kategori(kode_kategori)

    if action == "get_produk_by_nama":
        nama = params.get("nama_produk", "").strip()
        return db.get_produk_by_nama(nama)

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