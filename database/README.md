# Database

Runtime SQLite database location when running under Electron:

- Windows: `%APPDATA%/Sentinel/sentinel.db`
- macOS: `~/Library/Application Support/Sentinel/sentinel.db`
- Linux: `~/.config/Sentinel/sentinel.db`

The database is automatically created and migrated on first launch via
`src/database.py:init_db()`. No manual setup required.

Environment variables:
- `DATABASE_PATH` — override database file path
- `UPLOADS_DIR` — override uploads directory path
