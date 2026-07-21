import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Global variable — dibaca sekali saat startup
_nodes: dict = {}

REQUIRED_FIELDS = {
    "superstate": ["message", "options"],
    "substate": ["message", "options"],
    "terminal_state": ["action", "back_to"],
    "transitional_state": ["message", "action", "param_key", "back_to"],
}


def load_tree(path: str = "data.json") -> dict:
    global _nodes

    file_path = Path(path)
    if not file_path.exists():
        raise RuntimeError(f"data.json tidak ditemukan di path: {file_path.resolve()}")

    with open(file_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Toleransi format array maupun object langsung
    if isinstance(raw, list):
        raw = raw[0]

    if "nodes" not in raw:
        raise RuntimeError("data.json tidak memiliki key 'nodes'")

    nodes = raw["nodes"]

    if not nodes:
        raise RuntimeError("'nodes' kosong di data.json")

    _validate(nodes)

    _nodes = nodes
    logger.info(f"FSM tree berhasil dimuat: {len(nodes)} node")
    return _nodes


def get_nodes() -> dict:
    if not _nodes:
        raise RuntimeError("FSM tree belum dimuat. Panggil load_tree() saat startup.")
    return _nodes


def _validate(nodes: dict) -> None:
    errors = []

    # 1. Root harus ada
    if "root" not in nodes:
        errors.append("Node 'root' tidak ditemukan di nodes")

    for node_id, node in nodes.items():

        node_type = node.get("type")

        # 2. Validasi field wajib per tipe
        if node_type not in REQUIRED_FIELDS:
            errors.append(
                f"Node '{node_id}' memiliki type tidak dikenal: '{node_type}'"
            )
            continue

        for field in REQUIRED_FIELDS[node_type]:
            if field not in node:
                errors.append(
                    f"Node '{node_id}' (type: {node_type}) tidak memiliki field wajib: '{field}'"
                )

        # 3. Referential integrity untuk superstate dan substate
        if node_type in ("superstate", "substate"):
            options = node.get("options", {})
            for choice, target in options.items():
                if target not in nodes:
                    errors.append(
                        f"Node '{node_id}' opsi '{choice}' merujuk ke node "
                        f"'{target}' yang tidak terdefinisi"
                    )

    if errors:
        error_msg = "Validasi data.json gagal:\n" + "\n".join(f"  - {e}" for e in errors)
        raise RuntimeError(error_msg)