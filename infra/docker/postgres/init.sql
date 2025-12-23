-- Initialization script for PostgreSQL database
-- This runs once when the container is first created

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search optimization

-- Create schemas for logical separation
CREATE SCHEMA IF NOT EXISTS market_data;
CREATE SCHEMA IF NOT EXISTS news;
CREATE SCHEMA IF NOT EXISTS features;
CREATE SCHEMA IF NOT EXISTS agents;
CREATE SCHEMA IF NOT EXISTS users;

-- Set search path
ALTER DATABASE stockai_dev SET search_path TO public, market_data, news, features, agents, users;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA market_data TO stockai;
GRANT ALL PRIVILEGES ON SCHEMA news TO stockai;
GRANT ALL PRIVILEGES ON SCHEMA features TO stockai;
GRANT ALL PRIVILEGES ON SCHEMA agents TO stockai;
GRANT ALL PRIVILEGES ON SCHEMA users TO stockai;

-- Comment
COMMENT ON DATABASE stockai_dev IS 'Stock AI Platform - Development Database';
