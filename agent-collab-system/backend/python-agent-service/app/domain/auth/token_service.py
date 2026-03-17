from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.core.config import settings


@dataclass(frozen=True, slots=True)
class AuthTokenPayload:
    user_id: str
    dept_id: str
    display_name: str
    roles: tuple[str, ...]
    expires_at: str


class AuthTokenService:
    def __init__(self, secret_key: str) -> None:
        self.secret_key = secret_key.encode('utf-8')

    def issue_token(self, *, user_id: str, dept_id: str, display_name: str, roles: tuple[str, ...]) -> tuple[str, AuthTokenPayload]:
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
        payload = {
            'user_id': user_id,
            'dept_id': dept_id,
            'display_name': display_name,
            'roles': list(roles),
            'expires_at': expires_at,
        }
        encoded = base64.urlsafe_b64encode(json.dumps(payload, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        signature = hmac.new(self.secret_key, encoded.encode('utf-8'), hashlib.sha256).hexdigest()
        token = f'{encoded}.{signature}'
        return token, AuthTokenPayload(user_id=user_id, dept_id=dept_id, display_name=display_name, roles=roles, expires_at=expires_at)

    def verify_token(self, token: str) -> AuthTokenPayload | None:
        if not token or '.' not in token:
            return None
        encoded, signature = token.rsplit('.', 1)
        expected = hmac.new(self.secret_key, encoded.encode('utf-8'), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            return None
        try:
            payload = json.loads(base64.urlsafe_b64decode(encoded.encode('utf-8')).decode('utf-8'))
        except Exception:
            return None
        expires_at = payload.get('expires_at')
        if not isinstance(expires_at, str):
            return None
        try:
            parsed_exp = datetime.fromisoformat(expires_at)
        except ValueError:
            return None
        if parsed_exp.tzinfo is None:
            parsed_exp = parsed_exp.replace(tzinfo=timezone.utc)
        if parsed_exp < datetime.now(timezone.utc):
            return None
        user_id = payload.get('user_id')
        dept_id = payload.get('dept_id')
        display_name = payload.get('display_name')
        roles = payload.get('roles')
        if not isinstance(user_id, str) or not isinstance(dept_id, str) or not isinstance(display_name, str) or not isinstance(roles, list):
            return None
        clean_roles = tuple(item for item in roles if isinstance(item, str) and item)
        return AuthTokenPayload(user_id=user_id, dept_id=dept_id, display_name=display_name, roles=clean_roles, expires_at=expires_at)


token_service = AuthTokenService(settings.app_name)
