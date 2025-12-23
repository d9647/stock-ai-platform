# Migration Note: Fixed SQLAlchemy Reserved Keyword

## Issue
SQLAlchemy's `Base` class uses `metadata` as a reserved attribute name for table metadata. Our `AgentOutput` model had a column named `metadata` which caused this error:

```
sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
```

## Fix Applied
Renamed the column from `metadata` to `agent_metadata` in:
- [api/app/models/agents.py](api/app/models/agents.py) line 43

## When to Run Migration

After pulling this change, you need to create and run a database migration:

```bash
cd api
source venv/bin/activate

# Create migration
alembic revision --autogenerate -m "Rename metadata to agent_metadata"

# Review the migration file in api/migrations/versions/

# Apply migration
alembic upgrade head
```

## If You Haven't Created Any Data Yet

If you're setting up fresh (which you likely are in Phase 1), just run:

```bash
cd api
source venv/bin/activate
alembic upgrade head
```

This will create all tables with the correct column name from the start.

## What Changed

**Before:**
```python
metadata = Column(JSONB, default={})  # Reserved keyword!
```

**After:**
```python
agent_metadata = Column(JSONB, default={})  # No conflict
```

This field stores additional agent-specific data as JSON, and is only used in Phase 3 (agent orchestrator).