from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.loader import load_tree
from routes import auth, chat

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_tree("data.json")
    yield

app = FastAPI(
    title="MaungBot FSM API",
    description="Chatbot customer service Persib Bandung berbasis Hierarchical Finite State Machine",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)

@app.get("/")
def root():
    return {"status": "ok", "service": "MaungBot FSM API"}