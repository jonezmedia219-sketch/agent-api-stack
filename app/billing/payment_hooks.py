from fastapi import Request

from app.billing.context import RequestUsageContext


async def verify_payment(_request: Request, _context: RequestUsageContext | None = None) -> bool:
    return True
