from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import text
from core.db import engine
from core.dependencies import get_current_admin

router = APIRouter(prefix="/admin/merch", tags=["admin-merchandise"], dependencies=[Depends(get_current_admin)])

class KategoriProdukCreate(BaseModel):
    kode_kategori_produk: str
    nama_kategori_produk: str

class KategoriProdukUpdate(BaseModel):
    kode_kategori_produk: Optional[str] = None
    nama_kategori_produk: Optional[str] = None

@router.get("/kategori-produk")
def list_kategori_produk():
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM kategori_produk ORDER BY nama_kategori_produk")).mappings().all()
    return {"total": len(rows), "data": [dict(r) for r in rows]}


@router.post("/kategori-produk", status_code=201)
def create_kategori_produk(data: KategoriProdukCreate):
    with engine.connect() as conn:
        existing = conn.execute(
            text("SELECT 1 FROM kategori_produk WHERE kode_kategori_produk = :k"),
            {"k": data.kode_kategori_produk}
        ).fetchone()
        if existing:
            return {"error": f"Kode kategori '{data.kode_kategori_produk}' sudah digunakan"}

        result = conn.execute(
            text("""
                INSERT INTO kategori_produk (kode_kategori_produk, nama_kategori_produk)
                VALUES (:kode, :nama)
                RETURNING id_kategori_produk
            """),
            {"kode": data.kode_kategori_produk, "nama": data.nama_kategori_produk}
        )
        conn.commit()
        new_id = result.fetchone()[0]

    return {"message": "Kategori produk berhasil ditambahkan", "id_kategori_produk": new_id}


@router.put("/kategori-produk/{id_kategori_produk}")
def update_kategori_produk(id_kategori_produk: int, data: KategoriProdukUpdate):
    fields = {}
    if data.kode_kategori_produk is not None:
        fields["kode_kategori_produk"] = data.kode_kategori_produk
    if data.nama_kategori_produk is not None:
        fields["nama_kategori_produk"] = data.nama_kategori_produk

    if not fields:
        return {"error": "Tidak ada field yang diupdate"}

    with engine.connect() as conn:
        if "kode_kategori_produk" in fields:
            duplicate = conn.execute(
                text("SELECT 1 FROM kategori_produk WHERE kode_kategori_produk = :k AND id_kategori_produk != :id"),
                {"k": fields["kode_kategori_produk"], "id": id_kategori_produk}
            ).fetchone()
            if duplicate:
                return {"error": f"Kode kategori '{fields['kode_kategori_produk']}' sudah digunakan"}

        set_clause = ", ".join(f"{k} = :{k}" for k in fields)
        fields["id"] = id_kategori_produk
        result = conn.execute(
            text(f"UPDATE kategori_produk SET {set_clause} WHERE id_kategori_produk = :id"),
            fields
        )
        conn.commit()
        if result.rowcount == 0:
            return {"error": f"Kategori produk id {id_kategori_produk} tidak ditemukan"}

    return {"message": f"Kategori produk id {id_kategori_produk} berhasil diupdate"}


@router.delete("/kategori-produk/{id_kategori_produk}")
def delete_kategori_produk(id_kategori_produk: int):
    with engine.connect() as conn:
        result = conn.execute(
            text("DELETE FROM kategori_produk WHERE id_kategori_produk = :id"),
            {"id": id_kategori_produk}
        )
        conn.commit()
        if result.rowcount == 0:
            return {"error": f"Kategori produk id {id_kategori_produk} tidak ditemukan"}

    return {"message": f"Kategori produk id {id_kategori_produk} berhasil dihapus"}