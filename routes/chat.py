from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from core.engine import process_input, get_initial_message
from core.session import get_session
from core.dependencies import get_current_account

router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    current_node: str
    waiting_input: bool

@router.post("", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    current_user: dict = Depends(get_current_account),
):
    id_account = current_user["id_account"]

    if not body.message.strip():
        raise HTTPException(status_code=400, detail="Pesan tidak boleh kosong.")

    response = process_input(id_account, body.message)

    # Ambil session terbaru setelah diproses untuk dikembalikan ke frontend
    session = get_session(id_account)

    return ChatResponse(
        response=response,
        current_node=session["current_node"],
        waiting_input=session["waiting_input"],
    )

@router.get("/start", response_model=ChatResponse)
def start_chat(
    current_user: dict = Depends(get_current_account),
):
    id_account = current_user["id_account"]
    response = get_initial_message()
    session = get_session(id_account)

    return ChatResponse(
        response=response,
        current_node=session["current_node"],
        waiting_input=session["waiting_input"],
    )