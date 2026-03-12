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


class PaymentRequiredError(AppError):
    def __init__(
        self,
        message: str = "Payment is required before this request can be processed.",
        pricing_id: str | None = None,
        payment_mode: str | None = None,
        chain: str | None = None,
        token: str | None = None,
        receiver_wallet: str | None = None,
        payment_format: str | None = None,
        reason: str | None = None,
    ):
        super().__init__(code="PAYMENT_REQUIRED", message=message, status_code=402)
        self.pricing_id = pricing_id
        self.payment_mode = payment_mode
        self.chain = chain
        self.token = token
        self.receiver_wallet = receiver_wallet
        self.payment_format = payment_format
        self.reason = reason or "payment_required"
