from fastapi import APIRouter
from app.api.routes.query import router as query_router
from app.api.routes.ops import router as ops_router

router = APIRouter()
router.include_router(query_router)
router.include_router(ops_router)
