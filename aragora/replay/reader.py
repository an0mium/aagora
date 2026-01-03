from dataclasses import asdict
from pathlib import Path
from typing import Iterator, Dict, Any
import json

from .schema import ReplayEvent, ReplayMeta

class ReplayReader:
    """Loads and reads replay data."""
    
    def __init__(self, session_dir: str):
        self.session_dir = Path(session_dir)
        self.meta_path = self.session_dir / "meta.json"
        self.events_path = self.session_dir / "events.jsonl"
        
        with open(self.meta_path, 'r', encoding='utf-8') as f:
            self.meta = ReplayMeta.from_json(f.read())
    
    def iter_events(self) -> Iterator[ReplayEvent]:
        with open(self.events_path, 'r', encoding='utf-8') as f:
            for line in f:
                yield ReplayEvent.from_jsonl(line)
    
    def to_bundle(self) -> Dict[str, Any]:
        events = [asdict(e) for e in self.iter_events()]
        return {
            "meta": asdict(self.meta),
            "events": events
        }