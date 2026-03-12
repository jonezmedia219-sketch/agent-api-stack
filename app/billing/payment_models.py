from pydantic import BaseModel, Field


class PaymentRequirement(BaseModel):
    pricing_id: str
    payment_required: bool = False
    payment_mode: str = "free"
    verifier: str = "stub"
    chain: str | None = None
    token: str | None = None
    receiver_wallet: str | None = None


class PaymentContext(BaseModel):
    endpoint: str
    pricing_id: str
    request_id: str
    path: str
    method: str
    headers: dict[str, str] = Field(default_factory=dict)
    usage_context: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    requirement: PaymentRequirement


class PaymentDecision(BaseModel):
    allowed: bool
    shadow_mode: bool = True
    payment_required: bool = False
    reason: str
    pricing_id: str
    payment_mode: str = "free"
    chain: str | None = None
    token: str | None = None
    receiver_wallet: str | None = None
    payer: str | None = None
    verifier: str | None = None
