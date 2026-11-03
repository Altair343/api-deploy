from app.core.config import get_settings
from app.services.email.base import EmailSender
from app.services.email.console import ConsoleEmailSender

def get_email_sender() -> EmailSender:
    settings = get_settings()

    if settings.APP_ENV != "development":
        raise RuntimeError(
            "Console email sender is restricted to development"
        )

    return ConsoleEmailSender()
