# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SGQ Ligne G is a Django-based production management system for Saint-Gobain Quartz SAS - Nemours, designed for felt manufacturing line management with ISO 9001, 14001, and 45001 compliance.

## Key Commands

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Run development server
python manage.py runserver

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser

# Run tests
python manage.py test

# Check for issues
python manage.py check

# Collect static files (for production)
python manage.py collectstatic

# Run linting and type checking (when configured)
# TODO: Add linting commands when tools are configured
```

## Architecture

### Django Apps

**`core/`** - Base models and shared functionality
- `Operator`: Production operators with training status tracking
- `FabricationOrder`: Manufacturing orders with length requirements and progress tracking

**`production/`** - Shift and production management
- `Shift`: Production shifts with auto-generated IDs (DDMMYY_FirstnameLastname_Vacation)
- `CurrentProd`: Session-based auto-save for form persistence
- `QualityControl`: Quality measurements linked to shifts (renamed from QualityControlSeries)
- `Roll`: Individual production rolls with conformity tracking (preserves shift_id_str even if shift deleted)
- `RollDefect`: Defects on rolls with position tracking
- `RollThickness`: Thickness measurements at 6 points
- `LostTimeEntry`: Individual lost time entries linked to shifts
- Key feature: Quality controls must be complete before shift can be saved

**`quality/`** - Quality control and defect tracking
- `DefectType`: Defect definitions with severity levels (blocking/non-blocking/threshold)
- `RollDefect`: Actual defects with position tracking (meter position + side)
- `ThicknessMeasurement`: Thickness validation against specifications
- `Specification`: Configurable specs for all quality control types

**`reports/`** - Document generation (planned but not yet implemented)

### UI Architecture

- **Frontend**: Bootstrap 5.1.3 + HTMX for dynamic updates
- **Layout**: 3-column responsive design optimized for production floor tablets
- **Pattern**: Block-based modular UI with collapsible sections
- **Localization**: French throughout (user-facing strings, comments, field names)

### Key Patterns

**HTMX Integration**
- Forms use `hx-post` for submission without page reload
- `hx-get` loads content dynamically into blocks
- CSRF tokens handled via meta tag + event listener
- Auto-save triggered on field changes with 1-second debounce

**Session-Based Auto-Save**
- `CurrentProd` model stores form data per session
- JavaScript saves form state on every change
- Data restored on page load
- Critical for production floor reliability

**ID Generation**
- Shifts: `DDMMYY_FirstnameLastname_Vacation` (e.g., "091225_JeanDupont_Matin")
- Rolls: `OF_RollNumber` (e.g., "OF123_001")

**Validation Flow**
1. Client-side: Button disabled until quality controls filled
2. Server-side: Check quality controls before saving shift
3. Server-side: Verify shift doesn't already exist
4. Show JavaScript alerts for validation errors

### Business Logic

**Quality Control Requirements**
- All quality controls must be filled before shift can be saved:
  - Micronnaire: 6 values (3 left, 3 right)
  - Extrait Sec: 1 value + time
  - Masse Surfacique: 4 values (GG, GC, DC, DD)
  - LOI: Given status + time

**Machine State Continuity**
- `started_at_end` from previous shift → `started_at_beginning` for next shift
- Meter readings carry over between shifts
- Ensures production tracking continuity

**Lost Time Tracking**
- Lost time entries saved as individual `LostTimeEntry` records
- Linked to shift when shift is saved
- Preserved in session during data entry
- Accessible in admin interface

**Shift Transitions**
- Vacation sequence: Matin → ApresMidi → Nuit → Matin
- Default hours set based on vacation
- Date and operator cleared for privacy

## Development Considerations

### Current State
- **Database**: SQLite (development), PostgreSQL recommended for production
- **Dependencies**: 
  - Django==5.2.4
  - django-htmx==1.23.2
  - asgiref==3.9.0
  - sqlparse==0.5.3
- **Python Version**: 3.11+ required
- **Debug Mode**: Currently TRUE (must be FALSE for production)
- **Tests**: Test files exist but no tests implemented
- **Linting**: No tools configured yet

### Important Files
- `production/views.py`: Core shift management logic and validation
- `production/models.py`: All production-related models (Shift, Roll, QualityControl, etc.)
- `templates/production/blocks/shift_block.html`: Main shift form with quality controls
- `templates/production/prod.html`: Production dashboard layout
- `templates/production/blocks/fabric_block.html`: Fabrication order and roll management
- `static/css/style.css`: Custom styling with Saint-Gobain branding
- `sgq_ligne_g/settings.py`: Django configuration (change SECRET_KEY for production!)

### Common Modifications

**Adding a new quality control field**
1. Add field to `QualityControl` model in `production/models.py`
2. Create and run migration: `python manage.py makemigrations && python manage.py migrate`
3. Update form template (`shift_block.html`) to include input
4. Add to JavaScript validation in `checkAllQualityControlsFilled()`
5. Update server-side validation in `production/views.py`

**Modifying shift ID format**
1. Update `Shift.save()` method in model
2. Update validation logic in `views.shift_block()`
3. Consider migration for existing data

**Adding a new Django app**
1. Create app with `python manage.py startapp appname`
2. Add to `INSTALLED_APPS` in settings
3. Follow existing patterns for models and views
4. Use HTMX for dynamic updates

**Adding a new defect type**
1. Access Django admin at `/admin/` as superuser
2. Navigate to Quality > Defect types
3. Add new defect with name, severity, and threshold if applicable
4. Defect will automatically appear in roll defect selection lists

**Creating custom reports**
1. Implement report generation logic in `reports/views.py`
2. Use `openpyxl` or similar for Excel generation
3. Follow existing patterns for data aggregation
4. Add appropriate URL routing and permissions

### Security & Compliance
- ISO 9001, 14001, 45001 compliance built into data model
- All user actions tracked with timestamps
- Quality control data immutable once saved
- Session-based data isolated per user
- CSRF protection enabled on all forms
- Debug mode must be FALSE in production
- Change SECRET_KEY before deployment

### Production Deployment Checklist
1. Set `DEBUG = False` in settings.py
2. Configure `ALLOWED_HOSTS` with production domains
3. Generate new `SECRET_KEY`
4. Switch to PostgreSQL database
5. Configure static file serving
6. Set up proper backup procedures
7. Configure logging for production
8. Implement SSL/HTTPS
9. Set up monitoring and alerts

### Testing Utilities
- `test_shift_save.py`: Manual script to test shift creation
- `check_shifts.py`: Utility to inspect shifts in database
- `test_defect_functionality.js`: JavaScript test for defect UI

### Common Issues & Solutions

**Issue**: Form data not persisting after page reload
- Check session middleware is enabled
- Verify `CurrentProd` model is saving correctly
- Check JavaScript auto-save is not throwing errors

**Issue**: Quality controls not validating
- Ensure all 6 micronnaire fields have values
- Check that LOI and dry extract have both value and time
- Verify JavaScript validation matches server-side logic

**Issue**: Shift ID already exists error
- This is expected - each shift must have unique combination of date/operator/vacation
- Check if shift was already created
- Verify date and operator selection