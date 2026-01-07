-- Aragora Core Database Schema
-- Consolidated from: debates storage, traces, tournaments, embeddings, positions
-- Version: 1.0.0
-- Last Updated: 2026-01-07

-- Schema version tracking
CREATE TABLE IF NOT EXISTS _schema_versions (
    module TEXT PRIMARY KEY,
    version INTEGER NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- DEBATES (Core debate records)
-- Source: server/storage.py
-- =============================================================================

CREATE TABLE IF NOT EXISTS debates (
    id TEXT PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,
    task TEXT NOT NULL,
    agents TEXT NOT NULL,  -- JSON array
    artifact_json TEXT NOT NULL,
    consensus_reached BOOLEAN,
    confidence REAL,
    view_count INTEGER DEFAULT 0,
    audio_path TEXT,
    audio_generated_at TIMESTAMP,
    audio_duration_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_debates_slug ON debates(slug);
CREATE INDEX IF NOT EXISTS idx_debates_created ON debates(created_at);
CREATE INDEX IF NOT EXISTS idx_debates_consensus ON debates(consensus_reached);

-- =============================================================================
-- DEBATE METADATA (Configuration tracking)
-- Source: runtime/metadata.py
-- =============================================================================

CREATE TABLE IF NOT EXISTS debate_metadata (
    debate_id TEXT PRIMARY KEY,
    config_hash TEXT,
    task_hash TEXT,
    metadata_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (debate_id) REFERENCES debates(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_metadata_config_hash ON debate_metadata(config_hash);
CREATE INDEX IF NOT EXISTS idx_metadata_task_hash ON debate_metadata(task_hash);

-- =============================================================================
-- TRACES (Debate execution traces for replay)
-- Source: debate/traces.py
-- =============================================================================

CREATE TABLE IF NOT EXISTS traces (
    trace_id TEXT PRIMARY KEY,
    debate_id TEXT,
    task TEXT,
    agents TEXT,  -- JSON array
    random_seed INTEGER,
    checksum TEXT,
    trace_json TEXT,  -- Full trace data
    started_at TEXT,
    completed_at TEXT,
    FOREIGN KEY (debate_id) REFERENCES debates(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS trace_events (
    event_id TEXT PRIMARY KEY,
    trace_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    round_num INTEGER,
    agent TEXT,
    content TEXT,  -- JSON event content
    timestamp TEXT,
    FOREIGN KEY (trace_id) REFERENCES traces(trace_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_traces_debate ON traces(debate_id);
CREATE INDEX IF NOT EXISTS idx_trace_events_trace ON trace_events(trace_id);
CREATE INDEX IF NOT EXISTS idx_trace_events_type ON trace_events(event_type);

-- =============================================================================
-- TOURNAMENTS (Tournament system)
-- Source: tournaments/tournament.py
-- =============================================================================

CREATE TABLE IF NOT EXISTS tournaments (
    tournament_id TEXT PRIMARY KEY,
    name TEXT,
    format TEXT,  -- 'round_robin', 'swiss', 'single_elimination', 'free_for_all'
    agents TEXT,  -- JSON array of participating agents
    tasks TEXT,  -- JSON array of task IDs
    standings TEXT,  -- JSON map of agent -> score
    champion TEXT,
    started_at TEXT,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS tournament_matches (
    match_id TEXT PRIMARY KEY,
    tournament_id TEXT NOT NULL,
    round_num INTEGER,
    participants TEXT,  -- JSON array
    task_id TEXT,
    scores TEXT,  -- JSON map of agent -> score
    winner TEXT,
    started_at TEXT,
    completed_at TEXT,
    FOREIGN KEY (tournament_id) REFERENCES tournaments(tournament_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_tournament_matches_tournament ON tournament_matches(tournament_id);
CREATE INDEX IF NOT EXISTS idx_tournament_matches_round ON tournament_matches(round_num);

-- =============================================================================
-- EMBEDDINGS (Vector embedding cache)
-- Source: memory/embeddings.py
-- =============================================================================

CREATE TABLE IF NOT EXISTS embeddings (
    id TEXT PRIMARY KEY,
    text_hash TEXT UNIQUE,
    text TEXT,  -- Truncated to 1000 chars for storage
    embedding BLOB NOT NULL,
    provider TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_embeddings_hash ON embeddings(text_hash);

-- =============================================================================
-- POSITIONS (Agent positions and flips)
-- Source: insights/flip_detector.py, agents/grounded.py
-- =============================================================================

CREATE TABLE IF NOT EXISTS positions (
    id TEXT PRIMARY KEY,
    agent_name TEXT NOT NULL,
    claim TEXT NOT NULL,
    confidence REAL NOT NULL,
    debate_id TEXT NOT NULL,
    round_num INTEGER NOT NULL,
    outcome TEXT DEFAULT 'pending',  -- 'pending', 'correct', 'incorrect', 'unknown'
    reversed INTEGER DEFAULT 0,
    reversal_debate_id TEXT,
    domain TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    resolved_at TEXT
);

CREATE TABLE IF NOT EXISTS detected_flips (
    id TEXT PRIMARY KEY,
    agent_name TEXT NOT NULL,
    original_claim TEXT NOT NULL,
    new_claim TEXT NOT NULL,
    original_confidence REAL,
    new_confidence REAL,
    original_debate_id TEXT,
    new_debate_id TEXT,
    original_position_id TEXT,
    new_position_id TEXT,
    similarity_score REAL,
    flip_type TEXT,  -- 'contradiction', 'retraction', 'refinement', 'strengthening'
    domain TEXT,
    detected_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_positions_agent ON positions(agent_name);
CREATE INDEX IF NOT EXISTS idx_positions_debate ON positions(debate_id);
CREATE INDEX IF NOT EXISTS idx_positions_outcome ON positions(outcome);
CREATE INDEX IF NOT EXISTS idx_flips_agent ON detected_flips(agent_name);
CREATE INDEX IF NOT EXISTS idx_flips_type ON detected_flips(flip_type);

-- Initialize schema version
INSERT OR REPLACE INTO _schema_versions (module, version)
VALUES ('core', 1);
