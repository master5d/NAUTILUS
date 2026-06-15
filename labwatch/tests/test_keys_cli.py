import json

import keys
import keys_cli


def _read(p):
    return json.loads(p.read_text(encoding="utf-8"))


def test_gen_creates_active_key_and_no_material_in_stdout(tmp_path, capsys):
    krp = tmp_path / "kr.json"
    rc = keys_cli.main(["gen", "--host", "m4", "--keyring", str(krp)])
    assert rc == 0
    kr = _read(krp)
    kid = keys.active_key_id(kr, "m4")
    assert kid.startswith("m4-")
    mat = keys.material(kr, "m4", kid)
    assert len(mat) == 32
    out = capsys.readouterr().out
    # fingerprint printed, raw material never printed
    import base64
    assert base64.urlsafe_b64encode(mat).decode().rstrip("=") not in out
    assert kid in out


def test_rotate_adds_new_active_keeps_old_then_revoke(tmp_path):
    krp = tmp_path / "kr.json"
    keys_cli.main(["gen", "--host", "m4", "--keyring", str(krp)])
    first = keys.active_key_id(_read(krp), "m4")
    keys_cli.main(["rotate", "--host", "m4", "--keyring", str(krp)])
    kr = _read(krp)
    second = keys.active_key_id(kr, "m4")
    assert second != first
    assert {first, second} <= set(kr["hosts"]["m4"]["keys"])     # both retained
    assert dict(keys.acceptable(kr, "m4")).keys() == {first, second}  # overlap window

    keys_cli.main(["revoke", "--host", "m4", "--key-id", first, "--keyring", str(krp)])
    kr = _read(krp)
    assert set(dict(keys.acceptable(kr, "m4"))) == {second}       # old revoked


def test_export_then_import_roundtrip(tmp_path):
    src = tmp_path / "m4_keyring.json"
    keys_cli.main(["gen", "--host", "surface", "--keyring", str(src)])
    transfer = tmp_path / "surface_key.json"
    rc = keys_cli.main(["export-host", "--host", "surface",
                        "--out", str(transfer), "--keyring", str(src)])
    assert rc == 0
    assert transfer.exists()

    dst = tmp_path / "surface_keyring.json"
    rc = keys_cli.main(["import-host", "--in", str(transfer), "--keyring", str(dst)])
    assert rc == 0

    src_kr = _read(src)
    dst_kr = _read(dst)
    assert dict(keys.acceptable(src_kr, "surface")) == dict(keys.acceptable(dst_kr, "surface"))


def test_export_unknown_host_returns_1(tmp_path):
    src = tmp_path / "kr.json"
    keys_cli.main(["gen", "--host", "m4", "--keyring", str(src)])
    rc = keys_cli.main(["export-host", "--host", "surface",
                        "--out", str(tmp_path / "x.json"), "--keyring", str(src)])
    assert rc == 1
