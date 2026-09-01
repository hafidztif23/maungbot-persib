from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional
from sqlalchemy import text
from core.db import engine
from core.dependencies import get_current_admin
from core.loader import load_tree, get_nodes

router = APIRouter(prefix="/admin/fsm", tags=["FSM Admin"])

VALID_TYPES = {"menu_state", "terminal_state", "transitional_state"}

# ─────────────────────────────────────────
# SCHEMA
# ─────────────────────────────────────────

class NodeCreate(BaseModel):
    id: str
    type: str
    message: Optional[str] = None
    options: Optional[dict] = None
    action: Optional[str] = None
    params: Optional[dict] = None
    content: Optional[str] = None
    param_key: Optional[str] = None
    back_to: Optional[str] = None

    @field_validator("type")
    @classmethod
    def type_valid(cls, v: str) -> str:
        if v not in VALID_TYPES:
            raise ValueError(f"type harus salah satu dari: {VALID_TYPES}")
        return v

class NodeUpdate(BaseModel):
    type: Optional[str] = None
    message: Optional[str] = None
    options: Optional[dict] = None
    action: Optional[str] = None
    params: Optional[dict] = None
    content: Optional[str] = None
    param_key: Optional[str] = None
    back_to: Optional[str] = None

    @field_validator("type")
    @classmethod
    def type_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_TYPES:
            raise ValueError(f"type harus salah satu dari: {VALID_TYPES}")
        return v

# ─────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────

def _row_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "type": row["type"],
        "message": row["message"],
        "options": row["options"],
        "action": row["action"],
        "params": row["params"],
        "content": row["content"],
        "param_key": row["param_key"],
        "back_to": row["back_to"],
    }

# ─────────────────────────────────────────
# GET — list semua node
# ─────────────────────────────────────────

@router.get("/nodes")
def list_nodes(admin: dict = Depends(get_current_admin)):
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM fsm_node ORDER BY id")).mappings().all()
    return {"total": len(rows), "nodes": [_row_to_dict(r) for r in rows]}

# ─────────────────────────────────────────
# GET — satu node
# ─────────────────────────────────────────

@router.get("/nodes/{node_id}")
def get_node(node_id: str, admin: dict = Depends(get_current_admin)):
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM fsm_node WHERE id = :id"),
            {"id": node_id}
        ).mappings().fetchone()

    if not row:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' tidak ditemukan")

    return _row_to_dict(row)

# ─────────────────────────────────────────
# POST — buat node baru
# ─────────────────────────────────────────

@router.post("/nodes", status_code=201)
def create_node(data: NodeCreate, admin: dict = Depends(get_current_admin)):
    with engine.connect() as conn:
        existing = conn.execute(
            text("SELECT id FROM fsm_node WHERE id = :id"),
            {"id": data.id}
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail=f"Node '{data.id}' sudah ada")

        conn.execute(
            text("""
                INSERT INTO fsm_node
                    (id, type, message, options, action, params, content, param_key, back_to)
                VALUES
                    (:id, :type, :message, CAST(:options AS jsonb), :action,
                     CAST(:params AS jsonb), :content, :param_key, :back_to)
            """),
            {
                "id": data.id,
                "type": data.type,
                "message": data.message,
                "options": _to_json(data.options),
                "action": data.action,
                "params": _to_json(data.params),
                "content": data.content,
                "param_key": data.param_key,
                "back_to": data.back_to,
            }
        )
        conn.commit()

    return {"message": f"Node '{data.id}' berhasil dibuat", "id": data.id}

# ─────────────────────────────────────────
# PUT — update node
# ─────────────────────────────────────────

@router.put("/nodes/{node_id}")
def update_node(node_id: str, data: NodeUpdate, admin: dict = Depends(get_current_admin)):
    fields = {}
    if data.type is not None: fields["type"] = data.type
    if data.message is not None: fields["message"] = data.message
    if data.options is not None: fields["options"] = _to_json(data.options)
    if data.action is not None: fields["action"] = data.action
    if data.params is not None: fields["params"] = _to_json(data.params)
    if data.content is not None: fields["content"] = data.content
    if data.param_key is not None: fields["param_key"] = data.param_key
    if data.back_to is not None: fields["back_to"] = data.back_to

    if not fields:
        raise HTTPException(status_code=400, detail="Tidak ada field yang diupdate")

    with engine.connect() as conn:
        existing = conn.execute(
            text("SELECT id FROM fsm_node WHERE id = :id"),
            {"id": node_id}
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail=f"Node '{node_id}' tidak ditemukan")

        set_clause_parts = []
        for k in fields:
            if k in ("options", "params"):
                set_clause_parts.append(f"{k} = CAST(:{k} AS jsonb)")
            else:
                set_clause_parts.append(f"{k} = :{k}")
        set_clause = ", ".join(set_clause_parts) + ", updated_at = NOW()"
        fields["id"] = node_id

        conn.execute(text(f"UPDATE fsm_node SET {set_clause} WHERE id = :id"), fields)
        conn.commit()

    return {"message": f"Node '{node_id}' berhasil diupdate"}

# ─────────────────────────────────────────
# DELETE — hapus node
# ─────────────────────────────────────────

@router.delete("/nodes/{node_id}")
def delete_node(node_id: str, admin: dict = Depends(get_current_admin)):
    with engine.connect() as conn:
        result = conn.execute(text("DELETE FROM fsm_node WHERE id = :id"), {"id": node_id})
        conn.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Node '{node_id}' tidak ditemukan")

    return {"message": f"Node '{node_id}' berhasil dihapus"}

# ─────────────────────────────────────────
# POST — reload FSM tree dari DB ke memory (+ validasi)
# ─────────────────────────────────────────

@router.post("/reload")
def reload_fsm(admin: dict = Depends(get_current_admin)):
    try:
        load_tree()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": "FSM tree berhasil dimuat ulang", "total_nodes": len(get_nodes())}


def _to_json(value):
    import json
    return json.dumps(value) if value is not None else None