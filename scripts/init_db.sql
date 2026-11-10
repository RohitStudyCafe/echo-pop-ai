-- ==============================================================================
-- Echo Pop Cloud AI Voice Assistant - Database Schema Initialization Script
-- 
-- Run this script manually in your PostgreSQL or SQLite database.
-- Note: Antigravity adheres to user rules and does not automatically execute
-- database migrations or connect to live databases.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- PostgreSQL Schema
-- ------------------------------------------------------------------------------
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS alexa_users (
    user_id VARCHAR(255) PRIMARY KEY,
    preferred_provider VARCHAR(50) DEFAULT 'openai',
    custom_system_prompt TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversation_history (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    provider VARCHAR(50),
    model VARCHAR(100),
    latency_ms DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_alexa_user FOREIGN KEY (user_id) REFERENCES alexa_users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_conv_user_created ON conversation_history(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conv_session ON conversation_history(session_id);

-- ------------------------------------------------------------------------------
-- SQLite Equivalent Schema (if using local SQLite file)
-- ------------------------------------------------------------------------------
/*
CREATE TABLE IF NOT EXISTS alexa_users (
    user_id TEXT PRIMARY KEY,
    preferred_provider TEXT DEFAULT 'openai',
    custom_system_prompt TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    provider TEXT,
    model TEXT,
    latency_ms REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES alexa_users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_conv_user_created ON conversation_history(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conv_session ON conversation_history(session_id);
*/

