import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from google.cloud.sql.connector import Connector

load_dotenv()

INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "maungbot")
DATABASE_URL = os.getenv("DATABASE_URL")
MAX_HASIL_PENCARIAN_PRODUK = 5

if INSTANCE_CONNECTION_NAME and DB_PASSWORD:
    # Production: pakai Cloud SQL Python Connecto

    connector = Connector()

    def getconn():
        return connector.connect(
            INSTANCE_CONNECTION_NAME,
            "pg8000",
            user=DB_USER,
            password=DB_PASSWORD,
            db=DB_NAME,
        )

    engine = create_engine("postgresql+pg8000://", creator=getconn)
    print("Connected to Cloud SQL via Python Connector")

elif DATABASE_URL:
    engine = create_engine(DATABASE_URL)
    print("Connected via DATABASE_URL")

else:
    # Fallback lokal: SQLite
    engine = create_engine(
        "sqlite:///./chatbot.db",
        connect_args={"check_same_thread": False}
    )
    print("⚠ Menggunakan SQLite (development)")

def _get_varian_produk(conn, id_produk: int):
    """Ambil breakdown varian ukuran + stok untuk satu produk."""
    rows = conn.execute(
        text("""
            SELECT u.size, ku.nama_kategori_ukuran, pu.stok
            FROM produk_ukuran pu
            JOIN ukuran u ON u.id_ukuran = pu.id_ukuran
            JOIN kategori_ukuran ku ON ku.id_kategori_ukuran = u.id_kategori_ukuran
            WHERE pu.id_produk = :id_produk
            ORDER BY u.size
        """),
        {"id_produk": id_produk}
    ).mappings().all()
    return [dict(r) for r in rows]


def get_produk_by_kategori(kode_kategori: str):
    """Ambil semua produk dalam satu kategori beserta varian ukurannya."""
    with engine.connect() as conn:
        produk_rows = conn.execute(
            text("""
                SELECT DISTINCT p.id_produk, p.kode_produk, p.nama_produk, p.harga
                FROM produk p
                JOIN kategori_produk_produk kpp ON kpp.id_produk = p.id_produk
                JOIN kategori_produk kp ON kp.id_kategori_produk = kpp.id_kategori_produk
                WHERE kp.kode_kategori_produk = :kode_kategori
                  AND p.status = TRUE
                ORDER BY p.nama_produk
            """),
            {"kode_kategori": kode_kategori}
        ).mappings().all()

        if not produk_rows:
            return None

        result = []
        for p in produk_rows:
            result.append({
                "kode_produk": p["kode_produk"],
                "nama_produk": p["nama_produk"],
                "harga": p["harga"],
                "varian": _get_varian_produk(conn, p["id_produk"])
            })

    return result


def get_produk_by_nama(query: str):
    """Cari produk berdasarkan nama menggunakan pencocokan token (semua kata harus ada)."""
    tokens = [t.strip() for t in query.strip().split() if t.strip()]
    if not tokens:
        return {"status": "empty"}

    patterns = [f"%{t}%" for t in tokens]

    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT id_produk, kode_produk, nama_produk, harga
                FROM produk
                WHERE nama_produk ILIKE ALL(:patterns)
                  AND status = TRUE
                ORDER BY nama_produk
                LIMIT :limit
            """),
            {"patterns": patterns, "limit": MAX_HASIL_PENCARIAN_PRODUK + 1}
        ).mappings().all()

        if not rows:
            return {"status": "not_found"}

        if len(rows) > MAX_HASIL_PENCARIAN_PRODUK:
            return {"status": "too_many"}

        if len(rows) == 1:
            produk = rows[0]
            return {
                "status": "single",
                "produk": {
                    "kode_produk": produk["kode_produk"],
                    "nama_produk": produk["nama_produk"],
                    "harga": produk["harga"],
                    "varian": _get_varian_produk(conn, produk["id_produk"])
                }
            }

        return {
            "status": "multiple",
            "produk": [
                {
                    "kode_produk": r["kode_produk"],
                    "nama_produk": r["nama_produk"],
                    "harga": r["harga"]
                }
                for r in rows
            ]
        }
    
def get_jadwal_pertandingan(kompetisi: str = None, status: str = None):
    """Ambil semua jadwal, bisa difilter berdasarkan kompetisi dan/atau status"""

    query = """
        SELECT id_jadwal, lawan, tanggal_jam, lokasi, kompetisi, status_pertandingan
        FROM jadwal_pertandingan
    """

    conditions = []
    params = {}

    if kompetisi:
        conditions.append(
            "LOWER(CAST(kompetisi AS text)) LIKE LOWER(:kompetisi)"
        )
        params["kompetisi"] = f"%{kompetisi}%"

    if status:
        conditions.append(
            "LOWER(CAST(status_pertandingan AS text)) = LOWER(:status)"
        )
        params["status"] = status

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY tanggal_jam ASC"

    with engine.connect() as conn:
        rows = conn.execute(
            text(query),
            params
        ).mappings().all()

    return [
        {
            "id_jadwal": row["id_jadwal"],
            "lawan": row["lawan"],
            "tanggal_jam": row["tanggal_jam"].strftime("%d %B %Y, %H:%M WIB"),
            "lokasi": row["lokasi"],
            "kompetisi": row["kompetisi"],
            "status_pertandingan": row["status_pertandingan"]
        }
        for row in rows
    ]

def get_jadwal_terdekat():
    """Ambil 1 pertandingan terdekat yang akan datang"""
    with engine.connect() as conn:
        row = conn.execute(
            text("""
                SELECT id_jadwal, lawan, tanggal_jam, lokasi, kompetisi, status_pertandingan
                FROM jadwal_pertandingan
                WHERE status_pertandingan = 'Akan Datang'
                ORDER BY tanggal_jam ASC
                LIMIT 1
            """)
        ).mappings().fetchone()

    if not row:
        return None

    return {
        "id_jadwal": row["id_jadwal"],
        "lawan": row["lawan"],
        "tanggal_jam": row["tanggal_jam"].strftime("%d %B %Y, %H:%M WIB"),
        "lokasi": row["lokasi"],
        "kompetisi": row["kompetisi"],
        "status_pertandingan": row["status_pertandingan"]
    }

def get_jadwal_by_lawan(nama_lawan: str):
    """Cari jadwal pertandingan berdasarkan nama lawan (partial match)"""
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT id_jadwal, lawan, tanggal_jam, lokasi, kompetisi, status_pertandingan
                FROM jadwal_pertandingan
                WHERE LOWER(lawan) LIKE LOWER(:nama_lawan)
                ORDER BY tanggal_jam ASC
            """),
            {"nama_lawan": f"%{nama_lawan}%"}
        ).mappings().all()

    if not rows:
        return None

    return [
        {
            "id_jadwal": row["id_jadwal"],
            "lawan": row["lawan"],
            "tanggal_jam": row["tanggal_jam"].strftime("%d %B %Y, %H:%M WIB"),
            "lokasi": row["lokasi"],
            "kompetisi": row["kompetisi"],
            "status_pertandingan": row["status_pertandingan"]
        }
        for row in rows
    ]

def get_pemain_by_nama(nama: str):
    """Cari pemain berdasarkan nama (partial match)"""
    with engine.connect() as conn:
        row = conn.execute(
            text("""
                SELECT id_pemain, nama_pemain, nomor_punggung, posisi,
                       kewarganegaraan, tanggal_lahir, status
                FROM pemain
                WHERE LOWER(nama_pemain) LIKE LOWER(:nama)
                LIMIT 1
            """),
            {"nama": f"%{nama}%"}
        ).mappings().fetchone()

    if not row:
        return None

    return {
        "id_pemain": row["id_pemain"],
        "nama_pemain": row["nama_pemain"],
        "nomor_punggung": row["nomor_punggung"],
        "posisi": row["posisi"],
        "kewarganegaraan": row["kewarganegaraan"],
        "tanggal_lahir": row["tanggal_lahir"].strftime("%d %B %Y") if row["tanggal_lahir"] else None,
        "status": row["status"]
    }

def get_pemain_by_posisi(posisi: str):
    """Ambil semua pemain berdasarkan posisi"""
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT id_pemain, nama_pemain, nomor_punggung, posisi,
                       kewarganegaraan, tanggal_lahir, status
                FROM pemain
                WHERE LOWER(posisi) = LOWER(:posisi)
                AND status = 'Aktif'
                ORDER BY nomor_punggung ASC
            """),
            {"posisi": posisi}
        ).mappings().all()

    return [
        {
            "id_pemain": row["id_pemain"],
            "nama_pemain": row["nama_pemain"],
            "nomor_punggung": row["nomor_punggung"],
            "posisi": row["posisi"],
            "kewarganegaraan": row["kewarganegaraan"],
            "tanggal_lahir": row["tanggal_lahir"].strftime("%d %B %Y") if row["tanggal_lahir"] else None,
            "status": row["status"]
        }
        for row in rows
    ]

def get_pemain_by_status(status: str):
    """Ambil semua pemain berdasarkan status"""
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT id_pemain, nama_pemain, nomor_punggung, posisi,
                       kewarganegaraan, status
                FROM pemain
                WHERE LOWER(status) = LOWER(:status)
                ORDER BY nomor_punggung ASC
            """),
            {"status": status}
        ).mappings().all()

    return [
        {
            "id_pemain": row["id_pemain"],
            "nama_pemain": row["nama_pemain"],
            "nomor_punggung": row["nomor_punggung"],
            "posisi": row["posisi"],
            "kewarganegaraan": row["kewarganegaraan"],
            "status": row["status"]
        }
        for row in rows
    ]

def get_stok_tiket(id_jadwal: int):
    """Ambil stok tiket per tribun untuk pertandingan tertentu"""
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT t.nama_tribun, t.stok, t.harga_tiket, j.lawan, j.tanggal_jam, j.status_pertandingan
                FROM ticket t
                JOIN jadwal_pertandingan j ON t.id_jadwal = j.id_jadwal
                WHERE t.id_jadwal = :id_jadwal
                ORDER BY t.nama_tribun
            """),
            {"id_jadwal": id_jadwal}
        ).mappings().all()

    if not rows:
        return None

    first = rows[0]
    return {
        "id_jadwal": id_jadwal,
        "lawan": first["lawan"],
        "tanggal_jam": first["tanggal_jam"].strftime("%d %B %Y, %H:%M WIB"),
        "status_pertandingan": first["status_pertandingan"],
        "tribun": [
            {
                "nama_tribun": r["nama_tribun"], 
                "stok": r["stok"], 
                "harga_tiket": r.get("harga_tiket") or 0
            }
            for r in rows
        ],
        "total_stok": sum(r["stok"] for r in rows)
    }

def get_stok_tiket_terdekat():
    """Ambil stok tiket untuk pertandingan terdekat yang akan datang"""
    with engine.connect() as conn:
        row = conn.execute(
            text("""
                SELECT id_jadwal FROM jadwal_pertandingan
                WHERE status_pertandingan = 'Akan Datang'
                ORDER BY tanggal_jam ASC
                LIMIT 1
            """)
        ).mappings().fetchone()

    if not row:
        return None

    return get_stok_tiket(row["id_jadwal"])

def get_stok_tiket_by_lawan(nama_lawan: str):
    """Ambil stok tiket berdasarkan nama lawan (partial match), prioritas yang akan datang"""
    with engine.connect() as conn:
        row = conn.execute(
            text("""
                SELECT id_jadwal FROM jadwal_pertandingan
                WHERE LOWER(lawan) LIKE LOWER(:nama_lawan)
                ORDER BY
                    CASE WHEN status_pertandingan = 'Akan Datang' THEN 0 ELSE 1 END,
                    tanggal_jam ASC
                LIMIT 1
            """),
            {"nama_lawan": f"%{nama_lawan}%"}
        ).mappings().fetchone()

    if not row:
        return None

    return get_stok_tiket(row["id_jadwal"])
