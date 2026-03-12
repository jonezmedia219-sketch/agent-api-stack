PRICING = {
    "structured_web.extract": {"pricing_id": "structured_web.extract"},
    "structured_web.extract_html": {"pricing_id": "structured_web.extract_html"},
    "lead_extract.url": {"pricing_id": "lead_extract.url"},
    "lead_extract.html": {"pricing_id": "lead_extract.html"},
    "search.query": {"pricing_id": "search.query"},
}


def get_pricing_id(endpoint: str) -> str:
    config = PRICING.get(endpoint)
    if not config:
        raise KeyError(f"No pricing config found for endpoint: {endpoint}")
    return config["pricing_id"]
