from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db_session, get_mock_db_session, get_request_context
from app.core.security import RequestContext
from app.mock_records.schemas.records import (
    MockRecordMutationResponse,
    MockRecordsRecentEventsResponse,
    MockRecordsRowListResponse,
    MockRecordsSourcesResponse,
    MockRecordsTableSchemaResponse,
    MockRecordsTablesResponse,
    MockRecordUpsertRequest,
)
from app.mock_records.service.records_service import MockRecordsService

router = APIRouter()


def build_service(mock_session: AsyncSession, main_session: AsyncSession) -> MockRecordsService:
    return MockRecordsService(mock_session=mock_session, main_session=main_session)


@router.get("/sources", response_model=MockRecordsSourcesResponse)
async def list_record_sources(
    mock_session: AsyncSession = Depends(get_mock_db_session),
    main_session: AsyncSession = Depends(get_db_session),
) -> MockRecordsSourcesResponse:
    return build_service(mock_session, main_session).list_sources()


@router.get("/tables", response_model=MockRecordsTablesResponse)
async def list_record_tables(
    mock_session: AsyncSession = Depends(get_mock_db_session),
    main_session: AsyncSession = Depends(get_db_session),
) -> MockRecordsTablesResponse:
    return build_service(mock_session, main_session).list_tables()


@router.get("/tables/{table_name}/schema", response_model=MockRecordsTableSchemaResponse)
async def get_record_table_schema(
    table_name: str,
    mock_session: AsyncSession = Depends(get_mock_db_session),
    main_session: AsyncSession = Depends(get_db_session),
) -> MockRecordsTableSchemaResponse:
    try:
        return build_service(mock_session, main_session).get_table_schema(table_name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/tables/{table_name}/rows", response_model=MockRecordsRowListResponse)
async def list_record_rows(
    table_name: str,
    mock_session: AsyncSession = Depends(get_mock_db_session),
    main_session: AsyncSession = Depends(get_db_session),
) -> MockRecordsRowListResponse:
    try:
        return await build_service(mock_session, main_session).list_rows(table_name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/tables/{table_name}/rows", response_model=MockRecordMutationResponse)
async def create_record_row(
    table_name: str,
    payload: MockRecordUpsertRequest,
    context: RequestContext = Depends(get_request_context),
    mock_session: AsyncSession = Depends(get_mock_db_session),
    main_session: AsyncSession = Depends(get_db_session),
) -> MockRecordMutationResponse:
    try:
        return await build_service(mock_session, main_session).create_row(table_name, payload.values, dept_id=context.dept_id, user_id=context.user_id)
    except ValueError as exc:
        code = status.HTTP_404_NOT_FOUND if str(exc) == "RECORDS_TABLE_NOT_FOUND" else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=str(exc)) from exc


@router.put("/tables/{table_name}/rows/{record_id}", response_model=MockRecordMutationResponse)
async def update_record_row(
    table_name: str,
    record_id: str,
    payload: MockRecordUpsertRequest,
    context: RequestContext = Depends(get_request_context),
    mock_session: AsyncSession = Depends(get_mock_db_session),
    main_session: AsyncSession = Depends(get_db_session),
) -> MockRecordMutationResponse:
    try:
        return await build_service(mock_session, main_session).update_row(table_name, record_id, payload.values, dept_id=context.dept_id, user_id=context.user_id)
    except ValueError as exc:
        code = status.HTTP_404_NOT_FOUND if str(exc) in {"RECORDS_TABLE_NOT_FOUND", "RECORD_NOT_FOUND"} else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=str(exc)) from exc


@router.delete("/tables/{table_name}/rows/{record_id}", response_model=MockRecordMutationResponse)
async def delete_record_row(
    table_name: str,
    record_id: str,
    context: RequestContext = Depends(get_request_context),
    mock_session: AsyncSession = Depends(get_mock_db_session),
    main_session: AsyncSession = Depends(get_db_session),
) -> MockRecordMutationResponse:
    try:
        return await build_service(mock_session, main_session).delete_row(table_name, record_id, dept_id=context.dept_id, user_id=context.user_id)
    except ValueError as exc:
        code = status.HTTP_404_NOT_FOUND if str(exc) in {"RECORDS_TABLE_NOT_FOUND", "RECORD_NOT_FOUND"} else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=str(exc)) from exc


@router.get("/events/recent", response_model=MockRecordsRecentEventsResponse)
async def list_recent_record_events(
    mock_session: AsyncSession = Depends(get_mock_db_session),
    main_session: AsyncSession = Depends(get_db_session),
) -> MockRecordsRecentEventsResponse:
    return await build_service(mock_session, main_session).list_recent_events()
