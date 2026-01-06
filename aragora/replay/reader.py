import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

from .schema import ReplayEvent, ReplayMeta

logger = logging.getLogger(__name__)


class ReplayReader:
    """Loads and reads replay data."""

    def __init__(self, session_dir: str):
        self.session_dir = Path(session_dir)
        self.meta_path = self.session_dir / "meta.json"
        self.events_path = self.session_dir / "events.jsonl"
        self.meta: Optional[ReplayMeta] = None
        self._load_error: Optional[str] = None

        try:
            with open(self.meta_path, "r", encoding="utf-8") as f:
                self.meta = ReplayMeta.from_json(f.read())
        except FileNotFoundError:
            self._load_error = f"Replay metadata not found: {self.meta_path}"
            logger.warning(self._load_error)
        except json.JSONDecodeError as e:
            self._load_error = f"Corrupted replay metadata: {e.msg} at pos {e.pos}"
            logger.warning(self._load_error)
        except Exception as e:
            self._load_error = f"Failed to load replay: {type(e).__name__}: {e}"
            logger.warning(self._load_error)

    def iter_events(self) -> Iterator[ReplayEvent]:
        if not self.events_path.exists():
            return
        try:
            with open(self.events_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        yield ReplayEvent.from_jsonl(line)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Skipping corrupted event at line {line_num}: {e.msg}")
                        continue
        except Exception as e:
            logger.error(f"Failed to read events file: {type(e).__name__}: {e}")

    def to_bundle(self) -> Dict[str, Any]:
        if self._load_error:
            return {"error": self._load_error, "meta": None, "events": []}
        events = [asdict(e) for e in self.iter_events()]
        return {"meta": asdict(self.meta) if self.meta else None, "events": events}
