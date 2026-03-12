from abc import ABC, abstractmethod

from app.billing.payment_models import PaymentContext, PaymentDecision


class PaymentVerifier(ABC):
    name: str

    @abstractmethod
    async def verify(self, context: PaymentContext, hard_enforcement: bool, shadow_mode: bool) -> PaymentDecision:
        raise NotImplementedError
