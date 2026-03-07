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
    
    all_devices = list(devices.find({}, {"_id": 0}))    
    assigned = [d["device_id"] for d in devices.find({"status": "assigned"}, {"_id": 0})]

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

    # Fetch all past device stream entries
    data = list(device_stream_collection.find({}, {"_id": 0}))
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
    except Exception as e:
        connected_websockets.discard(ws)
