from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import razorpay
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Razorpay client setup
razorpay_client = razorpay.Client(
    auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET"))
)


@app.get("/")
async def root():
    return {"message": "Razorpay FastAPI backend is running 🚀"}


@app.post("/create-order")
async def create_order(request: Request):
    data = await request.json()
    amount = data.get("amount", 500)  # Default 500 paise = ₹5.00

    try:
        order = razorpay_client.order.create({
            "amount": amount,
            "currency": "INR",
            "payment_capture": 1
        })
        return JSONResponse(content=order)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/razorpay-webhook")
async def razorpay_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")

    try:
        # Webhook secret should match the one in Razorpay Dashboard
        webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")
        razorpay_client.utility.verify_webhook_signature(body, signature, webhook_secret)

        return {"status": "Webhook verified ✅"}

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)
