from fastapi import APIRouter

router = APIRouter(tags=["root"])


@router.get("/")
async def root_discovery() -> dict:
    return {
        "service": "agent-api-stack",
        "docs": "/docs",
        "pricing": "/pricing",
        "payment_schema": "/payment/schema",
        "integration_guide": "https://github.com/jonezmedia219-sketch/agent-api-stack/blob/main/docs/integration-payments.md",
    }
