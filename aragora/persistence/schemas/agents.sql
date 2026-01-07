-- Aragora Agents Database Schema
-- Consolidated from: agent_personas.db, persona_lab.db, agent_relationships.db,
--                    grounded_positions.db, genesis.db, agent_calibration.db
-- Version: 1.0.0
-- Last Updated: 2026-01-07

-- Schema version tracking
CREATE TABLE IF NOT EXISTS _schema_versions (
    module TEXT PRIMARY KEY,
    version INTEGER NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- PERSONAS (Agent personality definitions)
-- Source: agents/personas.py
-- =============================================================================

CREATE TABLE IF NOT EXISTS personas (
    agent_name TEXT PRIMARY KEY,
    description TEXT,
    traits TEXT,  -- JSON array of trait strings
    expertise TEXT,  -- JSON map of domain -> proficiency
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS performance_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT NOT NULL,
    debate_id TEXT,
    domain TEXT,
    action TEXT,  -- 'argue', 'critique', 'vote', etc.
    success INTEGER,  -- 1 = success, 0 = failure
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_performance_agent ON performance_history(agent_name);
CREATE INDEX IF NOT EXISTS idx_performance_domain ON performance_history(domain);
CREATE INDEX IF NOT EXISTS idx_performance_action ON performance_history(action);

-- =============================================================================
-- AGENT RELATIONSHIPS (Inter-agent dynamics)
-- Source: agents/grounded.py, ranking/elo.py
-- =============================================================================

CREATE TABLE IF NOT EXISTS agent_relationships (
    agent_a TEXT NOT NULL,
    agent_b TEXT NOT NULL,
    debate_count INTEGER DEFAULT 0,
    agreement_count INTEGER DEFAULT 0,
    critique_count_a_to_b INTEGER DEFAULT 0,
    critique_count_b_to_a INTEGER DEFAULT 0,
    critique_accepted_a_to_b INTEGER DEFAULT 0,
    critique_accepted_b_to_a INTEGER DEFAULT 0,
    position_changes_a_after_b INTEGER DEFAULT 0,
    position_changes_b_after_a INTEGER DEFAULT 0,
    a_wins_over_b INTEGER DEFAULT 0,
    b_wins_over_a INTEGER DEFAULT 0,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (agent_a, agent_b),
    CHECK (agent_a < agent_b)  -- Canonical ordering
);

CREATE INDEX IF NOT EXISTS idx_relationships_a ON agent_relationships(agent_a);
CREATE INDEX IF NOT EXISTS idx_relationships_b ON agent_relationships(agent_b);

-- =============================================================================
-- POSITION HISTORY & TRUTH GROUNDING
-- Source: agents/truth_grounding.py
-- =============================================================================

CREATE TABLE IF NOT EXISTS position_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    debate_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    position_type TEXT NOT NULL,  -- 'initial', 'revised', 'final'
    position_text TEXT NOT NULL,
    round_num INTEGER DEFAULT 0,
    confidence REAL DEFAULT 0.5,
    was_winning_position INTEGER DEFAULT NULL,
    verified_correct INTEGER DEFAULT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(debate_id, agent_name, position_type, round_num)
);

CREATE TABLE IF NOT EXISTS debate_outcomes (
    debate_id TEXT PRIMARY KEY,
    winning_agent TEXT,
    winning_position TEXT,
    consensus_confidence REAL,
    verified_at TEXT DEFAULT NULL,
    verification_result INTEGER DEFAULT NULL,  -- 1 = correct, 0 = incorrect
    verification_source TEXT DEFAULT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_position_history_agent ON position_history(agent_name);
CREATE INDEX IF NOT EXISTS idx_position_history_debate ON position_history(debate_id);

-- =============================================================================
-- PERSONA LABORATORY (A/B testing & trait experiments)
-- Source: agents/laboratory.py
-- =============================================================================

CREATE TABLE IF NOT EXISTS experiments (
    experiment_id TEXT PRIMARY KEY,
    agent_name TEXT NOT NULL,
    control_persona TEXT NOT NULL,  -- JSON persona state
    variant_persona TEXT NOT NULL,  -- JSON persona state
    hypothesis TEXT,
    status TEXT DEFAULT 'running',  -- 'running', 'completed', 'cancelled'
    control_successes INTEGER DEFAULT 0,
    control_trials INTEGER DEFAULT 0,
    variant_successes INTEGER DEFAULT 0,
    variant_trials INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS emergent_traits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trait_name TEXT NOT NULL,
    source_agents TEXT NOT NULL,  -- JSON array of contributing agents
    supporting_evidence TEXT,  -- JSON array
    confidence REAL DEFAULT 0.5,
    first_detected TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trait_transfers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_agent TEXT NOT NULL,
    to_agent TEXT NOT NULL,
    trait TEXT NOT NULL,
    expertise_domain TEXT,
    success_rate_before REAL,
    success_rate_after REAL,
    transferred_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_evolution_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT NOT NULL,
    mutation_type TEXT NOT NULL,  -- 'trait_add', 'trait_remove', 'expertise_change'
    before_state TEXT NOT NULL,  -- JSON state
    after_state TEXT NOT NULL,  -- JSON state
    reason TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_experiments_agent ON experiments(agent_name);
CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments(status);
CREATE INDEX IF NOT EXISTS idx_trait_transfers_from ON trait_transfers(from_agent);
CREATE INDEX IF NOT EXISTS idx_trait_transfers_to ON trait_transfers(to_agent);
CREATE INDEX IF NOT EXISTS idx_evolution_agent ON agent_evolution_history(agent_name);

-- =============================================================================
-- CALIBRATION PREDICTIONS
-- Source: agents/calibration.py
-- =============================================================================

CREATE TABLE IF NOT EXISTS calibration_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent TEXT NOT NULL,
    confidence REAL NOT NULL,
    correct INTEGER NOT NULL,  -- 1 = correct, 0 = incorrect
    domain TEXT DEFAULT 'general',
    debate_id TEXT,
    position_id TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cal_pred_agent ON calibration_predictions(agent);
CREATE INDEX IF NOT EXISTS idx_cal_pred_domain ON calibration_predictions(domain);
CREATE INDEX IF NOT EXISTS idx_cal_pred_confidence ON calibration_predictions(confidence);

-- =============================================================================
-- GENESIS SYSTEM (Agent breeding and evolution)
-- Source: genesis/genome.py, genesis/breeding.py, genesis/ledger.py
-- =============================================================================

CREATE TABLE IF NOT EXISTS genomes (
    genome_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    traits TEXT,  -- JSON array
    expertise TEXT,  -- JSON map of domain -> proficiency
    model_preference TEXT,
    parent_genomes TEXT,  -- JSON array of parent genome IDs
    generation INTEGER DEFAULT 0,
    fitness_score REAL DEFAULT 0.5,
    birth_debate_id TEXT,
    consensus_contributions INTEGER DEFAULT 0,
    critiques_accepted INTEGER DEFAULT 0,
    predictions_correct INTEGER DEFAULT 0,
    debates_participated INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS populations (
    population_id TEXT PRIMARY KEY,
    genome_ids TEXT,  -- JSON array of genome IDs
    generation INTEGER DEFAULT 0,
    debate_history TEXT,  -- JSON array of debate IDs
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS active_population (
    id INTEGER PRIMARY KEY CHECK (id = 1),  -- Singleton row
    population_id TEXT,
    FOREIGN KEY (population_id) REFERENCES populations(population_id)
);

CREATE TABLE IF NOT EXISTS genesis_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,  -- 'birth', 'mutation', 'crossover', 'selection', 'extinction'
    timestamp TEXT NOT NULL,
    parent_event_id TEXT,
    content_hash TEXT NOT NULL,
    data TEXT,  -- JSON event data
    FOREIGN KEY (parent_event_id) REFERENCES genesis_events(event_id)
);

CREATE INDEX IF NOT EXISTS idx_genomes_fitness ON genomes(fitness_score DESC);
CREATE INDEX IF NOT EXISTS idx_genomes_generation ON genomes(generation);
CREATE INDEX IF NOT EXISTS idx_populations_generation ON populations(generation);
CREATE INDEX IF NOT EXISTS idx_genesis_events_type ON genesis_events(event_type);
CREATE INDEX IF NOT EXISTS idx_genesis_events_timestamp ON genesis_events(timestamp);

-- Initialize schema version
INSERT OR REPLACE INTO _schema_versions (module, version)
VALUES ('agents', 1);
