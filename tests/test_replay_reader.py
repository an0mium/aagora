import pytest
from aragora.replay.reader import ReplayReader

def test_reader_bundle(tmp_path):
    # Assume files exist from recorder test
    reader = ReplayReader(str(tmp_path / "test"))
    bundle = reader.to_bundle()
    assert "meta" in bundle
    assert "events" in bundle