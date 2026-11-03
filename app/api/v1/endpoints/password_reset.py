from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.dependencies import SessionDep
from app.schemas.password_reset import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.services.email.base import EmailSender
from app.services.email.factory import get_email_sender
from app.services.password_reset import (
    InvalidResetTokenError,
    PasswordResetService,
)

router = APIRouter()

EmailSenderDep = Annotated[
    EmailSender,
    Depends(get_email_sender),
]

@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password( data: ForgotPasswordRequest, session: SessionDep,
    email_sender: EmailSenderDep):

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
    data: ResetPasswordRequest, session: SessionDep,
    email_sender: EmailSenderDep):

    service = PasswordResetService(
        session=session,
        email_sender=email_sender,
    )

    try:
        await service.reset_password(
            token=data.token,
            new_password=data.new_password,
        )
    except InvalidResetTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    return {
        "message": "Password updated successfully"
    }
