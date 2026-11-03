from typing import Protocol

class EmailSender(Protocol):
    async def send_password_reset(
        self,
        recipient: str,
        reset_url: str,
        expires_minutes: int,
    ) -> None:
        """Send a password reset email."""
        ...
