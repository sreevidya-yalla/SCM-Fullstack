# routers/device_stream_routes.py

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse
from app.database import devices, device_stream_collection
from app.websocket_manager import connected_websockets
import asyncio
from utils.auth_guard import require_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# -----------------------------------------
# PAGE ROUTE (Loads HTML)
# -----------------------------------------
@router.get("/device-stream")
async def device_stream(request: Request):
    guard = await require_user(request)
    if not guard:
        return RedirectResponse("/login", 303)

    # Async: fetch all devices
    all_devices = await devices.find({}, {"_id": 0}).to_list(length=None)

    # Async: fetch assigned devices only
    assigned_docs = await devices.find(
        {"status": "assigned"},
        {"_id": 0, "device_id": 1}
    ).to_list(length=None)

    assigned = [d["device_id"] for d in assigned_docs]

    return templates.TemplateResponse("device_stream.html", {
        "request": request,
        "devices": all_devices,
        "assigned_ids": assigned
    })


# -----------------------------------------
# HISTORY API (Load MongoDB stored data)
# -----------------------------------------
@router.get("/device-stream/history")
async def device_stream_history(request: Request):
    guard = await require_user(request)
    if not guard:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    # Async: fetch all past device stream entries
    data = await device_stream_collection.find({}, {"_id": 0}).to_list(length=None)
    return JSONResponse(data)


# -----------------------------------------
# REAL-TIME WEBSOCKET STREAM
# -----------------------------------------
@router.websocket("/ws/device-stream")
async def ws_device_stream(ws: WebSocket):
    await ws.accept()
    connected_websockets.add(ws)

    try:
        while True:
            await asyncio.sleep(1)  # Keep socket alive
    except WebSocketDisconnect:
        connected_websockets.discard(ws)
    except Exception:
        connected_websockets.discard(ws)
