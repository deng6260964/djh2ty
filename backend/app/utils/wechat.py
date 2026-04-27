import httpx
from typing import Optional
from loguru import logger
from app.config import settings


WECHAT_CODE2SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"
WECHAT_ACCESS_TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
WECHAT_SEND_MSG_URL = "https://api.weixin.qq.com/cgi-bin/message/subscribe/send"


async def get_wechat_openid(code: str) -> Optional[dict]:
    """
    通过微信 code 换取 openid 和 session_key
    Returns: {"openid": "...", "session_key": "..."} or None
    """
    if not settings.WECHAT_APP_ID or not settings.WECHAT_APP_SECRET:
        logger.warning("微信 AppID 或 AppSecret 未配置")
        return None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                WECHAT_CODE2SESSION_URL,
                params={
                    "appid": settings.WECHAT_APP_ID,
                    "secret": settings.WECHAT_APP_SECRET,
                    "js_code": code,
                    "grant_type": "authorization_code",
                }
            )
            data = resp.json()

        if "errcode" in data and data["errcode"] != 0:
            logger.error(f"微信 code2session 失败: {data}")
            return None

        return {
            "openid": data.get("openid"),
            "session_key": data.get("session_key"),
            "unionid": data.get("unionid"),
        }
    except Exception as e:
        logger.error(f"调用微信 API 异常: {e}")
        return None


async def get_wechat_access_token() -> Optional[str]:
    """获取微信 access_token"""
    if not settings.WECHAT_APP_ID or not settings.WECHAT_APP_SECRET:
        return None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                WECHAT_ACCESS_TOKEN_URL,
                params={
                    "grant_type": "client_credential",
                    "appid": settings.WECHAT_APP_ID,
                    "secret": settings.WECHAT_APP_SECRET,
                }
            )
            data = resp.json()

        if "access_token" in data:
            return data["access_token"]
        logger.error(f"获取微信 access_token 失败: {data}")
        return None
    except Exception as e:
        logger.error(f"获取微信 access_token 异常: {e}")
        return None


async def send_wechat_subscribe_message(
    openid: str,
    template_id: str,
    data: dict,
    page: Optional[str] = None,
) -> bool:
    """发送微信订阅消息"""
    access_token = await get_wechat_access_token()
    if not access_token:
        logger.warning("无法获取 access_token，跳过微信推送")
        return False

    payload = {
        "touser": openid,
        "template_id": template_id,
        "data": data,
    }
    if page:
        payload["page"] = page

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{WECHAT_SEND_MSG_URL}?access_token={access_token}",
                json=payload,
            )
            result = resp.json()

        if result.get("errcode") == 0:
            logger.info(f"微信消息推送成功: openid={openid}")
            return True
        else:
            logger.warning(f"微信消息推送失败: {result}")
            return False
    except Exception as e:
        logger.error(f"微信消息推送异常: {e}")
        return False
