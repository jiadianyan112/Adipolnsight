# AdipoInsight Architecture

## Overview

AdipoInsight is a medical research AI platform built with a Mock-First strategy.
The system consists of three layers:

1. **Frontend** (Vite + React + TypeScript + Tailwind + Zustand)
2. **Backend API** (FastAPI + SQLAlchemy + SQLite)
3. **Analysis Scripts** (Python CLI scripts called via subprocess)

## Data Flow

```
Browser → React App → REST API (/api/v1/*)
  → FastAPI → TaskOrchestrator → SkillRunner
    → subprocess → mock_*.py → stdout JSON
      → SkillRunner saves results → SQLite + storage/
```

## Directory Layout

See project README for full tree.

## Key Design Decisions

- SQLite for zero-config local deployment
- BackgroundTasks for in-process task execution (no Redis needed)
- UnifiedResultView adapts UI based on result_type
- All mock scripts share the same CLI contract (--output-dir, --task-id, stdout JSON)
