from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_request_context
from app.core.security import RequestContext
from app.domain.auth.directory import find_account_by_username
from app.domain.auth.token_service import token_service
from app.schemas.auth import AuthIdentityResponse, AuthLoginRequest, AuthLoginResponse

router = APIRouter()


@router.post('/login', response_model=AuthLoginResponse)
async def login(payload: AuthLoginRequest) -> AuthLoginResponse:
    account = find_account_by_username(payload.username)
    if account is None or account.password != payload.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='AUTH_INVALID_CREDENTIALS')
    token, token_payload = token_service.issue_token(
        user_id=account.user_id,
        dept_id=account.dept_id,
        display_name=account.display_name,
        roles=account.roles,
    )
    return AuthLoginResponse(
        access_token=token,
        identity=AuthIdentityResponse(
            user_id=token_payload.user_id,
            dept_id=token_payload.dept_id,
            display_name=token_payload.display_name,
            roles=list(token_payload.roles),
        ),
    )


@router.get('/me', response_model=AuthIdentityResponse)
async def me(context: RequestContext = Depends(get_request_context)) -> AuthIdentityResponse:
    if context.user_id in {'system', 'default'}:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='AUTH_UNAUTHORIZED')
    return AuthIdentityResponse(
        user_id=context.user_id,
        dept_id=context.dept_id,
        display_name=context.display_name or context.user_id,
        roles=context.roles,
    )
