from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import text
from core.db import engine
from core.dependencies import get_current_admin

router = APIRouter(prefix="/admin/merch", tags=["admin-merchandise"], dependencies=[Depends(get_current_admin)])

class ProdukCreate(BaseModel):
    kode_produk: str
    nama_produk: str
    harga: int
    status: Optional[bool] = True
    id_kategori_produk: list[int] = []

class ProdukUpdate(BaseModel):
    kode_produk: Optional[str] = None
    nama_produk: Optional[str] = None
    harga: Optional[int] = None
    status: Optional[bool] = None

@router.get("/produk")
def list_produk(
    kode_kategori: Optional[str] = Query(None),
    nama: Optional[str] = Query(None),
    status: Optional[bool] = Query(None)
):
    query = """
        SELECT DISTINCT p.*
        FROM produk p
        LEFT JOIN kategori_produk_produk kpp ON kpp.id_produk = p.id_produk
        LEFT JOIN kategori_produk kp ON kp.id_kategori_produk = kpp.id_kategori_produk
        WHERE 1=1
    """
    params = {}
    if kode_kategori:
        query += " AND kp.kode_kategori_produk = :kode_kategori"
        params["kode_kategori"] = kode_kategori
    if nama:
        query += " AND p.nama_produk ILIKE :nama"
        params["nama"] = f"%{nama}%"
    if status is not None:
        query += " AND p.status = :status"
        params["status"] = status
    query += " ORDER BY p.nama_produk"

    with engine.connect() as conn:
        rows = conn.execute(text(query), params).mappings().all()
    return {"total": len(rows), "data": [dict(r) for r in rows]}


@router.get("/produk/{id_produk}")
def get_produk(id_produk: int):
    with engine.connect() as conn:
        produk = conn.execute(
            text("SELECT * FROM produk WHERE id_produk = :id"),
            {"id": id_produk}
        ).mappings().fetchone()
        if not produk:
            return {"error": f"Produk id {id_produk} tidak ditemukan"}

        kategori = conn.execute(
            text("""
                SELECT kp.id_kategori_produk, kp.kode_kategori_produk, kp.nama_kategori_produk
                FROM kategori_produk_produk kpp
                JOIN kategori_produk kp ON kp.id_kategori_produk = kpp.id_kategori_produk
                WHERE kpp.id_produk = :id
            """),
            {"id": id_produk}
        ).mappings().all()

        varian = conn.execute(
            text("""
                SELECT pu.id_ukuran, u.kode_ukuran, u.size, pu.stok
                FROM produk_ukuran pu
                JOIN ukuran u ON u.id_ukuran = pu.id_ukuran
                WHERE pu.id_produk = :id
                ORDER BY u.size
            """),
            {"id": id_produk}
        ).mappings().all()

    return {
        **dict(produk),
        "kategori": [dict(k) for k in kategori],
        "varian": [dict(v) for v in varian]
    }


@router.post("/produk", status_code=201)
def create_produk(data: ProdukCreate):
    if data.harga < 0:
        return {"error": "Harga tidak boleh negatif"}

    with engine.connect() as conn:
        existing = conn.execute(
            text("SELECT 1 FROM produk WHERE kode_produk = :k"),
            {"k": data.kode_produk}
        ).fetchone()
        if existing:
            return {"error": f"Kode produk '{data.kode_produk}' sudah digunakan"}

        if data.id_kategori_produk:
            found = conn.execute(
                text("SELECT id_kategori_produk FROM kategori_produk WHERE id_kategori_produk = ANY(:ids)"),
                {"ids": data.id_kategori_produk}
            ).fetchall()
            if len(found) != len(set(data.id_kategori_produk)):
                return {"error": "Salah satu id_kategori_produk tidak ditemukan"}

        result = conn.execute(
            text("""
                INSERT INTO produk (kode_produk, nama_produk, harga, status)
                VALUES (:kode, :nama, :harga, :status)
                RETURNING id_produk
            """),
            {"kode": data.kode_produk, "nama": data.nama_produk, "harga": data.harga, "status": data.status}
        )
        new_id = result.fetchone()[0]

        for id_kategori in data.id_kategori_produk:
            conn.execute(
                text("""
                    INSERT INTO kategori_produk_produk (id_kategori_produk, id_produk)
                    VALUES (:id_kategori, :id_produk)
                """),
                {"id_kategori": id_kategori, "id_produk": new_id}
            )
        conn.commit()

    return {"message": "Produk berhasil ditambahkan", "id_produk": new_id}


@router.put("/produk/{id_produk}")
def update_produk(id_produk: int, data: ProdukUpdate):
    fields = {}
    if data.kode_produk is not None:
        fields["kode_produk"] = data.kode_produk
    if data.nama_produk is not None:
        fields["nama_produk"] = data.nama_produk
    if data.harga is not None:
        if data.harga < 0:
            return {"error": "Harga tidak boleh negatif"}
        fields["harga"] = data.harga
    if data.status is not None:
        fields["status"] = data.status

    if not fields:
        return {"error": "Tidak ada field yang diupdate"}

    with engine.connect() as conn:
        if "kode_produk" in fields:
            duplicate = conn.execute(
                text("SELECT 1 FROM produk WHERE kode_produk = :k AND id_produk != :id"),
                {"k": fields["kode_produk"], "id": id_produk}
            ).fetchone()
            if duplicate:
                return {"error": f"Kode produk '{fields['kode_produk']}' sudah digunakan"}

        set_clause = ", ".join(f"{k} = :{k}" for k in fields)
        fields["id"] = id_produk
        result = conn.execute(
            text(f"UPDATE produk SET {set_clause} WHERE id_produk = :id"),
            fields
        )
        conn.commit()
        if result.rowcount == 0:
            return {"error": f"Produk id {id_produk} tidak ditemukan"}

    return {"message": f"Produk id {id_produk} berhasil diupdate"}


@router.delete("/produk/{id_produk}")
def delete_produk(id_produk: int):
    with engine.connect() as conn:
        result = conn.execute(text("DELETE FROM produk WHERE id_produk = :id"), {"id": id_produk})
        conn.commit()
        if result.rowcount == 0:
            return {"error": f"Produk id {id_produk} tidak ditemukan"}

    return {"message": f"Produk id {id_produk} berhasil dihapus"}


@router.post("/produk/{id_produk}/kategori/{id_kategori_produk}", status_code=201)
def assign_kategori_produk(id_produk: int, id_kategori_produk: int):
    with engine.connect() as conn:
        produk = conn.execute(text("SELECT 1 FROM produk WHERE id_produk = :id"), {"id": id_produk}).fetchone()
        if not produk:
            return {"error": f"Produk id {id_produk} tidak ditemukan"}

        kategori = conn.execute(
            text("SELECT 1 FROM kategori_produk WHERE id_kategori_produk = :id"),
            {"id": id_kategori_produk}
        ).fetchone()
        if not kategori:
            return {"error": f"Kategori produk id {id_kategori_produk} tidak ditemukan"}

        existing = conn.execute(
            text("SELECT 1 FROM kategori_produk_produk WHERE id_produk = :p AND id_kategori_produk = :k"),
            {"p": id_produk, "k": id_kategori_produk}
        ).fetchone()
        if existing:
            return {"error": "Produk sudah tergabung dalam kategori ini"}

        conn.execute(
            text("""
                INSERT INTO kategori_produk_produk (id_produk, id_kategori_produk)
                VALUES (:p, :k)
            """),
            {"p": id_produk, "k": id_kategori_produk}
        )
        conn.commit()

    return {"message": "Kategori berhasil ditambahkan ke produk"}


@router.delete("/produk/{id_produk}/kategori/{id_kategori_produk}")
def unassign_kategori_produk(id_produk: int, id_kategori_produk: int):
    with engine.connect() as conn:
        result = conn.execute(
            text("DELETE FROM kategori_produk_produk WHERE id_produk = :p AND id_kategori_produk = :k"),
            {"p": id_produk, "k": id_kategori_produk}
        )
        conn.commit()
        if result.rowcount == 0:
            return {"error": "Relasi produk-kategori tidak ditemukan"}

    return {"message": "Kategori berhasil dihapus dari produk"}