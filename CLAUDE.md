# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SGQ Ligne G is a Django-based production management system for Saint-Gobain Quartz SAS - Nemours, designed for felt manufacturing line management with ISO 9001, 14001, and 45001 compliance.

## Key Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Run development server
python manage.py runserver

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Run tests
python manage.py test

# Check for issues
python manage.py check
```

## Architecture

**Django Apps:**
- `core/`: Base models (Operator, FabricationOrder)
- `production/`: Shift management with auto-save functionality
- `quality/`: Defect tracking and thickness measurements
- `reports/`: Excel generation (planned)

**Key Patterns:**
- HTMX for dynamic UI updates without full page reloads
- Session-based auto-save for form persistence
- Modular block-based UI components
- Dynamic ID generation: Shifts use `DDMMYY_FirstnameLastname_Vacation`, Rolls use `OF_RollNumber`

**Important Models:**
- `Shift`: Tracks production shifts with machine states, meter readings, and time tracking
- `FabricationOrder`: Manufacturing orders with length requirements
- `RollDefect`: Quality defects with position tracking and blocking status
- `ThicknessMeasurement`: Thickness validation with configurable thresholds

**UI/UX Considerations:**
- 3-column responsive layout optimized for production floor
- French localization throughout
- "--" placeholder for empty fields
- Real-time validation with HTMX
- Edit buttons with confirmation workflow

**Development Notes:**
- No requirements.txt exists yet - dependencies are Django==5.2.4, django-htmx==1.23.2
- DEBUG=True in settings.py (must be False for production)
- SQLite database (PostgreSQL recommended for production)
- No linting or formatting tools configured
- Test files exist but contain only boilerplate

**Business Logic:**
- Defects can be blocking/non-blocking based on DefectType severity
- Thickness measurements auto-validate against specifications
- Machine states carry over between shifts for continuity
- All data tied to ISO compliance requirements