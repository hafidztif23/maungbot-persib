import logging
from core.loader import get_nodes
from core.session import (
    get_session,
    save_session,
    save_session_waiting,
)
from core.dispatcher import dispatch
from core.formatter import format_response

logger = logging.getLogger(__name__)

def process_input(id_account: int, user_input: str) -> str:
    user_input = user_input.strip()
    session = get_session(id_account)
 
    if session["waiting_input"]:
        return _handle_waiting_input(id_account, user_input, session)
 
    return _handle_menu_input(id_account, user_input, session)

def _handle_waiting_input(id_account: int, user_input: str, session: dict) -> str:
    action       = session["pending_action"]
    param_key    = session["pending_param_key"]
    back_to      = session["pending_back_to"]

    params = {param_key: user_input}
    result = dispatch(action, params, id_account)

    save_session(id_account, back_to)
    nodes = get_nodes()
    back_node = nodes[back_to]
 
    response = format_response(action, result)
    response += "\n\n" + _render_menu(back_node)
    return response

def _handle_menu_input(id_account: int, user_input: str, session: dict) -> str:

    nodes        = get_nodes()
    current_node = session["current_node"]
    node         = nodes.get(current_node)

    if node is None:
        logger.error(f"Node '{current_node}' tidak ditemukan, reset ke root")
        save_session(id_account, "root")
        return _render_menu(nodes["root"])

    options = node.get("options", {})
    next_node_id = options.get(user_input)
 
    if next_node_id is None:
        invalid_msg = (
            f"Pilihan '{user_input}' tidak tersedia. "
            f"Silakan pilih dari opsi yang ada.\n\n"
        )
        return invalid_msg + _render_menu(node)
 
    next_node = nodes.get(next_node_id)
    if next_node is None:
        logger.error(f"Target node '{next_node_id}' tidak terdefinisi")
        return "Terjadi kesalahan sistem. Silakan coba lagi.\n\n" + _render_menu(node)
 
    return _execute_node(id_account, next_node_id, next_node, nodes)

def _execute_node(
    id_account: int,
    node_id: str,
    node: dict,
    nodes: dict,
) -> str:
    node_type = node["type"]
 
    if node_type == "superstate":
        return _execute_superstate(id_account, node_id, node)
 
    if node_type == "terminal_state":
        return _execute_terminal(id_account, node_id, node, nodes)
 
    if node_type == "transitional_state":
        return _execute_transitional(id_account, node_id, node)
 
    logger.error(f"Tipe node tidak dikenal: '{node_type}' pada node '{node_id}'")
    return "Terjadi kesalahan sistem."

def _execute_superstate(id_account: int, node_id: str, node: dict) -> str:
    save_session(id_account, node_id)
    return _render_menu(node)

def _execute_terminal(
    id_account: int,
    node_id: str,
    node: dict,
    nodes: dict,
) -> str:
    action  = node["action"]
    params  = node.get("params", {})
    back_to = node["back_to"]

    if action == "static":
        params = {"content": node.get("content", "")}
 
    # Eksekusi action
    result = dispatch(action, params, id_account)
 
    # Simpan posisi ke back_to
    save_session(id_account, back_to)
    back_node = nodes[back_to]
 
    response = format_response(action, result)
    response += "\n\n" + _render_menu(back_node)
    return response

def _execute_transitional(id_account: int, node_id: str, node: dict) -> str:
    save_session_waiting(
        id_account=id_account,
        current_node=node_id,
        pending_action=node["action"],
        pending_param_key=node["param_key"],
        pending_back_to=node["back_to"],
    )
    return node["message"]

def _render_menu(node: dict) -> str:
    return node.get("message", "")

def get_initial_message() -> str:
    nodes = get_nodes()
    return _render_menu(nodes["root"])