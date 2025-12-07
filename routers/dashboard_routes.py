from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from utils.auth_guard import require_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/dashboard")
async def dashboard(request: Request):
    guard = await require_user(request)
    if not guard:
        return RedirectResponse("/login", 303)

    message = request.session.get("flash_message")
    msg_type = request.session.get("flash_type")

    if "flash_message" in request.session:
        del request.session["flash_message"]
    if "flash_type" in request.session:
        del request.session["flash_type"]

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "username": request.session.get("user_name"),
        "message": message,
        "msg_type": msg_type
    })
