import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import (
    dashboard,
    calendar,
    itinerary,
    pois,
    weather,
    blossom,
    reminders,
    wishlist,
    chat,
    knowledge,
    admin,
    settings,
    ambient,
)

app = FastAPI(title="Shogun Web API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://shogun.ibbytech.com",
        "http://localhost:3000",
        "http://localhost:3010",
        "http://192.168.71.220:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)
app.include_router(calendar.router)
app.include_router(itinerary.router)
app.include_router(pois.router)
app.include_router(weather.router)
app.include_router(blossom.router)
app.include_router(reminders.router)
app.include_router(wishlist.router)
app.include_router(chat.router)
app.include_router(knowledge.router)
app.include_router(admin.router)
app.include_router(settings.router)
app.include_router(ambient.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "shogun-web-api", "version": "1.0.0"}
