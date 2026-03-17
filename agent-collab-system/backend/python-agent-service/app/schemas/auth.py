from pydantic import BaseModel, Field


class AuthLoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class AuthIdentityResponse(BaseModel):
    user_id: str
    dept_id: str
    display_name: str
    roles: list[str]


class AuthLoginResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    identity: AuthIdentityResponse
