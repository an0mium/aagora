-- Aragora Memory Database Schema
-- Consolidated from: agent_memories.db, continuum.db, consensus_memory.db,
--                    agora_memory.db, semantic_patterns.db, suggestion_feedback.db
-- Version: 1.0.0
-- Last Updated: 2026-01-07

-- Schema version tracking
CREATE TABLE IF NOT EXISTS _schema_versions (
    module TEXT PRIMARY KEY,
    version INTEGER NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- CONTINUUM MEMORY (Multi-tier memory system)
-- Source: continuum.db
-- =============================================================================

CREATE TABLE IF NOT EXISTS continuum_memory (
    id TEXT PRIMARY KEY,
    tier TEXT NOT NULL DEFAULT 'slow',  -- 'fast', 'medium', 'slow', 'glacial'
    content TEXT NOT NULL,
    importance REAL DEFAULT 0.5,
    surprise_score REAL DEFAULT 0.0,
    consolidation_score REAL DEFAULT 0.0,
    update_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    semantic_centroid BLOB,  -- Embedding vector
    last_promotion_at TEXT,
    expires_at TEXT,
    metadata TEXT DEFAULT '{}',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tier_transitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_id TEXT NOT NULL,
    from_tier TEXT NOT NULL,
    to_tier TEXT NOT NULL,
    reason TEXT,
    surprise_score REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (memory_id) REFERENCES continuum_memory(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS continuum_memory_archive (
    id TEXT PRIMARY KEY,
    tier TEXT NOT NULL,
    content TEXT NOT NULL,
    importance REAL,
    surprise_score REAL,
    consolidation_score REAL,
    update_count INTEGER,
    success_count INTEGER,
    failure_count INTEGER,
    semantic_centroid BLOB,
    created_at TEXT,
    updated_at TEXT,
    archived_at TEXT DEFAULT CURRENT_TIMESTAMP,
    archive_reason TEXT,
    metadata TEXT
);

CREATE TABLE IF NOT EXISTS meta_learning_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hyperparams TEXT NOT NULL,  -- JSON
    learning_efficiency REAL,
    pattern_retention_rate REAL,
    forgetting_rate REAL,
    cycles_evaluated INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_continuum_tier ON continuum_memory(tier);
CREATE INDEX IF NOT EXISTS idx_continuum_surprise ON continuum_memory(surprise_score DESC);
CREATE INDEX IF NOT EXISTS idx_continuum_importance ON continuum_memory(importance DESC);
CREATE INDEX IF NOT EXISTS idx_continuum_expires ON continuum_memory(expires_at);
CREATE INDEX IF NOT EXISTS idx_archive_tier ON continuum_memory_archive(tier);
CREATE INDEX IF NOT EXISTS idx_archive_archived_at ON continuum_memory_archive(archived_at);
CREATE INDEX IF NOT EXISTS idx_tier_transitions_memory ON tier_transitions(memory_id);

-- =============================================================================
-- AGENT MEMORIES (Short-term and working memory)
-- Source: agent_memories.db
-- =============================================================================

CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT NOT NULL,
    memory_type TEXT NOT NULL,  -- 'debate', 'reflection', 'learning', 'interaction'
    content TEXT NOT NULL,
    context TEXT,  -- JSON context
    importance REAL DEFAULT 0.5,
    decay_rate REAL DEFAULT 0.1,
    embedding BLOB,
    debate_id TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    expires_at TEXT
);

CREATE TABLE IF NOT EXISTS reflection_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT NOT NULL,
    reflection_type TEXT NOT NULL,
    scheduled_for TEXT NOT NULL,
    completed_at TEXT,
    memory_ids TEXT,  -- JSON array of memory IDs to reflect on
    result TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_memories_agent ON memories(agent_name);
CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_memories_debate ON memories(debate_id);
CREATE INDEX IF NOT EXISTS idx_memories_expires ON memories(expires_at);
CREATE INDEX IF NOT EXISTS idx_reflection_agent ON reflection_schedule(agent_name);
CREATE INDEX IF NOT EXISTS idx_reflection_scheduled ON reflection_schedule(scheduled_for);

-- =============================================================================
-- CONSENSUS MEMORY
-- Source: consensus_memory.db
-- =============================================================================

CREATE TABLE IF NOT EXISTS consensus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    position TEXT NOT NULL,
    confidence REAL DEFAULT 0.5,
    supporting_agents TEXT,  -- JSON array
    opposing_agents TEXT,  -- JSON array
    evidence TEXT,  -- JSON array of evidence items
    debate_ids TEXT,  -- JSON array of debate IDs that formed this consensus
    stability_score REAL DEFAULT 0.5,  -- How stable this consensus has been
    last_challenged_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dissent (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    consensus_id INTEGER NOT NULL,
    agent_name TEXT NOT NULL,
    dissent_position TEXT NOT NULL,
    reasoning TEXT,
    strength REAL DEFAULT 0.5,
    resolved INTEGER DEFAULT 0,
    resolved_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (consensus_id) REFERENCES consensus(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_consensus_topic ON consensus(topic);
CREATE INDEX IF NOT EXISTS idx_consensus_confidence ON consensus(confidence DESC);
CREATE INDEX IF NOT EXISTS idx_dissent_consensus ON dissent(consensus_id);
CREATE INDEX IF NOT EXISTS idx_dissent_agent ON dissent(agent_name);

-- =============================================================================
-- CRITIQUE PATTERNS (Learning from critiques)
-- Source: agora_memory.db
-- =============================================================================

CREATE TABLE IF NOT EXISTS critiques (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    debate_id TEXT NOT NULL,
    critic_agent TEXT NOT NULL,
    target_agent TEXT NOT NULL,
    critique_type TEXT,  -- 'logical', 'factual', 'clarity', etc.
    critique_text TEXT NOT NULL,
    accepted INTEGER DEFAULT 0,
    impact_score REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_type TEXT NOT NULL,
    pattern_text TEXT NOT NULL,
    source_type TEXT,  -- 'critique', 'debate', 'consensus'
    source_id TEXT,
    success_rate REAL DEFAULT 0.5,
    usage_count INTEGER DEFAULT 1,
    last_used_at TEXT,
    embedding BLOB,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS patterns_archive (
    id INTEGER PRIMARY KEY,
    pattern_type TEXT NOT NULL,
    pattern_text TEXT NOT NULL,
    source_type TEXT,
    source_id TEXT,
    success_rate REAL,
    usage_count INTEGER,
    archived_at TEXT DEFAULT CURRENT_TIMESTAMP,
    archive_reason TEXT
);

CREATE TABLE IF NOT EXISTS pattern_embeddings (
    pattern_id INTEGER PRIMARY KEY,
    embedding BLOB NOT NULL,
    model_version TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pattern_id) REFERENCES patterns(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS agent_reputation (
    agent_name TEXT PRIMARY KEY,
    critique_accuracy REAL DEFAULT 0.5,
    argument_strength REAL DEFAULT 0.5,
    collaboration_score REAL DEFAULT 0.5,
    influence_score REAL DEFAULT 0.5,
    debates_participated INTEGER DEFAULT 0,
    critiques_given INTEGER DEFAULT 0,
    critiques_accepted INTEGER DEFAULT 0,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_critiques_debate ON critiques(debate_id);
CREATE INDEX IF NOT EXISTS idx_critiques_critic ON critiques(critic_agent);
CREATE INDEX IF NOT EXISTS idx_critiques_target ON critiques(target_agent);
CREATE INDEX IF NOT EXISTS idx_patterns_type ON patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_patterns_success ON patterns(success_rate DESC);

-- =============================================================================
-- SEMANTIC PATTERNS (Embeddings for semantic search)
-- Source: semantic_patterns.db
-- =============================================================================

CREATE TABLE IF NOT EXISTS semantic_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL,  -- 'debate', 'critique', 'pattern', 'memory'
    source_id TEXT NOT NULL,
    content_hash TEXT,  -- Hash of content for deduplication
    embedding BLOB NOT NULL,
    model_version TEXT,
    dimensions INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_type, source_id)
);

CREATE INDEX IF NOT EXISTS idx_semantic_source ON semantic_embeddings(source_type, source_id);

-- =============================================================================
-- USER SUGGESTIONS & FEEDBACK
-- Source: suggestion_feedback.db
-- =============================================================================

CREATE TABLE IF NOT EXISTS suggestion_injections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    debate_id TEXT NOT NULL,
    user_id TEXT,
    suggestion_type TEXT NOT NULL,  -- 'argument', 'question', 'evidence'
    content TEXT NOT NULL,
    target_agent TEXT,
    accepted INTEGER DEFAULT 0,
    impact_score REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contributor_stats (
    user_id TEXT PRIMARY KEY,
    suggestions_total INTEGER DEFAULT 0,
    suggestions_accepted INTEGER DEFAULT 0,
    acceptance_rate REAL DEFAULT 0.0,
    impact_score_sum REAL DEFAULT 0.0,
    last_contribution_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_suggestions_debate ON suggestion_injections(debate_id);
CREATE INDEX IF NOT EXISTS idx_suggestions_user ON suggestion_injections(user_id);

-- =============================================================================
-- DEBATES (Metadata for memory cross-references)
-- Source: agora_memory.db
-- =============================================================================

CREATE TABLE IF NOT EXISTS debates (
    debate_id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    domain TEXT,
    status TEXT DEFAULT 'active',  -- 'active', 'completed', 'archived'
    participants TEXT,  -- JSON array
    rounds_completed INTEGER DEFAULT 0,
    consensus_reached INTEGER DEFAULT 0,
    final_outcome TEXT,
    metadata TEXT DEFAULT '{}',
    started_at TEXT DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_debates_topic ON debates(topic);
CREATE INDEX IF NOT EXISTS idx_debates_domain ON debates(domain);
CREATE INDEX IF NOT EXISTS idx_debates_status ON debates(status);

-- Initialize schema version
INSERT OR REPLACE INTO _schema_versions (module, version)
VALUES ('memory', 1);
