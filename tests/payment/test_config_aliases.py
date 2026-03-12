from app.config import Settings


def test_payment_receiver_walet_alias_is_accepted():
    settings = Settings(PAYMENT_RECEIVER_WALET="0x1111111111111111111111111111111111111111")
    assert settings.payment_receiver_wallet == "0x1111111111111111111111111111111111111111"
