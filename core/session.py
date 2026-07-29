from sqlalchemy import text
from core.db import engine


def get_session(id_account: int) -> dict:
    with engine.connect() as conn:
        row = conn.execute(
            text("""
                SELECT current_node, waiting_input,
                       pending_action, pending_param_key, pending_back_to
                FROM fsm_session
                WHERE id_account = :id_account
            """),
            {"id_account": id_account}
        ).fetchone()

    if row is None:
        return _default_session()

    return {
        "current_node":      row[0],
        "waiting_input":     row[1],
        "pending_action":    row[2],
        "pending_param_key": row[3],
        "pending_back_to":   row[4],
    }


def save_session(id_account: int, current_node: str) -> None:
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO fsm_session
                    (id_account, current_node, waiting_input,
                     pending_action, pending_param_key, pending_back_to, updated_at)
                VALUES
                    (:id_account, :current_node, FALSE,
                     NULL, NULL, NULL, NOW())
                ON CONFLICT (id_account) DO UPDATE SET
                    current_node    = EXCLUDED.current_node,
                    waiting_input   = FALSE,
                    pending_action  = NULL,
                    pending_param_key = NULL,
                    pending_back_to = NULL,
                    updated_at      = NOW()
            """),
            {"id_account": id_account, "current_node": current_node}
        )

def save_session_waiting(
    id_account: int,
    current_node: str,
    pending_action: str,
    pending_param_key: str,
    pending_back_to: str,
) -> None:
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO fsm_session
                    (id_account, current_node, waiting_input,
                     pending_action, pending_param_key, pending_back_to, updated_at)
                VALUES
                    (:id_account, :current_node, TRUE,
                     :pending_action, :pending_param_key, :pending_back_to, NOW())
                ON CONFLICT (id_account) DO UPDATE SET
                    current_node      = EXCLUDED.current_node,
                    waiting_input     = TRUE,
                    pending_action    = EXCLUDED.pending_action,
                    pending_param_key = EXCLUDED.pending_param_key,
                    pending_back_to   = EXCLUDED.pending_back_to,
                    updated_at        = NOW()
            """),
            {
                "id_account":       id_account,
                "current_node":     current_node,
                "pending_action":   pending_action,
                "pending_param_key": pending_param_key,
                "pending_back_to":  pending_back_to,
            }
        )


def reset_session(id_account: int) -> None:
    save_session_waiting(
        id_account=id_account,
        current_node="user_menu_utama",
        pending_action="route_menu",
        pending_param_key="user_input",
        pending_back_to="user_menu_utama",
    )


def delete_session(id_account: int) -> None:
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM fsm_session WHERE id_account = :id_account"),
            {"id_account": id_account}
        )


def _default_session() -> dict:
    return {
        "current_node":      "user_menu_utama",
        "waiting_input":     True,
        "pending_action":    "route_menu",
        "pending_param_key": "user_input",
        "pending_back_to":   "user_menu_utama",
    }