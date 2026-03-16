"""
Knowledge router — currently routes to POI knowledge endpoint.
Kept as a dedicated router for future expansion (e.g. general knowledge search).
"""
from fastapi import APIRouter

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
# POI-specific knowledge is handled in pois.py at /pois/{id}/knowledge
