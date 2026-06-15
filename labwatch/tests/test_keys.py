import keys


def test_bearer_and_signing_keys_are_distinct_and_deterministic():
    master = b"\x01" * 32
    b1 = keys.bearer_token(master)
    b2 = keys.bearer_token(master)
    assert b1 == b2                      # deterministic
    assert keys.signing_key(master) != master
    assert keys.bearer_token(master).encode() != keys.signing_key(master)


def test_sign_then_verify_roundtrip():
    master = b"\x02" * 32
    body = b'{"a":1,"b":2}'
    sig = keys.sign_payload(master, body)
    assert keys.verify_payload(master, body, sig) is True


def test_verify_rejects_tampered_body_and_wrong_key():
    master = b"\x03" * 32
    sig = keys.sign_payload(master, b'{"a":1}')
    assert keys.verify_payload(master, b'{"a":2}', sig) is False
    assert keys.verify_payload(b"\x04" * 32, b'{"a":1}', sig) is False
