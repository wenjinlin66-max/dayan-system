from fastapi import APIRouter

from app.api.v1.approvals import router as approvals_router
from app.api.v1.chat import router as chat_router
from app.api.v1.executions import router as executions_router
from app.api.v1.monitor import router as monitor_router
from app.api.v1.workflows import router as workflows_router

api_router = APIRouter()
api_router.include_router(workflows_router, prefix="/v1/workflows", tags=["workflows"])
api_router.include_router(executions_router, prefix="/v1/executions", tags=["executions"])
api_router.include_router(chat_router, prefix="/v1/chat", tags=["chat"])
api_router.include_router(monitor_router, prefix="/v1/monitor", tags=["monitor"])
api_router.include_router(approvals_router, prefix="/v1/approvals", tags=["approvals"])
