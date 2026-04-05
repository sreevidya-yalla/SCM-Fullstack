from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.database import users_collection
from utils.email_utils import send_email
import random

router = APIRouter()

templates = Jinja2Templates(directory="templates")
temp_users = {}

@router.get("/signup")
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@router.post("/signup")
async def signup(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    otp: str = Form(None)
):

    # --------------- FIRST STEP (SEND OTP) ---------------
    if not otp:
        existing_user = await users_collection.find_one({"email": email})
        if existing_user:
            return templates.TemplateResponse("signup.html", {
                "request": request,
                "message": "⚠️ Email already exists. Please login.",
                "otp_stage": False
            })
        
        generated_otp = str(random.randint(100000, 999999))

        # Store temporarily in memory
        temp_users[email] = {
            "name": name,
            "email": email,
            "password": password,
            "otp": generated_otp
        }

        await send_email("OTP Verification", email, f"Your OTP is {generated_otp}")

        return templates.TemplateResponse("signup.html", {
            "request": request,
            "message": f"✅ OTP sent to {email}. Please verify below.",
            "otp_stage": True,
            "email": email
        })

    # --------------- SECOND STEP (VERIFY OTP) ---------------
    user_data = temp_users.get(email)

    if not user_data:
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "message": "⚠️ Session expired or invalid. Please sign up again.",
            "otp_stage": False
        })

    if user_data["otp"] == otp:

        await users_collection.insert_one({
            "name": user_data["name"],
            "email": user_data["email"],
            "password": user_data["password"],
            "auth_provider": "local"
        })

        del temp_users[email]

        return templates.TemplateResponse("signup.html", {
            "request": request,
            "message": "🎉 Signup successful! You can now login.",
            "otp_stage": False
        })

    # --------------- WRONG OTP ---------------
    return templates.TemplateResponse("signup.html", {
        "request": request,
        "message": "❌ Invalid OTP. Please try again.",
        "otp_stage": True,
        "email": email,
        "name": name,
        "password": password
    })
