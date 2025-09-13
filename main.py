from fastapi import FastAPI, Request
import razorpay
import requests
import os

app = FastAPI()

# Razorpay keys (from Render env)
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

# Shiprocket credentials (from Render env)
SHIPROCKET_EMAIL = os.getenv("SHIPROCKET_EMAIL")
SHIPROCKET_PASSWORD = os.getenv("SHIPROCKET_PASSWORD")

razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


# ✅ Generate Razorpay Order (called by frontend before checkout)
@app.post("/create-order")
async def create_order(data: dict):
    amount = data["amount"]  # in INR
    receipt_id = data.get("receipt", "receipt#1")

    order = razorpay_client.order.create({
        "amount": amount * 100,  # Razorpay expects paise
        "currency": "INR",
        "receipt": receipt_id,
        "payment_capture": 1
    })

    return {"order_id": order["id"], "amount": amount}


# ✅ Razorpay Payment Success Webhook → Push to Shiprocket
@app.post("/razorpay-webhook")
async def razorpay_webhook(request: Request):
    body = await request.json()

    payment_id = body.get("razorpay_payment_id")
    order_id = body.get("razorpay_order_id")
    customer_name = body.get("name")
    customer_email = body.get("email")
    customer_phone = body.get("phone")

    # 🔑 Authenticate Shiprocket
    login_url = "https://apiv2.shiprocket.in/v1/external/auth/login"
    login_payload = {"email": SHIPROCKET_EMAIL, "password": SHIPROCKET_PASSWORD}
    login_res = requests.post(login_url, json=login_payload).json()
    token = login_res.get("token")

    # 🚚 Create Shiprocket Order
    headers = {"Authorization": f"Bearer {token}"}
    order_payload = {
        "order_id": order_id,
        "order_date": "2025-09-13",
        "pickup_location": "Primary",
        "channel_id": "",
        "billing_customer_name": customer_name,
        "billing_last_name": "",
        "billing_address": "Test Address",
        "billing_city": "Bangalore",
        "billing_pincode": "560001",
        "billing_state": "Karnataka",
        "billing_country": "India",
        "billing_email": customer_email,
        "billing_phone": customer_phone,
        "order_items": [
            {"name": "Test Product", "sku": "sku001", "units": 1, "selling_price": "500"}
        ],
        "payment_method": "Prepaid",
        "sub_total": 500,
        "length": 10,
        "breadth": 15,
        "height": 20,
        "weight": 2.5
    }
    order_res = requests.post(
        "https://apiv2.shiprocket.in/v1/external/orders/create/adhoc",
        headers=headers, json=order_payload
    ).json()

    return {"status": "success", "shiprocket_response": order_res}
