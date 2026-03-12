from pydantic import BaseModel, Field


class PaymentRequirement(BaseModel):
    pricing_id: str
    payment_required: bool = False
    payment_mode: str = "free"
    verifier: str = "stub"
    chain: str | None = None
    token: str | None = None
    receiver_wallet: str | None = None
    amount: str = "0"


class RequestBinding(BaseModel):
    method: str
    path: str


class OnchainRequestBinding(BaseModel):
    method: str
    path: str
    body_sha256: str


class X402PaymentProof(BaseModel):
    version: str
    chain: str
    token: str
    pricing_id: str
    payment_mode: str
    receiver_wallet: str
    payer_wallet: str
    amount: str
    currency_decimals: int = 6
    request_binding: RequestBinding
    timestamp: int
    nonce: str
    tx_hash: str | None = None
    signature: str


class BaseUSDCOnchainProof(BaseModel):
    version: str
    chain_id: int
    pricing_id: str
    payment_mode: str
    receiver_wallet: str
    token_contract: str
    amount: str
    currency_decimals: int = 6
    request_binding: OnchainRequestBinding
    quote_id: str
    nonce: str
    timestamp: int
    payer_wallet: str
    tx_hash: str
    wallet_signature: str


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
    proof_format: str | None = None
    amount: str | None = None
    nonce: str | None = None
    timestamp: int | None = None
    tx_hash: str | None = None
    quote_id: str | None = None
