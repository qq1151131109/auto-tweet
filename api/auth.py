"""
API Key 鉴权
简单版本：从配置文件读取预定义的API keys
生产环境建议使用数据库管理
"""
from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import settings
from typing import Optional

# Bearer token认证
security = HTTPBearer()


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    """
    验证API Key

    Args:
        credentials: HTTP Bearer认证凭据

    Returns:
        API key（验证成功）

    Raises:
        HTTPException: 认证失败
    """
    api_key = credentials.credentials

    # 检查API key是否有效
    if api_key not in settings.valid_api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return api_key


async def verify_api_key_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[str]:
    """
    可选的API Key验证（用于公开端点）

    Args:
        credentials: HTTP Bearer认证凭据（可选）

    Returns:
        API key或None
    """
    if credentials is None:
        return None

    api_key = credentials.credentials

    if api_key in settings.valid_api_keys:
        return api_key

    return None


def get_user_id_from_api_key(api_key: str) -> str:
    """
    从API Key获取用户ID
    简单版本：直接使用API key的hash作为user_id
    生产环境应该查询数据库

    Args:
        api_key: API密钥

    Returns:
        用户ID
    """
    import hashlib
    return hashlib.md5(api_key.encode()).hexdigest()[:16]


# 依赖注入函数
async def get_current_user_id(api_key: str = Security(verify_api_key)) -> str:
    """
    获取当前用户ID（用于依赖注入）

    Args:
        api_key: 已验证的API key

    Returns:
        用户ID
    """
    return get_user_id_from_api_key(api_key)
