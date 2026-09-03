from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import text
from core.db import engine
from core.dependencies import get_current_admin

router = APIRouter(prefix="/admin/merch", tags=["admin-merchandise"], dependencies=[Depends(get_current_admin)])

class ProdukUkuranCreate(BaseModel):
    id_produk: int
    id_ukuran: int
    stok: int = 0

class ProdukUkuranUpdate(BaseModel):
    stok: int

@router.post("/produk-ukuran", status_code=201)
def assign_produk_ukuran(data: ProdukUkuranCreate):
    if data.stok < 0:
        return {"error": "Stok tidak boleh negatif"}

    with engine.connect() as conn:
        produk = conn.execute(text("SELECT 1 FROM produk WHERE id_produk = :id"), {"id": data.id_produk}).fetchone()
        if not produk:
            return {"error": f"Produk id {data.id_produk} tidak ditemukan"}

        ukuran = conn.execute(text("SELECT 1 FROM ukuran WHERE id_ukuran = :id"), {"id": data.id_ukuran}).fetchone()
        if not ukuran:
            return {"error": f"Ukuran id {data.id_ukuran} tidak ditemukan"}

        existing = conn.execute(
            text("SELECT 1 FROM produk_ukuran WHERE id_produk = :p AND id_ukuran = :u"),
            {"p": data.id_produk, "u": data.id_ukuran}
        ).fetchone()
        if existing:
            return {"error": "Varian ukuran ini sudah terdaftar untuk produk tersebut"}

        conn.execute(
            text("""
                INSERT INTO produk_ukuran (id_produk, id_ukuran, stok)
                VALUES (:p, :u, :stok)
            """),
            {"p": data.id_produk, "u": data.id_ukuran, "stok": data.stok}
        )
        conn.commit()

    return {"message": "Varian ukuran berhasil ditambahkan ke produk"}


@router.put("/produk-ukuran/{id_produk}/{id_ukuran}")
def update_stok_produk_ukuran(id_produk: int, id_ukuran: int, data: ProdukUkuranUpdate):
    if data.stok < 0:
        return {"error": "Stok tidak boleh negatif"}

    with engine.connect() as conn:
        result = conn.execute(
            text("""
                UPDATE produk_ukuran SET stok = :stok
                WHERE id_produk = :p AND id_ukuran = :u
            """),
            {"stok": data.stok, "p": id_produk, "u": id_ukuran}
        )
        conn.commit()
        if result.rowcount == 0:
            return {"error": "Varian produk-ukuran tidak ditemukan"}

    return {"message": "Stok berhasil diperbarui"}


@router.delete("/produk-ukuran/{id_produk}/{id_ukuran}")
def unassign_produk_ukuran(id_produk: int, id_ukuran: int):
    with engine.connect() as conn:
        result = conn.execute(
            text("DELETE FROM produk_ukuran WHERE id_produk = :p AND id_ukuran = :u"),
            {"p": id_produk, "u": id_ukuran}
        )
        conn.commit()
        if result.rowcount == 0:
            return {"error": "Varian produk-ukuran tidak ditemukan"}

    return {"message": "Varian ukuran berhasil dihapus dari produk"}