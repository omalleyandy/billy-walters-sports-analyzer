# Environment Configuration Guide

This document explains how to configure environment variables for Billy Walters Analytics database connection.

---

## Configuration Methods

You can set database credentials using **either**:
1. `.env` file (project-level, not committed to git)
2. Windows Environment Variables (system-level)
3. Both (Windows env vars take precedence)

---

## Option 1: .env File (Recommended for Development)

**Location:** `C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer\.env`

**Add these lines:**

```bash
# PostgreSQL Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=billy_walters_analytics
DB_USER=postgres
DB_PASSWORD=your_postgres_password_here
DB_MIN_CONNECTIONS=1
DB_MAX_CONNECTIONS=10
```

**Replace** `your_postgres_password_here` with your actual postgres superuser password.

**Example:**
```bash
DB_PASSWORD=Billy2025!Walters
```

**Security:** `.env` is in `.gitignore` so it won't be committed to git.

---

## Option 2: Windows Environment Variables (System-Level)

**For permanent system configuration, set Windows environment variables:**

### Step 1: Open Windows Environment Variables

```powershell
# Option A: Using Windows Settings
# Settings → System → About → Advanced system settings → Environment Variables

# Option B: Using PowerShell (as Administrator)
[Environment]::SetEnvironmentVariable("DB_HOST", "localhost", "User")
[Environment]::SetEnvironmentVariable("DB_PORT", "5432", "User")
[Environment]::SetEnvironmentVariable("DB_NAME", "billy_walters_analytics", "User")
[Environment]::SetEnvironmentVariable("DB_USER", "postgres", "User")
[Environment]::SetEnvironmentVariable("DB_PASSWORD", "your_password_here", "User")
```

### Step 2: Verify Variables Set

```powershell
# Check if variables are set
$env:DB_HOST
$env:DB_PORT
$env:DB_NAME
$env:DB_USER
$env:DB_PASSWORD
```

**Expected Output:**
```
localhost
5432
billy_walters_analytics
postgres
Billy2025!Walters
```

---

## Environment Variable Reference

| Variable | Default | Required | Purpose |
|----------|---------|----------|---------|
| `DB_HOST` | `localhost` | No | PostgreSQL server hostname |
| `DB_PORT` | `5432` | No | PostgreSQL server port |
| `DB_NAME` | `billy_walters_analytics` | No | Database name |
| `DB_USER` | `postgres` | No | Database user/superuser |
| `DB_PASSWORD` | `` (empty) | **YES** | Database password |
| `DB_MIN_CONNECTIONS` | `1` | No | Connection pool minimum |
| `DB_MAX_CONNECTIONS` | `10` | No | Connection pool maximum |

---

## Connection Priority

When `src/db/connection.py` initializes, it checks for values in this order:

1. **Function parameters** (if you pass them directly)
2. **Environment variables** (`.env` or Windows env vars)
3. **Defaults** (hardcoded fallback values)

**Example:**
```python
from src.db import get_db_connection

# Uses env variables
db = get_db_connection()

# Override with parameters (takes precedence over env vars)
db = get_db_connection(
    host="remote-server.com",
    port=5432
)
```

---

## Testing Configuration

### Test 1: Verify Environment Variables Loaded

```powershell
uv run python -c "
import os
print('DB_HOST:', os.getenv('DB_HOST', 'NOT SET'))
print('DB_PORT:', os.getenv('DB_PORT', 'NOT SET'))
print('DB_NAME:', os.getenv('DB_NAME', 'NOT SET'))
print('DB_USER:', os.getenv('DB_USER', 'NOT SET'))
print('DB_PASSWORD:', 'SET' if os.getenv('DB_PASSWORD') else 'NOT SET')
"
```

**Expected Output:**
```
DB_HOST: localhost
DB_PORT: 5432
DB_NAME: billy_walters_analytics
DB_USER: postgres
DB_PASSWORD: SET
```

### Test 2: Connection Test Script

```powershell
uv run python scripts/database/test_connection.py
```

**Expected Output:**
```
[OK] Connection pool created: billy_walters_analytics@localhost
[OK] Connected to PostgreSQL: PostgreSQL 18.1...
[OK] Found 9 tables (expected: 9)
...
[OK] DATABASE SETUP COMPLETE!
```

---

## Troubleshooting

### Issue: "password authentication failed"

**Cause:** Wrong password in environment variable

**Solution:**
1. Verify `DB_PASSWORD` is set correctly
2. Check for extra spaces or special characters
3. Test password in pgAdmin 4 first

```powershell
# View current password (careful - it's in plaintext)
$env:DB_PASSWORD
```

### Issue: "could not connect to server"

**Cause:** PostgreSQL service not running or wrong host/port

**Solution:**
```powershell
# Check service status
Get-Service -Name postgresql*

# Check DB_HOST and DB_PORT are correct
$env:DB_HOST
$env:DB_PORT

# Verify PostgreSQL is listening on port 5432
netstat -ano | findstr :5432
```

### Issue: Environment variables not taking effect

**Cause:** Python process still has old environment

**Solution:**
1. Close all Python terminals
2. Close IDE/code editor
3. Reopen terminal
4. Test again

**Or verify env vars in new Python process:**
```powershell
# New PowerShell window
pwsh
$env:DB_PASSWORD  # Should show value
```

---

## Security Best Practices

✅ **DO:**
- Store passwords in environment variables (not in code)
- Keep `.env` file in `.gitignore`
- Use `.env.example` template (with dummy values)
- Use strong passwords (12+ characters, mixed case/numbers/special)
- Rotate passwords periodically

❌ **DON'T:**
- Hardcode passwords in source code
- Commit `.env` to git
- Share credentials in Slack, email, or chats
- Use same password for dev/prod
- Store unencrypted credentials in plain text files

---

## Production Considerations

**For production environments:**
1. Use system environment variables (not `.env` file)
2. Consider using AWS Secrets Manager, Azure Key Vault, or similar
3. Use distinct credentials (different user for each environment)
4. Set minimum permissions (read-only users where possible)
5. Enable SSL/TLS for remote connections

**Production Environment Variables:**
```powershell
# Use different credentials than development
[Environment]::SetEnvironmentVariable("DB_PASSWORD", "prod_password_here", "User")
[Environment]::SetEnvironmentVariable("DB_HOST", "prod-db-server.com", "User")
```

---

## Current Configuration Status

**Your Setup:**
- ✅ PostgreSQL 18.1 installed
- ✅ billy_walters_analytics database created
- ✅ .env file with credentials
- ✅ Windows environment variables set
- ✅ Python psycopg2 driver installed
- ✅ Connection code clean and consistent

**Environment variables used by connection.py:**
```python
DB_HOST         → localhost (default)
DB_PORT         → 5432 (default)
DB_NAME         → billy_walters_analytics (default)
DB_USER         → postgres (default)
DB_PASSWORD     → YOUR_POSTGRES_PASSWORD (required)
```

---

## Quick Reference

```bash
# Set in PowerShell (current session only)
$env:DB_PASSWORD="your_password"

# Set permanently (Windows User variables)
[Environment]::SetEnvironmentVariable("DB_PASSWORD", "your_password", "User")

# View current setting
$env:DB_PASSWORD

# View all DB variables
Get-Item env:DB_*
```

---

**Generated:** 2025-11-23
**Version:** 1.0.0
**Project:** Billy Walters Sports Analytics