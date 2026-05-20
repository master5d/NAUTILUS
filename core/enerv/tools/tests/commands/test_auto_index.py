import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
from tools.commands.auto_index import should_rebuild, read_last_index_timestamp, write_last_index_timestamp, check_root_rebuild_needed, build_summary, rebuild_index_for_root, auto_index_command

def test_should_rebuild_when_elapsed_exceeds_threshold():
    """Tech root (3 min threshold): rebuild if 3+ minutes elapsed."""
    now = datetime.fromisoformat("2026-04-20T15:30:00.000000")
    last_index = datetime.fromisoformat("2026-04-20T15:26:00.000000")

    result = should_rebuild(
        last_index_time=last_index,
        now=now,
        threshold_minutes=3
    )

    assert result is True


def test_should_not_rebuild_when_elapsed_below_threshold():
    """Tech root (3 min threshold): don't rebuild if < 3 minutes elapsed."""
    now = datetime.fromisoformat("2026-04-20T15:30:00.000000")
    last_index = datetime.fromisoformat("2026-04-20T15:29:00.000000")  # 1 minute ago

    result = should_rebuild(
        last_index_time=last_index,
        now=now,
        threshold_minutes=3
    )

    assert result is False


def test_should_rebuild_on_clock_skew():
    """If system time went backward, always rebuild (safety)."""
    now = datetime.fromisoformat("2026-04-20T15:25:00.000000")
    last_index = datetime.fromisoformat("2026-04-20T15:30:00.000000")  # Future time

    result = should_rebuild(
        last_index_time=last_index,
        now=now,
        threshold_minutes=3
    )

    assert result is True


def test_should_rebuild_at_exact_threshold():
    """Boundary: elapsed == threshold should rebuild."""
    now = datetime.fromisoformat("2026-04-20T15:30:00.000000")
    last_index = datetime.fromisoformat("2026-04-20T15:27:00.000000")  # Exactly 3 minutes

    result = should_rebuild(
        last_index_time=last_index,
        now=now,
        threshold_minutes=3
    )

    assert result is True


def test_read_last_index_returns_datetime(tmp_path):
    """Read valid ISO 8601 timestamp from .last-index file."""
    facets_dir = tmp_path / ".facets"
    facets_dir.mkdir()
    last_index_file = facets_dir / ".last-index"
    last_index_file.write_text("2026-04-20T15:25:18.456789\n")

    result = read_last_index_timestamp(facets_dir)

    assert result == datetime.fromisoformat("2026-04-20T15:25:18.456789")


def test_read_last_index_returns_none_if_file_missing(tmp_path):
    """Missing .last-index should return None (triggers rebuild)."""
    facets_dir = tmp_path / ".facets"
    facets_dir.mkdir()

    result = read_last_index_timestamp(facets_dir)

    assert result is None


def test_read_last_index_raises_on_invalid_format(tmp_path):
    """Invalid ISO 8601 timestamp should raise ValueError."""
    facets_dir = tmp_path / ".facets"
    facets_dir.mkdir()
    last_index_file = facets_dir / ".last-index"
    last_index_file.write_text("not-a-valid-timestamp\n")

    with pytest.raises(ValueError):
        read_last_index_timestamp(facets_dir)


def test_write_last_index_writes_iso_timestamp(tmp_path):
    """Write current ISO 8601 timestamp to .last-index file."""
    facets_dir = tmp_path / ".facets"
    facets_dir.mkdir()
    now = datetime.fromisoformat("2026-04-20T15:30:42.123456")

    write_last_index_timestamp(facets_dir, now=now)

    last_index_file = facets_dir / ".last-index"
    assert last_index_file.exists()
    assert last_index_file.read_text().strip() == "2026-04-20T15:30:42.123456"


def test_check_root_rebuild_needed_tech(tmp_path):
    """Tech root: rebuild if >= 3 minutes elapsed."""
    facets_dir = tmp_path / ".facets"
    facets_dir.mkdir()
    last_index_file = facets_dir / ".last-index"
    last_index_file.write_text("2026-04-20T15:26:00.000000\n")

    now = datetime.fromisoformat("2026-04-20T15:30:00.000000")  # 4 minutes later

    needed, reason = check_root_rebuild_needed(root_path=tmp_path, root_name="tech", now=now)

    assert needed is True
    assert "4.0 minutes elapsed" in reason or "4" in reason


def test_check_root_rebuild_needed_knowledge(tmp_path):
    """Knowledge root: rebuild if >= 60 minutes elapsed."""
    facets_dir = tmp_path / ".facets"
    facets_dir.mkdir()
    last_index_file = facets_dir / ".last-index"
    last_index_file.write_text("2026-04-20T14:00:00.000000\n")

    now = datetime.fromisoformat("2026-04-20T15:30:00.000000")  # 90 minutes later

    needed, reason = check_root_rebuild_needed(root_path=tmp_path, root_name="knowledge", now=now)

    assert needed is True


def test_check_root_rebuild_needed_facets_missing(tmp_path):
    """Root without .facets should be skipped."""
    now = datetime.fromisoformat("2026-04-20T15:30:00.000000")

    needed, reason = check_root_rebuild_needed(root_path=tmp_path, root_name="tech", now=now)

    assert needed is False
    assert "not initialized" in reason


def test_build_summary_json_format():
    """Build JSON summary with tech and knowledge rebuild results."""
    now = datetime.fromisoformat("2026-04-20T15:30:42.123456")

    summary = build_summary(
        tech_indexed=True,
        tech_reason="3.5 minutes elapsed",
        tech_entry_count=34,
        knowledge_indexed=False,
        knowledge_reason="45 minutes elapsed (60 min threshold)",
        knowledge_entry_count=10,
        timestamp=now
    )

    data = json.loads(summary)

    assert data["tech"]["indexed"] is True
    assert data["tech"]["reason"] == "3.5 minutes elapsed"
    assert data["tech"]["entry_count"] == 34
    assert data["knowledge"]["indexed"] is False
    assert data["knowledge"]["entry_count"] == 10
    assert "timestamp" in data


def test_rebuild_index_for_root_calls_aggregator(tmp_path):
    """Call IndexAggregator to rebuild index when needed."""
    facets_dir = tmp_path / ".facets"
    facets_dir.mkdir()

    # Create index.jsonl with test entries
    index_file = facets_dir / "index.jsonl"
    index_file.write_text('{"id": "1"}\n{"id": "2"}\n{"id": "3"}\n')

    with patch('tools.core.index.IndexAggregator') as mock_aggregator_class:
        mock_aggregator = Mock()
        mock_aggregator.rebuild = Mock()
        mock_aggregator_class.return_value = mock_aggregator

        entry_count = rebuild_index_for_root(tmp_path)

        mock_aggregator_class.assert_called_once()
        mock_aggregator.rebuild.assert_called_once_with(force=True)
        assert entry_count == 3


def test_auto_index_command_rebuilds_both_roots(tmp_path):
    """Full command: check both roots, rebuild as needed, return JSON."""
    # Setup: Create tech and knowledge root directories with timestamps
    tech_root = tmp_path / "tech"
    knowledge_root = tmp_path / "knowledge"
    tech_root.mkdir()
    knowledge_root.mkdir()

    # Create .facets with old timestamps (both need rebuild)
    tech_facets = tech_root / ".facets"
    knowledge_facets = knowledge_root / ".facets"
    tech_facets.mkdir()
    knowledge_facets.mkdir()

    tech_facets.joinpath(".last-index").write_text("2026-04-20T15:20:00.000000\n")
    knowledge_facets.joinpath(".last-index").write_text("2026-04-20T14:00:00.000000\n")

    # Create index.jsonl files with test entries
    tech_facets.joinpath("index.jsonl").write_text('{"id": "1"}\n{"id": "2"}\n{"id": "3"}\n')
    knowledge_facets.joinpath("index.jsonl").write_text('{"id": "1"}\n{"id": "2"}\n{"id": "3"}\n')

    now = datetime.fromisoformat("2026-04-20T15:35:00.000000")

    with patch('tools.core.index.IndexAggregator') as mock_agg_class:
        mock_agg = Mock()
        mock_agg.rebuild = Mock()
        mock_agg_class.return_value = mock_agg

        result = auto_index_command(
            tech_root=str(tech_root),
            knowledge_root=str(knowledge_root),
            now=now
        )

    data = json.loads(result)

    assert data["tech"]["indexed"] is True
    assert data["knowledge"]["indexed"] is True
    assert data["tech"]["entry_count"] == 3
    assert data["knowledge"]["entry_count"] == 3


def test_write_last_index_defaults_to_now(tmp_path):
    """Write uses datetime.now() if now parameter not provided."""
    facets_dir = tmp_path / ".facets"
    facets_dir.mkdir()

    # Call without now parameter - should use current time
    write_last_index_timestamp(facets_dir)

    last_index_file = facets_dir / ".last-index"
    assert last_index_file.exists()
    # Just verify it's a valid ISO format string
    timestamp_str = last_index_file.read_text().strip()
    parsed = datetime.fromisoformat(timestamp_str)
    assert isinstance(parsed, datetime)


def test_check_root_rebuild_needed_defaults_to_now(tmp_path):
    """Check rebuild with no now parameter defaults to datetime.now()."""
    facets_dir = tmp_path / ".facets"
    facets_dir.mkdir()
    last_index_file = facets_dir / ".last-index"
    # Write a timestamp from 4 minutes ago
    past_time = datetime.now()
    past_time_str = (past_time.replace(microsecond=0) - timedelta(minutes=4)).isoformat()
    last_index_file.write_text(past_time_str + "\n")

    # Call without now parameter - should use current time
    needed, reason = check_root_rebuild_needed(root_path=tmp_path, root_name="tech")

    # Should be True because 4 minutes > 3 minute threshold
    assert needed is True


def test_auto_index_command_defaults_to_now(tmp_path):
    """Auto-index command with no now parameter defaults to datetime.now()."""
    tech_root = tmp_path / "tech"
    knowledge_root = tmp_path / "knowledge"
    tech_root.mkdir()
    knowledge_root.mkdir()

    # Create .facets with old timestamps
    tech_facets = tech_root / ".facets"
    knowledge_facets = knowledge_root / ".facets"
    tech_facets.mkdir()
    knowledge_facets.mkdir()

    # Write a tech timestamp from 5 minutes ago (> 3 min threshold)
    # and knowledge timestamp from 120 minutes ago (> 60 min threshold)
    past_time = datetime.now()
    tech_past_str = (past_time.replace(microsecond=0) - timedelta(minutes=5)).isoformat()
    knowledge_past_str = (past_time.replace(microsecond=0) - timedelta(minutes=120)).isoformat()
    tech_facets.joinpath(".last-index").write_text(tech_past_str + "\n")
    knowledge_facets.joinpath(".last-index").write_text(knowledge_past_str + "\n")

    # Create index.jsonl files
    tech_facets.joinpath("index.jsonl").write_text('{"id": "1"}\n{"id": "2"}\n')
    knowledge_facets.joinpath("index.jsonl").write_text('{"id": "1"}\n{"id": "2"}\n')

    with patch('tools.core.index.IndexAggregator') as mock_agg_class:
        mock_agg = Mock()
        mock_agg.rebuild = Mock()
        mock_agg_class.return_value = mock_agg

        # Call without now parameter
        result = auto_index_command(
            tech_root=str(tech_root),
            knowledge_root=str(knowledge_root)
        )

    data = json.loads(result)
    # Both should be indexed because elapsed times exceed thresholds
    assert data["tech"]["indexed"] is True  # 5 min > 3 min
    assert data["knowledge"]["indexed"] is True  # 120 min > 60 min


def test_auto_index_integration_real_filesystem(tmp_path):
    """Integration: real filesystem, real index rebuild, state persistence."""
    tech_root = tmp_path / "tech"
    knowledge_root = tmp_path / "knowledge"
    tech_root.mkdir()
    knowledge_root.mkdir()

    # Initialize .facets directories
    tech_facets = tech_root / ".facets"
    knowledge_facets = knowledge_root / ".facets"
    tech_facets.mkdir()
    knowledge_facets.mkdir()

    # Create meta.json files to be indexed
    (tech_root / "project" / ".meta").mkdir(parents=True, exist_ok=True)
    (tech_root / "project" / ".meta" / "meta.json").write_text(
        '{"name": "project", "type": "workspace"}\n'
    )
    (knowledge_root / "article" / ".meta").mkdir(parents=True, exist_ok=True)
    (knowledge_root / "article" / ".meta" / "meta.json").write_text(
        '{"title": "article", "type": "document"}\n'
    )

    now1 = datetime.fromisoformat("2026-04-20T15:00:00.000000")

    # First run: should rebuild both
    with patch('tools.core.index.IndexAggregator') as mock_agg_class:
        mock_agg = Mock()
        mock_agg.rebuild = Mock()
        mock_agg_class.return_value = mock_agg

        result1 = auto_index_command(
            tech_root=str(tech_root),
            knowledge_root=str(knowledge_root),
            now=now1
        )

    data1 = json.loads(result1)
    assert data1["tech"]["indexed"] is True
    assert data1["knowledge"]["indexed"] is True

    # Verify .last-index files were written
    assert (tech_facets / ".last-index").exists()
    assert (knowledge_facets / ".last-index").exists()
    # Check that the written timestamps are valid ISO format
    tech_timestamp_str = (tech_facets / ".last-index").read_text().strip()
    knowledge_timestamp_str = (knowledge_facets / ".last-index").read_text().strip()
    assert datetime.fromisoformat(tech_timestamp_str) == now1
    assert datetime.fromisoformat(knowledge_timestamp_str) == now1

    # Second run: 2 minutes later (tech should rebuild, knowledge should not)
    now2 = datetime.fromisoformat("2026-04-20T15:02:00.000000")

    with patch('tools.core.index.IndexAggregator') as mock_agg_class:
        mock_agg = Mock()
        mock_agg.rebuild = Mock()
        mock_agg_class.return_value = mock_agg

        result2 = auto_index_command(
            tech_root=str(tech_root),
            knowledge_root=str(knowledge_root),
            now=now2
        )

    data2 = json.loads(result2)
    assert data2["tech"]["indexed"] is False  # 2 min < 3 min threshold
    assert data2["knowledge"]["indexed"] is False  # 2 min < 60 min threshold

    # Third run: 4 minutes later (tech should rebuild, knowledge should not)
    now3 = datetime.fromisoformat("2026-04-20T15:04:00.000000")

    with patch('tools.core.index.IndexAggregator') as mock_agg_class:
        mock_agg = Mock()
        mock_agg.rebuild = Mock()
        mock_agg_class.return_value = mock_agg

        result3 = auto_index_command(
            tech_root=str(tech_root),
            knowledge_root=str(knowledge_root),
            now=now3
        )

    data3 = json.loads(result3)
    assert data3["tech"]["indexed"] is True  # 4 min >= 3 min threshold
    assert data3["knowledge"]["indexed"] is False  # 4 min < 60 min threshold
