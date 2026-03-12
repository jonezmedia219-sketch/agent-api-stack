class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class FetchError(AppError):
    def __init__(self, message: str = "Unable to fetch URL."):
        super().__init__(code="FETCH_ERROR", message=message, status_code=502)


class ValidationError(AppError):
    def __init__(self, message: str = "Invalid request."):
        super().__init__(code="VALIDATION_ERROR", message=message, status_code=422)
