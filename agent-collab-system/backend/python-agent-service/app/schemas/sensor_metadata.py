from pydantic import BaseModel, Field


class SensorSourceTypeOption(BaseModel):
    value: str
    label: str


class SensorOperatorOption(BaseModel):
    value: str
    label: str
    supported_field_types: list[str] = Field(default_factory=list)


class SensorFieldOption(BaseModel):
    value: str
    label: str
    field_type: str
    suggested_values: list[str] = Field(default_factory=list)


class SensorEventKeyOption(BaseModel):
    value: str
    label: str


class SensorTableOption(BaseModel):
    value: str
    label: str
    event_keys: list[SensorEventKeyOption] = Field(default_factory=list)
    fields: list[SensorFieldOption] = Field(default_factory=list)


class SensorSourceOption(BaseModel):
    value: str
    label: str
    source_type: str
    tables: list[SensorTableOption] = Field(default_factory=list)


class SensorMetadataResponse(BaseModel):
    source_types: list[SensorSourceTypeOption] = Field(default_factory=list)
    operators: list[SensorOperatorOption] = Field(default_factory=list)
    sources: list[SensorSourceOption] = Field(default_factory=list)
