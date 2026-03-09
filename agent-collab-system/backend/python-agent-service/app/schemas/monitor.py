from pydantic import BaseModel


class MetricPoint(BaseModel):
    metric_type: str
    value: float
