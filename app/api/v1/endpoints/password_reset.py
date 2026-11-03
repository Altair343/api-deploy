from typing import Annotated
from fastapi import (APIRouter, Depends, HTTPException, status, Request)
from app.api.dependencies import (SessionDep, PasswordResetRateLimiterDep)
from app.schemas.password_reset import (ForgotPasswordRequest, ResetPasswordRequest)
from app.services.email.base import EmailSender
from app.services.email.factory import get_email_sender
from app.services.password_reset import (InvalidResetTokenError, PasswordResetService)
from redis.exceptions import RedisError
from app.core.rate_limit import (RateLimitExceeded, PasswordResetRateLimiter)

router = APIRouter()

EmailSenderDep = Annotated[
    EmailSender,
    Depends(get_email_sender),
]

@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    data: ForgotPasswordRequest, request: Request,
    session: SessionDep, email_sender: EmailSenderDep,
    limiter: PasswordResetRateLimiterDep):
    await enforce_reset_rate_limit(
        request=request,
        limiter=limiter,
        email=data.email,
    )

    service = PasswordResetService(
        session=session,
        email_sender=email_sender,
    )

    await service.request_reset(data.email)
    return {
        "message": (
            "If the account exists, "
            "a recovery email will be sent"
        )
    }

@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    data: ResetPasswordRequest, request: Request,
    session: SessionDep, email_sender: EmailSenderDep,
    limiter: PasswordResetRateLimiterDep):
    await enforce_reset_rate_limit(
        request=request,
        limiter=limiter,
    )

    service = PasswordResetService(
        session=session,
        email_sender=email_sender,
    )

    try:
        await service.reset_password(
            token=data.token,
            new_password=data.new_password,
        )
    except InvalidResetTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        ) from exc

    return {
        "message": "Password updated successfully"
    }

async def enforce_reset_rate_limit(
    request: Request,
    limiter: PasswordResetRateLimiter,
    email: str | None = None,
) -> None:
    ip_address = (
        request.client.host
        if request.client
        else "unknown"
    )

    try:
        if email is not None:
            await limiter.check_request(
                ip_address=ip_address,
                email=email,
            )
        else:
            await limiter.check_reset(
                ip_address=ip_address,
            )

    except RateLimitExceeded as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests",
            headers={
                "Retry-After": str(exc.retry_after),
            },
        ) from exc

    except RedisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable",
        ) from exc
