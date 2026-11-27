import httpx2
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.accounts.models import Account
from app.core.config import Settings
from app.core.errors import ApiError


async def exchange_code(settings: Settings, code: str) -> str:
    secret = settings.wechat_app_secret
    if not settings.wechat_login_enabled or secret is None:
        raise ApiError(503, "wechat_unavailable", "小程序微信登录暂未配置，可使用邮箱登录。")
    try:
        async with httpx2.AsyncClient(timeout=6) as client:
            response = await client.get(
                "https://api.weixin.qq.com/sns/jscode2session",
                params={
                    "appid": settings.wechat_app_id,
                    "secret": secret.get_secret_value(),
                    "js_code": code,
                    "grant_type": "authorization_code",
                },
            )
            response.raise_for_status()
            payload = response.json()
    except (httpx2.HTTPError, ValueError) as error:
        raise ApiError(503, "wechat_service_failed", "微信服务暂不可用，请稍后重试。") from error
    if not isinstance(payload, dict):
        raise ApiError(503, "wechat_service_failed", "微信登录暂不可用，请稍后重试。")
    open_id = payload.get("openid")
    error_code = payload.get("errcode")
    if error_code or not isinstance(open_id, str) or not 1 <= len(open_id) <= 128:
        if error_code in (40029, 40163):
            raise ApiError(401, "wechat_code_invalid", "微信登录状态已失效，请重新授权。")
        raise ApiError(503, "wechat_service_failed", "微信登录暂不可用，请稍后重试。")
    return open_id


async def linked_account(db: AsyncSession, app_id: str, open_id: str) -> Account | None:
    return await db.scalar(
        select(Account).where(
            Account.wechat_app_id == app_id,
            Account.wechat_open_id == open_id,
        )
    )
