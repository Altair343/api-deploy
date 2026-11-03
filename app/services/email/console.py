import logging
logger = logging.getLogger(__name__)

class ConsoleEmailSender:
    """
    DEVELOPMENT ONLY.
    Simulates email delivery by printing the email content.
    TODO:
        Replace with a real email provider for production.
        Never log password reset tokens in production.
    """
    async def send_password_reset(
        self,
        recipient: str,
        reset_url: str,
        expires_minutes: int,
    ) -> None:
        logger.warning(
            "\n"
            "========================================\n"
            "SIMULATED PASSWORD RESET EMAIL\n"
            "========================================\n"
            "To: %s\n"
            "Subject: Reset your password\n\n"
            "We received a request to reset your password.\n\n"
            "Open this link:\n"
            "%s\n\n"
            "This link expires in %s minutes.\n\n"
            "If you did not request this change, ignore this email.\n"
            "========================================",
            recipient,
            reset_url,
            expires_minutes,
        )
