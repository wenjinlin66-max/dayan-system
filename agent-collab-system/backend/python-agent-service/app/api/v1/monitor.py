from fastapi import APIRouter

router = APIRouter()


@router.get("/metrics")
async def get_metrics() -> dict[str, list[dict[str, float]]]:
    return {"metrics": []}
