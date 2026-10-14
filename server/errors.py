"""Errors that carry an HTTP status and a message a person can act on."""


class ApiError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def bad_request(message): return ApiError(400, message)
def unauthorized(message="Please sign in to do that."): return ApiError(401, message)
def forbidden(message): return ApiError(403, message)
def not_found(message): return ApiError(404, message)
