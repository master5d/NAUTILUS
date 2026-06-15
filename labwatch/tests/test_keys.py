import base64
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


def _b64(raw):
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def test_keyring_material_and_acceptable(tmp_path):
    import json
    kr = {
        "hosts": {
            "m4": {
                "active": "m4-2",
                "keys": {
                    "m4-1": {"material": _b64(b"\xaa" * 32), "created": "t", "revoked": True},
                    "m4-2": {"material": _b64(b"\xbb" * 32), "created": "t", "revoked": False},
                },
            }
        }
    }
    p = tmp_path / "kr.json"
    p.write_text(json.dumps(kr), encoding="utf-8")

    loaded = keys.load_keyring(str(p))
    assert keys.active_key_id(loaded, "m4") == "m4-2"
    assert keys.material(loaded, "m4", "m4-2") == b"\xbb" * 32

    acc = dict(keys.acceptable(loaded, "m4"))
    assert set(acc) == {"m4-2"}          # revoked m4-1 excluded
    assert acc["m4-2"] == b"\xbb" * 32


def test_load_keyring_missing_file_returns_empty():
    assert keys.load_keyring("/no/such/keyring.json") == {"hosts": {}}
