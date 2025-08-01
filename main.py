from fastapi import FastAPI, HTTPException, Request
from models import WebhookPayload
from db import insert_data
import traceback

app = FastAPI()

@app.get("/")
def root():
    return {"message": "🚀 Miya Kebabs Webhook is live and ready to receive Petpooja orders! Please use /webhook url and send post requests"}

@app.post("/webhook")
async def webhook_handler(payload: WebhookPayload, request: Request):
    try:
        insert_data(payload)
        return {"status": "success", "message": "Data inserted successfully."}
    except Exception as e:
        print("[Webhook Error]", str(e))
        raise HTTPException(status_code=500, detail=str(e))