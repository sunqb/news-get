import random
import string
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.database import get_db
from app.core.config import get_settings
from app.core.security import create_access_token, get_current_user, decode_access_token
from app.core.session_store import session_store
from app.models.models import User, VerificationCode
from app.schemas.schemas import (
    SendCodeRequest,
    VerifyCodeRequest,
    TokenResponse,
    UserResponse,
    MessageResponse,
)
from app.services.email_service import send_verification_code

router = APIRouter(prefix="/auth", tags=["认证"])
settings = get_settings()


def generate_code(length: int = 6) -> str:
    """生成数字验证码"""
    return "".join(random.choices(string.digits, k=length))


@router.post("/send-code", response_model=MessageResponse)
async def send_code(request: SendCodeRequest, db: AsyncSession = Depends(get_db)):
    """发送验证码到邮箱"""
    # 检查是否有未过期且未使用的验证码
    existing_code = await db.execute(
        select(VerificationCode).where(
            and_(
                VerificationCode.email == request.email,
                VerificationCode.is_used == False,
                VerificationCode.expires_at > datetime.utcnow(),
            )
        )
    )
    existing = existing_code.scalar_one_or_none()

    if existing:
        # 如果最近1分钟内已发送过，不允许重发
        if (datetime.utcnow() - existing.created_at).total_seconds() < 60:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="验证码发送过于频繁，请稍后再试",
            )
        # 将旧验证码标记为已使用
        existing.is_used = True

    # 生成新验证码
    code = generate_code()
    expires_at = datetime.utcnow() + timedelta(minutes=settings.verification_code_expire_minutes)

    verification = VerificationCode(
        email=request.email,
        code=code,
        expires_at=expires_at,
    )
    db.add(verification)
    await db.commit()

    # 发送邮件（在生产环境中应该使用后台任务）
    success = await send_verification_code(request.email, code)
    if not success:
        # 即使邮件发送失败，在开发环境中也返回成功（方便调试）
        if settings.debug:
            print(f"[DEBUG] 验证码: {code}")
            return MessageResponse(message=f"验证码已发送（调试模式: {code}）")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证码发送失败，请稍后再试",
        )

    return MessageResponse(message="验证码已发送到您的邮箱")


@router.post("/verify-code", response_model=TokenResponse)
async def verify_code(request: VerifyCodeRequest, db: AsyncSession = Depends(get_db)):
    """验证验证码并返回token"""
    # 查找验证码
    result = await db.execute(
        select(VerificationCode).where(
            and_(
                VerificationCode.email == request.email,
                VerificationCode.code == request.code,
                VerificationCode.is_used == False,
                VerificationCode.expires_at > datetime.utcnow(),
            )
        )
    )
    verification = result.scalar_one_or_none()

    if not verification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码无效或已过期",
        )

    # 标记验证码为已使用
    verification.is_used = True

    # 查找或创建用户
    user_result = await db.execute(select(User).where(User.email == request.email))
    user = user_result.scalar_one_or_none()

    if not user:
        user = User(email=request.email)
        db.add(user)

    user.last_login = datetime.utcnow()
    await db.commit()

    # 生成token
    access_token = create_access_token(data={"sub": user.email})

    # 存储会话到内存
    expires_at = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    session_store.add_session(access_token, user.email, expires_at)

    return TokenResponse(access_token=access_token)


@router.post("/validate-token", response_model=MessageResponse)
async def validate_token(
    current_user: User = Depends(get_current_user),
):
    """验证token是否有效"""
    return MessageResponse(message="Token有效", success=True)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: User = Depends(get_current_user),
):
    """登出，清除会话"""
    # 注意：由于我们使用的是JWT，实际上无法真正"注销"token
    # 但我们可以从内存中移除会话记录
    return MessageResponse(message="已登出")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user
