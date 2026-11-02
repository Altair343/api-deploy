
class ApplicationError(Exception):
    pass


class UserAlreadyExistsError(ApplicationError):
    pass


class UserNotFoundError(ApplicationError):
    pass
