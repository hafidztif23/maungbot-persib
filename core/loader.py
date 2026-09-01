from sqlalchemy import text
from core.db import engine
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s"
)
logger = logging.getLogger(__name__)

_nodes: dict = {}

REQUIRED_FIELDS = {
    "menu_state": ["message", "options"],
    "terminal_state": ["action", "back_to"],
    "transitional_state": ["message", "action", "param_key", "back_to"],
}

def load_tree() -> dict:
    global _nodes

    with engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM fsm_node")).mappings().all()

    if not rows:
        raise RuntimeError("Tabel fsm_node kosong. Belum ada node yang terdaftar.")

    nodes = {}
    for row in rows:
        node = dict(row)
        node_id = node["id"]
        entry = {"id": node_id, "type": node["type"]}

        if node["message"] is not None:
            entry["message"] = node["message"]
        if node["options"] is not None:
            entry["options"] = node["options"]
        if node["action"] is not None:
            entry["action"] = node["action"]
        if node["params"] is not None:
            entry["params"] = node["params"]
        if node["content"] is not None:
            entry["content"] = node["content"]
        if node["param_key"] is not None:
            entry["param_key"] = node["param_key"]
        if node["back_to"] is not None:
            entry["back_to"] = node["back_to"]

        nodes[node_id] = entry

    _validate(nodes)   # fungsi validasi existing — TIDAK DIUBAH

    _nodes = nodes
    logger.info(f"Total {len(nodes)} node berhasil di-load dari database dan divalidasi.")
    return _nodes

def get_nodes() -> dict:
    if not _nodes:
        raise RuntimeError("FSM tree belum dimuat. Panggil load_tree() saat startup.")
    return _nodes

def _validate(nodes: dict) -> None:
    errors = []

    # Validasi bahwa node awal / utama itu ada
    if "user_menu_utama" not in nodes:
        errors.append("Node 'user_menu_utama' tidak ditemukan di nodes")

    for node_id, node in nodes.items():
        node_type = node.get("type")

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

        # Referential integrity untuk options (menu_state)
        if node_type == "menu_state":
            options = node.get("options", {})
            for choice, target in options.items():
                if target not in nodes:
                    errors.append(
                        f"Node '{node_id}' opsi '{choice}' merujuk ke node "
                        f"'{target}' yang tidak terdefinisi"
                    )

        # Referential integrity untuk back_to (terminal & transitional)
        if node_type in ("terminal_state", "transitional_state"):
            back_to = node.get("back_to")
            if back_to is not None and back_to not in nodes:
                errors.append(
                    f"Node '{node_id}' back_to merujuk ke node "
                    f"'{back_to}' yang tidak terdefinisi"
                )

    if errors:
        error_msg = "Validasi data.json gagal:\n" + "\n".join(f"  - {e}" for e in errors)
        raise RuntimeError(error_msg)

def find_unreachable_nodes(entry_points: list[str] | None = None) -> list[str]:
    nodes = get_nodes()

    if entry_points is None:
        entry_points = [
            "user_sambutan", "user_menu_utama", "user_fallback"
        ]

    visited = set()
    queue = [n for n in entry_points if n in nodes]

    while queue:
        node_id = queue.pop()
        if node_id in visited:
            continue
        visited.add(node_id)

        node = nodes[node_id]
        node_type = node.get("type")

        if node_type == "menu_state":
            for target in node.get("options", {}).values():
                if target not in visited:
                    queue.append(target)

        if node_type in ("terminal_state", "transitional_state"):
            back_to = node.get("back_to")
            if back_to and back_to not in visited:
                queue.append(back_to)

    return sorted(set(nodes.keys()) - visited)