from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AuthAccount:
    username: str
    password: str
    user_id: str
    dept_id: str
    display_name: str
    roles: tuple[str, ...] = ()


AUTH_ACCOUNTS: tuple[AuthAccount, ...] = (
    AuthAccount(username='production.li', password='dayan-prod-123', user_id='prod_li', dept_id='production', display_name='生产部 / 李工'),
    AuthAccount(username='warehouse.wang', password='dayan-warehouse-123', user_id='warehouse_wang', dept_id='warehouse', display_name='仓储部 / 王仓'),
    AuthAccount(username='supply.zhou', password='dayan-supply-123', user_id='supply_zhou', dept_id='supply_chain', display_name='供应链部 / 周链'),
    AuthAccount(username='ceo.demo', password='dayan-ceo-123', user_id='ceo_demo', dept_id='ceo', display_name='CEO / 全局查看', roles=('ceo',)),
)


def find_account_by_username(username: str) -> AuthAccount | None:
    normalized = username.strip().lower()
    for account in AUTH_ACCOUNTS:
      if account.username == normalized:
        return account
    return None
