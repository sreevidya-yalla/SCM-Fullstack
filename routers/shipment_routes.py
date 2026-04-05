from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.database import devices, shipments, users_collection
from utils.auth_guard import require_user
import time, random
from utils.email_utils import send_email

reset_otps = {}
router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/create-shipment")
async def create_shipment_page(request: Request):

    guard = await require_user(request)
    if not guard:
        return RedirectResponse("/login", 303)

    # Async fetch available devices
    available_devices = await devices.find(
        {"status": "available"}, {"_id": 0}
    ).to_list(length=None)

    return templates.TemplateResponse("shipment.html", {
        "request": request,
        "devices": available_devices
    })


@router.post("/shipment")
async def create_shipment(
    request: Request,
    shipment_number: str = Form(...),
    container_number: str = Form(...),
    route_details: str = Form(...),
    goods_type: str = Form(...),
    device_id: int = Form(...),
    expected_delivery: str = Form(...),
    po_number: str = Form(...),
    delivery_number: str = Form(...),
    ndc_number: str = Form(...),
    batch_id: str = Form(...),
    serial_number: str = Form(...),
    description: str = Form(...)
):

    guard = await require_user(request)
    if not guard:
        return RedirectResponse("/login", 303)

    # Check if device exists
    device = await devices.find_one({"device_id": device_id})
    if not device:
        return HTMLResponse("❌ Device not found", status_code=400)

    # Check if assigned already
    if device["status"] == "assigned":
        return HTMLResponse("❌ Device already assigned", status_code=400)

    # Save shipment
    shipment_data = {
        "shipment_number": shipment_number,
        "container_number": container_number,
        "route_details": route_details,
        "goods_type": goods_type,
        "device_id": device_id,
        "expected_delivery": expected_delivery,
        "po_number": po_number,
        "delivery_number": delivery_number,
        "ndc_number": ndc_number,
        "batch_id": batch_id,
        "serial_number": serial_number,
        "description": description
    }

    await shipments.insert_one(shipment_data)

    # Mark device as assigned
    await devices.update_one(
        {"device_id": device_id},
        {"$set": {"status": "assigned"}}
    )

    request.session["flash_message"] = "Shipment created successfully!"
    request.session["flash_type"] = "shipment"

    return RedirectResponse(url="/dashboard?success=1", status_code=303)


@router.get("/shipments", response_class=HTMLResponse)
async def list_shipments(request: Request):

    guard = await require_user(request)
    if not guard:
        return RedirectResponse("/login", 303)

    # Async fetch all shipments
    all_shipments = await shipments.find(
        {}, {"_id": 0}
    ).to_list(length=None)

    return templates.TemplateResponse("shipments.html", {
        "request": request,
        "shipments": all_shipments
    })


@router.api_route("/account", methods=["GET", "POST"])
async def account(request: Request):

    email = request.session.get("email")
    user = await users_collection.find_one({"email": email}, {"_id": 0})

    if request.method == "POST":
        data = await request.json()
        action = data.get("action")

        if action == "send_otp":
            otp = str(random.randint(100000, 999999))
            reset_otps[email] = {"otp": otp, "expires": time.time() + 120}

            await send_email("Password Reset OTP", email, f"Your OTP is {otp}")

            return JSONResponse({"success": True, "message": "OTP sent to your email."})

        if action == "verify_and_update":
            otp = data.get("otp")
            new_pass = data.get("password")
            otp_data = reset_otps.get(email)

            if not otp_data:
                return JSONResponse({"success": False, "message": "OTP not sent."})

            if time.time() > otp_data["expires"]:
                return JSONResponse({"success": False, "message": "OTP expired."})

            if otp_data["otp"] != otp:
                return JSONResponse({"success": False, "message": "Invalid OTP."})

            await users_collection.update_one(
                {"email": email},
                {"$set": {"password": new_pass}}
            )

            del reset_otps[email]
            return JSONResponse({"success": True, "message": "Password updated successfully!"})

    return templates.TemplateResponse(
        "account.html",
        {"request": request, "user": user}
    )
