import asyncio
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from routers import (
    auth_routes, signup_routes, dashboard_routes,
    shipment_routes, device_stream_routes
)
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="supersecret")

# Register routers
app.include_router(auth_routes.router)
app.include_router(signup_routes.router)
app.include_router(dashboard_routes.router)
app.include_router(shipment_routes.router)
app.include_router(device_stream_routes.router)
