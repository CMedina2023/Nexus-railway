# PostgreSQL Placeholder Fix - Summary

## Problem
The application was failing on Railway with PostgreSQL because the repository code was using SQLite-style parameter placeholders (`?`) instead of PostgreSQL-style placeholders (`%s`).

### Error Messages
```
ERROR:app.core.app:Error al guardar historias en BD local: syntax error at or near ","
LINE 5:                 ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                   ^

ERROR:app.auth.metrics_routes:Error al guardar reporte en BD local: syntax error at or near ","
LINE 5:                 ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                   ^
```

## Root Cause
The repositories were using `get_db_connection()` which returns a raw database connection without the `CursorWrapper` that adapts SQL placeholders. The `CursorWrapper` in `db.py` was designed to automatically convert `?` to `%s` for PostgreSQL, but it was only available through `get_cursor()` context manager.

## Solution
Updated the following repository files to detect the database type and use the appropriate placeholder:

### Files Fixed ✅
1. **user_story_repository.py** - Now detects DB type and uses `%s` for PostgreSQL, `?` for SQLite
2. **jira_report_repository.py** - Now detects DB type and uses `%s` for PostgreSQL, `?` for SQLite  
3. **test_case_repository.py** - Now detects DB type and uses `%s` for PostgreSQL, `?` for SQLite
4. **bulk_upload_repository.py** - Now detects DB type and uses `%s` for PostgreSQL, `?` for SQLite

### Files Already Compatible ✅
These files were already using `self.db.get_cursor()` which has the `CursorWrapper`:
- **user_repository.py**
- **user_jira_config_repository.py**
- **project_config_repository.py**

## Changes Made

### Pattern Used
For each repository method that executes SQL queries:

```python
# Before (SQLite only)
cursor.execute('''
    INSERT INTO table (col1, col2)
    VALUES (?, ?)
''', (val1, val2))

# After (SQLite + PostgreSQL compatible)
db = get_db()
placeholder = '%s' if db.is_postgres else '?'

cursor.execute(f'''
    INSERT INTO table (col1, col2)
    VALUES ({placeholder}, {placeholder})
''', (val1, val2))
```

### Additional Changes
- Removed `import sqlite3` from all repository files
- Changed `sqlite3.Error` to generic `Exception` for database error handling
- Added `from app.database.db import get_db` to detect database type

## Testing
After deploying to Railway, the following operations should now work:
1. ✅ Saving user stories to database
2. ✅ Saving Jira reports to database  
3. ✅ Generating and saving PDF metrics
4. ✅ All other database operations

## Database Compatibility
The application now supports:
- **SQLite** (local development) - Uses `?` placeholders
- **PostgreSQL** (Railway production) - Uses `%s` placeholders

The detection is automatic based on the `DATABASE_URL` environment variable.
