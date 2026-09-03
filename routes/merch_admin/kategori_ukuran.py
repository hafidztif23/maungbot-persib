from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import text
from core.db import engine
from core.dependencies import get_current_admin

router = APIRouter(prefix="/admin/merch", tags=["admin-merchandise"], dependencies=[Depends(get_current_admin)])

VALID_KATEGORI_UKURAN = {"Atasan", "Celana", "Sendal", "Tanpa Ukuran"}

class KategoriUkuranCreate(BaseModel):
    nama_kategori_ukuran: str

class KategoriUkuranUpdate(BaseModel):
    nama_kategori_ukuran: str

@router.get("/kategori-ukuran")
def list_kategori_ukuran():
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM kategori_ukuran ORDER BY nama_kategori_ukuran")).mappings().all()
    return {"total": len(rows), "data": [dict(r) for r in rows]}


@router.post("/kategori-ukuran", status_code=201)
def create_kategori_ukuran(data: KategoriUkuranCreate):
    with engine.connect() as conn:
        existing = conn.execute(
            text("SELECT 1 FROM kategori_ukuran WHERE nama_kategori_ukuran = :n"),
            {"n": data.nama_kategori_ukuran}
        ).fetchone()
        if existing:
            return {"error": f"Kategori ukuran '{data.nama_kategori_ukuran}' sudah ada"}

        result = conn.execute(
            text("""
                INSERT INTO kategori_ukuran (nama_kategori_ukuran)
                VALUES (:n)
                RETURNING id_kategori_ukuran
            """),
            {"n": data.nama_kategori_ukuran}
        )
        conn.commit()
        new_id = result.fetchone()[0]

    return {"message": "Kategori ukuran berhasil ditambahkan", "id_kategori_ukuran": new_id}


@router.put("/kategori-ukuran/{id_kategori_ukuran}")
def update_kategori_ukuran(id_kategori_ukuran: int, data: KategoriUkuranUpdate):
    with engine.connect() as conn:
        duplicate = conn.execute(
            text("SELECT 1 FROM kategori_ukuran WHERE nama_kategori_ukuran = :n AND id_kategori_ukuran != :id"),
            {"n": data.nama_kategori_ukuran, "id": id_kategori_ukuran}
        ).fetchone()
        if duplicate:
            return {"error": f"Kategori ukuran '{data.nama_kategori_ukuran}' sudah ada"}

        result = conn.execute(
            text("UPDATE kategori_ukuran SET nama_kategori_ukuran = :n WHERE id_kategori_ukuran = :id"),
            {"n": data.nama_kategori_ukuran, "id": id_kategori_ukuran}
        )
        conn.commit()
        if result.rowcount == 0:
            return {"error": f"Kategori ukuran id {id_kategori_ukuran} tidak ditemukan"}

    return {"message": f"Kategori ukuran id {id_kategori_ukuran} berhasil diupdate"}


@router.delete("/kategori-ukuran/{id_kategori_ukuran}")
def delete_kategori_ukuran(id_kategori_ukuran: int):
    with engine.connect() as conn:
        result = conn.execute(
            text("DELETE FROM kategori_ukuran WHERE id_kategori_ukuran = :id"),
            {"id": id_kategori_ukuran}
        )
        conn.commit()
        if result.rowcount == 0:
            return {"error": f"Kategori ukuran id {id_kategori_ukuran} tidak ditemukan"}

    return {"message": f"Kategori ukuran id {id_kategori_ukuran} berhasil dihapus"}