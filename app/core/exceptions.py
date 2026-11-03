class ApplicationError(Exception):
    pass

class UserAlreadyExistsError(ApplicationError):
    pass

class UserNotFoundError(ApplicationError):
    pass

class InvalidCredentialsError(ApplicationError):
    pass

class InvalidAccessTokenError(Exception):
    pass

class InvalidRefreshTokenError(Exception):
    pass

class InvalidResetTokenError(Exception):
    pass

class RateLimitExceeded(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__("Rate limit exceeded")