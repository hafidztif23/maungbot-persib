from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import text
from core.db import engine
from core.dependencies import get_current_admin

router = APIRouter(prefix="/admin/merch", tags=["admin-merchandise"], dependencies=[Depends(get_current_admin)])

class UkuranCreate(BaseModel):
    id_kategori_ukuran: int
    kode_ukuran: str
    size: str
    # detail opsional, wajib diisi sesuai kategori ukurannya
    lebar_bahu: Optional[float] = None
    panjang_atasan: Optional[float] = None
    lingkar_dada: Optional[float] = None
    panjang_lengan_baju: Optional[float] = None
    pinggang: Optional[float] = None
    tinggi_depan: Optional[float] = None
    tinggi_belakang: Optional[float] = None
    paha: Optional[float] = None
    lutut: Optional[float] = None
    bukaan_kaki: Optional[float] = None
    panjang_inseam: Optional[float] = None
    panjang_outseam: Optional[float] = None
    panjang_sendal: Optional[float] = None

class UkuranUpdate(BaseModel):
    kode_ukuran: Optional[str] = None
    size: Optional[str] = None
    lebar_bahu: Optional[float] = None
    panjang_atasan: Optional[float] = None
    lingkar_dada: Optional[float] = None
    panjang_lengan_baju: Optional[float] = None
    pinggang: Optional[float] = None
    tinggi_depan: Optional[float] = None
    tinggi_belakang: Optional[float] = None
    paha: Optional[float] = None
    lutut: Optional[float] = None
    bukaan_kaki: Optional[float] = None
    panjang_inseam: Optional[float] = None
    panjang_outseam: Optional[float] = None
    panjang_sendal: Optional[float] = None

_DETAIL_FIELDS = {
    "Atasan": ["lebar_bahu", "panjang_atasan", "lingkar_dada", "panjang_lengan_baju"],
    "Celana": ["pinggang", "tinggi_depan", "tinggi_belakang", "paha", "lutut",
               "bukaan_kaki", "panjang_inseam", "panjang_outseam"],
    "Sendal": ["panjang_sendal"],
    "Tanpa Ukuran": [],
}
_DETAIL_TABLE = {
    "Atasan": "ukuran_atasan",
    "Celana": "ukuran_celana",
    "Sendal": "ukuran_sendal",
}


def _get_nama_kategori_ukuran(conn, id_kategori_ukuran: int) -> str | None:
    row = conn.execute(
        text("SELECT nama_kategori_ukuran FROM kategori_ukuran WHERE id_kategori_ukuran = :id"),
        {"id": id_kategori_ukuran}
    ).fetchone()
    return row[0] if row else None


@router.get("/ukuran")
def list_ukuran(id_kategori_ukuran: Optional[int] = Query(None)):
    query = "SELECT * FROM ukuran WHERE 1=1"
    params = {}
    if id_kategori_ukuran:
        query += " AND id_kategori_ukuran = :id_kategori"
        params["id_kategori"] = id_kategori_ukuran
    query += " ORDER BY size"

    with engine.connect() as conn:
        rows = conn.execute(text(query), params).mappings().all()
    return {"total": len(rows), "data": [dict(r) for r in rows]}


@router.get("/ukuran/{id_ukuran}")
def get_ukuran(id_ukuran: int):
    with engine.connect() as conn:
        ukuran = conn.execute(text("SELECT * FROM ukuran WHERE id_ukuran = :id"), {"id": id_ukuran}).mappings().fetchone()
        if not ukuran:
            return {"error": f"Ukuran id {id_ukuran} tidak ditemukan"}

        nama_kategori = _get_nama_kategori_ukuran(conn, ukuran["id_kategori_ukuran"])
        detail = {}
        if nama_kategori in _DETAIL_TABLE:
            table = _DETAIL_TABLE[nama_kategori]
            row = conn.execute(text(f"SELECT * FROM {table} WHERE id_ukuran = :id"), {"id": id_ukuran}).mappings().fetchone()
            detail = dict(row) if row else {}

    return {**dict(ukuran), "nama_kategori_ukuran": nama_kategori, "detail": detail}


@router.post("/ukuran", status_code=201)
def create_ukuran(data: UkuranCreate):
    with engine.connect() as conn:
        nama_kategori = _get_nama_kategori_ukuran(conn, data.id_kategori_ukuran)
        if nama_kategori is None:
            return {"error": f"Kategori ukuran id {data.id_kategori_ukuran} tidak ditemukan"}

        existing = conn.execute(
            text("SELECT 1 FROM ukuran WHERE kode_ukuran = :k"),
            {"k": data.kode_ukuran}
        ).fetchone()
        if existing:
            return {"error": f"Kode ukuran '{data.kode_ukuran}' sudah digunakan"}

        # Validasi field detail wajib sesuai kategori
        required_fields = _DETAIL_FIELDS.get(nama_kategori, [])
        payload = data.model_dump()
        missing = [f for f in required_fields if payload.get(f) is None]
        if missing:
            return {"error": f"Field wajib untuk kategori '{nama_kategori}' belum diisi: {', '.join(missing)}"}

        result = conn.execute(
            text("""
                INSERT INTO ukuran (id_kategori_ukuran, kode_ukuran, size)
                VALUES (:id_kategori, :kode, :size)
                RETURNING id_ukuran
            """),
            {"id_kategori": data.id_kategori_ukuran, "kode": data.kode_ukuran, "size": data.size}
        )
        new_id = result.fetchone()[0]

        if nama_kategori in _DETAIL_TABLE and required_fields:
            table = _DETAIL_TABLE[nama_kategori]
            cols = ", ".join(required_fields)
            placeholders = ", ".join(f":{f}" for f in required_fields)
            detail_params = {f: payload[f] for f in required_fields}
            detail_params["id_ukuran"] = new_id
            conn.execute(
                text(f"INSERT INTO {table} (id_ukuran, {cols}) VALUES (:id_ukuran, {placeholders})"),
                detail_params
            )

        conn.commit()

    return {"message": "Ukuran berhasil ditambahkan", "id_ukuran": new_id}


@router.put("/ukuran/{id_ukuran}")
def update_ukuran(id_ukuran: int, data: UkuranUpdate):
    with engine.connect() as conn:
        ukuran = conn.execute(text("SELECT * FROM ukuran WHERE id_ukuran = :id"), {"id": id_ukuran}).mappings().fetchone()
        if not ukuran:
            return {"error": f"Ukuran id {id_ukuran} tidak ditemukan"}

        base_fields = {}
        if data.kode_ukuran is not None:
            duplicate = conn.execute(
                text("SELECT 1 FROM ukuran WHERE kode_ukuran = :k AND id_ukuran != :id"),
                {"k": data.kode_ukuran, "id": id_ukuran}
            ).fetchone()
            if duplicate:
                return {"error": f"Kode ukuran '{data.kode_ukuran}' sudah digunakan"}
            base_fields["kode_ukuran"] = data.kode_ukuran
        if data.size is not None:
            base_fields["size"] = data.size

        if base_fields:
            set_clause = ", ".join(f"{k} = :{k}" for k in base_fields)
            base_fields["id"] = id_ukuran
            conn.execute(text(f"UPDATE ukuran SET {set_clause} WHERE id_ukuran = :id"), base_fields)

        nama_kategori = _get_nama_kategori_ukuran(conn, ukuran["id_kategori_ukuran"])
        if nama_kategori in _DETAIL_TABLE:
            table = _DETAIL_TABLE[nama_kategori]
            allowed = _DETAIL_FIELDS[nama_kategori]
            payload = data.model_dump()
            detail_fields = {f: payload[f] for f in allowed if payload.get(f) is not None}
            if detail_fields:
                set_clause = ", ".join(f"{k} = :{k}" for k in detail_fields)
                detail_fields["id"] = id_ukuran
                conn.execute(text(f"UPDATE {table} SET {set_clause} WHERE id_ukuran = :id"), detail_fields)

        conn.commit()

    return {"message": f"Ukuran id {id_ukuran} berhasil diupdate"}


@router.delete("/ukuran/{id_ukuran}")
def delete_ukuran(id_ukuran: int):
    with engine.connect() as conn:
        result = conn.execute(text("DELETE FROM ukuran WHERE id_ukuran = :id"), {"id": id_ukuran})
        conn.commit()
        if result.rowcount == 0:
            return {"error": f"Ukuran id {id_ukuran} tidak ditemukan"}

    return {"message": f"Ukuran id {id_ukuran} berhasil dihapus"}