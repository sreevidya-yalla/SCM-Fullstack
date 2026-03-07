from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.database import users_collection
from utils.email_utils import send_email
from utils.jwt_utility import create_access_token, create_refresh_token
from app.oauth import oauth
import random, time

router = APIRouter()

templates = Jinja2Templates(directory="templates")

reset_otps = {}

@router.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "message": ""})


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, forgot: bool = False):
    forgot_stage = "email" if forgot else None
    return templates.TemplateResponse("login.html", {
        "request": request,
        "message": "",
        "forgot_stage": forgot_stage
    })


@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    email: str = Form(None),
    password: str = Form(None),
    forgot_email: str = Form(None),
    forgot_otp: str = Form(None),
    new_password: str = Form(None),
    forgot_action: str = Form(None)
):
    if not forgot_action:
        user = users_collection.find_one({"email": email})
        if user:
            if user["auth_provider"] == "google":
                message = "⚠️ This account was created using Google. Please login with Google or reset your password."
                return templates.TemplateResponse("login.html", {
                    "request": request,
                    "message": message,
                    "forgot_stage": None
                })

            if user["password"] == password:
                access = create_access_token({"sub": email})
                refresh = create_refresh_token({"sub": email})

                request.session["access_token"] = access
                request.session["refresh_token"] = refresh
                request.session["email"] = user["email"]
                request.session["user_name"] = user.get("name")
                request.session["logged_in"] = True

                request.session["flash_message"] = "Login Successful Welcome back!"
                request.session["flash_type"] = "success"

                return RedirectResponse(url="/base", status_code=303)

            else:
                message = "❌ Invalid password."
                return templates.TemplateResponse("login.html", {"request": request, "message": message, "forgot_stage": None})

        else:
            message = "⚠️ User not found. Please sign up."
            return templates.TemplateResponse("login.html", {"request": request, "message": message, "forgot_stage": None})

    if forgot_action == "send_otp":
        user = users_collection.find_one({"email": forgot_email})
        if not user:
            return templates.TemplateResponse("login.html", {
                "request": request,
                "message": "❌ No account found with this email.",
                "forgot_stage": "email"
            })

        otp = str(random.randint(100000, 999999))
        reset_otps[forgot_email] = {"otp": otp, "expires": time.time() + 120}
        await send_email("OTP Verification", forgot_email, f"Your OTP is {otp}")

        return templates.TemplateResponse("login.html", {
            "request": request,
            "message": f"✅ OTP sent to {forgot_email}. Check your inbox.",
            "forgot_stage": "otp",
            "forgot_email": forgot_email
        })

    if forgot_action == "verify_otp":
        otp_data = reset_otps.get(forgot_email)
        if not otp_data or time.time() > otp_data["expires"]:
            return templates.TemplateResponse("login.html", {
                "request": request,
                "message": "⏰ OTP expired. Please try again.",
                "forgot_stage": "email"
            })

        if otp_data["otp"] == forgot_otp:
            users_collection.update_one({"email": forgot_email}, {"$set": {"password": new_password}})
            del reset_otps[forgot_email]
            return templates.TemplateResponse("login.html", {
                "request": request,
                "message": "🎉 Password reset successful! You can now login.",
                "forgot_stage": None
            })
        else:
            return templates.TemplateResponse("login.html", {
                "request": request,
                "message": "❌ Invalid OTP. Try again.",
                "forgot_stage": "otp",
                "forgot_email": forgot_email
            })


@router.get("/login/google")
async def login_google(request: Request):
    redirect_uri = request.url_for("auth")
    print(">>>>>>>")
    print(redirect_uri,">>>>>")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/auth")
async def auth(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")

    email = user_info["email"]
    name = user_info.get("name", "")

    user = users_collection.find_one({"email": email})
    if not user:
        users_collection.insert_one({
            "name": name,
            "email": email,
            "auth_provider": "google"
        })

    access = create_access_token({"sub": email})
    refresh = create_refresh_token({"sub": email})

    request.session["access_token"] = access
    request.session["refresh_token"] = refresh
    request.session["user_name"] = name
    request.session["email"] = user["email"]

    request.session["flash_message"] = "Logged in with Google successfully!"
    request.session["flash_type"] = "success"

    return RedirectResponse("/base", 303)


# BASE redirection with exception handling
@router.get("/base")
async def auth(request: Request):
    try:
        return RedirectResponse(url="/dashboard", status_code=303)
    except Exception as e:
        print("Dashboard load error:", e)
        return RedirectResponse(url="/dashboard", status_code=303)




@router.get("/logout")
async def logout(request: Request):
    request.session.clear()   
    return RedirectResponse("/login", status_code=303)
