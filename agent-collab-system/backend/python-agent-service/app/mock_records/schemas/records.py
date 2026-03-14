from pydantic import BaseModel, Field


class MockRecordsSourceItem(BaseModel):
    source_system: str
    label: str


class MockRecordsTableSchemaField(BaseModel):
    name: str
    label: str
    field_type: str
    editable: bool = True


class MockRecordsTableSchemaResponse(BaseModel):
    table_name: str
    label: str
    source_system: str
    fields: list[MockRecordsTableSchemaField] = Field(default_factory=list)


class MockRecordsTableItem(BaseModel):
    table_name: str
    label: str
    source_system: str
    description: str


class MockRecordsSourcesResponse(BaseModel):
    sources: list[MockRecordsSourceItem] = Field(default_factory=list)


class MockRecordsTablesResponse(BaseModel):
    tables: list[MockRecordsTableItem] = Field(default_factory=list)


class MockRecordsRowListResponse(BaseModel):
    table_name: str
    rows: list[dict[str, object]] = Field(default_factory=list)


class MockRecordUpsertRequest(BaseModel):
    values: dict[str, object] = Field(default_factory=dict)


class MockRecordMutationResponse(BaseModel):
    table_name: str
    record_id: str
    row: dict[str, object]
    change_event_id: str
    triggered_execution_ids: list[str] = Field(default_factory=list)


class MockRecordsRecentEventItem(BaseModel):
    change_event_id: str
    table_name: str
    record_id: str
    operation: str
    event_type: str
    changed_fields: list[str] = Field(default_factory=list)
    triggered_execution_ids: list[str] = Field(default_factory=list)
    created_at: str | None = None


class MockRecordsRecentEventsResponse(BaseModel):
    events: list[MockRecordsRecentEventItem] = Field(default_factory=list)
