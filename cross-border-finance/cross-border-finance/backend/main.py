import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from data_store import store
from compliance import check_transfer
from agent import CrossBorderAgent

app = FastAPI(title="Intelligent Cross-Border Finance")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = None


def get_agent() -> CrossBorderAgent:
    global agent
    if agent is None:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise HTTPException(
                status_code=500,
                detail="ANTHROPIC_API_KEY is not set. Add it to a .env file in backend/ (see .env.example).",
            )
        agent = CrossBorderAgent()
    return agent


# ---------- schemas ----------
class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


class ConvertRequest(BaseModel):
    amount: float
    from_currency: str
    to_currency: str


class TransferRequest(BaseModel):
    recipient: str
    amount: float
    from_currency: str
    to_currency: str
    provider_id: str


# ---------- API routes ----------
@app.get("/api/rates")
def get_rates():
    return {"base": store.base_currency, "updated": store.rates_updated, "rates": store.rates}

@app.get("/api/rate")
def get_rate(from_currency: str, to_currency: str):
    return {"rate": store.get_rate(from_currency, to_currency)}

@app.post("/api/convert")
def convert(req: ConvertRequest):
    return store.convert(req.amount, req.from_currency, req.to_currency)

@app.get("/api/providers/compare")
def compare(amount: float, from_currency: str, to_currency: str):
    return store.compare_providers(amount, from_currency, to_currency)

@app.get("/api/compliance/check")
def compliance_check(recipient: str, amount: float, from_currency: str):
    flags = check_transfer(recipient, amount, from_currency)
    return {"flags": flags, "clear": len(flags) == 0}

@app.post("/api/transfers")
def create_transfer(req: TransferRequest):
    return store.create_transfer(req.recipient, req.amount, req.from_currency, req.to_currency, req.provider_id)

@app.get("/api/transfers")
def get_transfers(limit: int = 20):
    return store.get_transfers(limit)

@app.post("/api/chat")
def chat(req: ChatRequest):
    return get_agent().chat(req.message, req.history)


# ---------- serve the simple frontend ----------
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
