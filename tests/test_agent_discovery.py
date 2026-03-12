def test_skill_md_endpoint(client):
    response = client.get("/.well-known/skills/default/skill.md")
    assert response.status_code == 200
    body = response.text
    assert "# agent-api-stack" in body
    assert "https://agent-api-stack.onrender.com/" in body
    assert "https://agent-api-stack.onrender.com/docs" in body
    assert "https://agent-api-stack.onrender.com/pricing" in body
    assert "https://agent-api-stack.onrender.com/payment/schema" in body
    assert "X-Payment-Format: base-usdc-onchain-v1" in body
    assert "X-Payment-Proof: <base64url-encoded-json>" in body
    assert "Never replay a used proof" in body


def test_llms_txt_endpoint(client):
    response = client.get("/llms.txt")
    assert response.status_code == 200
    body = response.text
    assert "# agent-api-stack" in body
    assert "https://agent-api-stack.onrender.com/" in body
    assert "https://agent-api-stack.onrender.com/docs" in body
    assert "https://agent-api-stack.onrender.com/pricing" in body
    assert "https://agent-api-stack.onrender.com/payment/schema" in body
    assert "https://github.com/jonezmedia219-sketch/agent-api-stack/blob/main/docs/integration-payments.md" in body
