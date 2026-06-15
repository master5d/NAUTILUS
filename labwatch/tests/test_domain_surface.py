import os
from datetime import datetime

import reporter


def _write(path, content=""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def test_codex_tokens_sums_last_token_count_per_file(tmp_path):
    today = datetime.now().date()
    d = os.path.join(str(tmp_path), ".codex", "sessions",
                     f"{today.year}", f"{today.month:02d}", f"{today.day:02d}")
    _write(os.path.join(d, "rollout-1.jsonl"),
           '{"type":"x"}\n'
           '{"type":"token_count","total_tokens":100}\n'
           '{"type":"token_count","total_tokens":250}\n')
    # only the LAST token_count line counts (cumulative), -> 250
    assert reporter._codex_tokens(str(tmp_path), today) == 250


def test_codex_tokens_missing_dir_returns_zero(tmp_path):
    assert reporter._codex_tokens(str(tmp_path), datetime.now().date()) == 0


def test_gemini_requests_counts_gemini_turns_today(tmp_path):
    today = datetime.now().date()
    f = os.path.join(str(tmp_path), ".gemini", "tmp", "proj", "chats", "session-1.jsonl")
    _write(f, '{"type":"gemini"}\n{"type":"user"}\n{"type":"gemini"}\n')
    assert reporter._gemini_requests(str(tmp_path), today) == 2


def test_agy_runs_counts_today_brain_dirs(tmp_path):
    today = datetime.now().date()
    base = os.path.join(str(tmp_path), ".gemini", "antigravity-cli", "brain")
    os.makedirs(os.path.join(base, "run1"))
    os.makedirs(os.path.join(base, "run2"))
    assert reporter._agy_runs(str(tmp_path), today) == 2


def test_domain_surface_shape(tmp_path):
    d = reporter.domain_surface(home=str(tmp_path), today=datetime.now().date())
    assert "wallets" in d
    w = d["wallets"]
    assert "as_of" in w
    assert set(w["agents"]) == {"codex", "gemini-cli", "antigravity", "claude"}
    assert w["agents"]["antigravity"]["budget"] == 20
    assert w["agents"]["claude"]["used_today"] is None
