from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.database import users_collection
from utils.email_utils import send_email
from utils.jwt_utility import create_access_token, create_refresh_token
from app.oauth import oauth
import random, time, os, requests

router = APIRouter()
templates = Jinja2Templates(directory="templates")

reset_otps = {}


@router.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {
        "request": request,
        "message": "",
        "RECAPTCHA_SITE_KEY": os.getenv("RECAPTCHA_SITE_KEY")
    })


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, forgot: bool = False):
    forgot_stage = "email" if forgot else None
    return templates.TemplateResponse("login.html", {
        "request": request,
        "message": "",
        "forgot_stage": forgot_stage,
        "RECAPTCHA_SITE_KEY": os.getenv("RECAPTCHA_SITE_KEY")
    })


@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    email: str = Form(None),
    password: str = Form(None),
    forgot_email: str = Form(None),
    forgot_otp: str = Form(None),
    new_password: str = Form(None),
    forgot_action: str = Form(None),
    g_recaptcha_response: str | None = Form(None, alias="g-recaptcha-response")
):

    # ========== RECAPTCHA VALIDATION (ONLY LOGIN) ==========
    if not forgot_action:
        if not g_recaptcha_response:  # Check if box is not clicked
            return templates.TemplateResponse("login.html", {
                "request": request,
                "message": "⚠️ Please verify the reCAPTCHA.",
                "forgot_stage": None,
                "RECAPTCHA_SITE_KEY": os.getenv("RECAPTCHA_SITE_KEY")
            })

        verify_url = "https://www.google.com/recaptcha/api/siteverify"
        secret_key = os.getenv("RECAPTCHA_SECRET_KEY")
        payload = {"secret": secret_key, "response": g_recaptcha_response}

        recaptcha_result = requests.post(verify_url, data=payload).json()

        if not recaptcha_result.get("success"):
            return templates.TemplateResponse("login.html", {
                "request": request,
                "message": "❌ reCAPTCHA verification failed. Try again.",
                "forgot_stage": None,
                "RECAPTCHA_SITE_KEY": os.getenv("RECAPTCHA_SITE_KEY")
            })
    # ======================================================

    # NORMAL LOGIN
    if not forgot_action:
        user = await users_collection.find_one({"email": email})
        if user:
            if user["auth_provider"] == "google":
                return templates.TemplateResponse("login.html", {
                    "request": request,
                    "message": "⚠️ This account was created using Google. Please login with Google.",
                    "forgot_stage": None,
                    "RECAPTCHA_SITE_KEY": os.getenv("RECAPTCHA_SITE_KEY")
                })

            if user["password"] == password:
                access = create_access_token({"sub": email})
                refresh = create_refresh_token({"sub": email})

                request.session["access_token"] = access
                request.session["refresh_token"] = refresh
                request.session["email"] = user["email"]
                request.session["user_name"] = user.get("name")
                request.session["logged_in"] = True

                request.session["flash_message"] = "Login Successful Welcome Back!"
                request.session["flash_type"] = "success"

                return RedirectResponse(url="/base", status_code=303)

            else:
                return templates.TemplateResponse("login.html", {
                    "request": request,
                    "message": "❌ Invalid password.",
                    "forgot_stage": None,
                    "RECAPTCHA_SITE_KEY": os.getenv("RECAPTCHA_SITE_KEY")
                })

        else:
            return templates.TemplateResponse("login.html", {
                "request": request,
                "message": "⚠️ User not found. Please sign up.",
                "forgot_stage": None,
                "RECAPTCHA_SITE_KEY": os.getenv("RECAPTCHA_SITE_KEY")
            })


    # SEND OTP
    if forgot_action == "send_otp":
        user = await users_collection.find_one({"email": forgot_email})
        if not user:
            return templates.TemplateResponse("login.html", {
                "request": request,
                "message": "❌ No account found with this email.",
                "forgot_stage": "email",
                "RECAPTCHA_SITE_KEY": os.getenv("RECAPTCHA_SITE_KEY")
            })

        otp = str(random.randint(100000, 999999))
        reset_otps[forgot_email] = {"otp": otp, "expires": time.time() + 120}
        await send_email("OTP Verification", forgot_email, f"Your OTP is {otp}")

        return templates.TemplateResponse("login.html", {
            "request": request,
            "message": f"📨 OTP sent to {forgot_email}. Check your inbox.",
            "forgot_stage": "otp",
            "forgot_email": forgot_email,
            "RECAPTCHA_SITE_KEY": os.getenv("RECAPTCHA_SITE_KEY")
        })


    # VERIFY OTP
    if forgot_action == "verify_otp":
        otp_data = reset_otps.get(forgot_email)
        if not otp_data or time.time() > otp_data["expires"]:
            return templates.TemplateResponse("login.html", {
                "request": request,
                "message": "⏰ OTP expired. Try again.",
                "forgot_stage": "email",
                "RECAPTCHA_SITE_KEY": os.getenv("RECAPTCHA_SITE_KEY")
            })

        if otp_data["otp"] == forgot_otp:
            await users_collection.update_one({"email": forgot_email}, {"$set": {"password": new_password}})
            del reset_otps[forgot_email]
            return templates.TemplateResponse("login.html", {
                "request": request,
                "message": "🎉 Password reset successful! You can now login.",
                "forgot_stage": None,
                "RECAPTCHA_SITE_KEY": os.getenv("RECAPTCHA_SITE_KEY")
            })

        return templates.TemplateResponse("login.html", {
            "request": request,
            "message": "❌ Invalid OTP.",
            "forgot_stage": "otp",
            "forgot_email": forgot_email,
            "RECAPTCHA_SITE_KEY": os.getenv("RECAPTCHA_SITE_KEY")
        })


# GOOGLE LOGIN
@router.get("/login/google")
async def login_google(request: Request):
    redirect_uri = request.url_for("auth")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/auth")
async def auth(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")

    email = user_info["email"]
    name = user_info.get("name", "")

    user = await users_collection.find_one({"email": email})
    if not user:
        await users_collection.insert_one({
            "name": name,
            "email": email,
            "auth_provider": "google"
        })

    access = create_access_token({"sub": email})
    refresh = create_refresh_token({"sub": email})

    request.session["access_token"] = access
    request.session["refresh_token"] = refresh
    request.session["user_name"] = name
    request.session["email"] = email

    request.session["flash_message"] = "Logged in with Google successfully!"
    request.session["flash_type"] = "success"

    return RedirectResponse("/base", 303)


@router.get("/base")
async def auth(request: Request):
    return RedirectResponse(url="/dashboard", status_code=303)
