
# Windows Setup Guide

## Migration Complete! ✓

Your project has been successfully migrated from WSL to Windows.

**Location:** `C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer`

## What Was Done

1. ✓ Copied entire project from WSL to Windows
2. ✓ Removed `.git` folder (no more git repository)
3. ✓ Removed `.github` folder (no more GitHub workflows)
4. ✓ Kept `.gitignore` and `.gitattributes` files
5. ✓ WSL backup remains at `/home/omalleyandy/billy-walters-sports-analyzer`

## Next Steps - Setting Up Your Windows Environment


### 1. Install Python (if not already installed)

Download and install Python 3.11 or later from:
- https://www.python.org/downloads/

**Important:** During installation, check the box "Add Python to PATH"

### 2. Install UV Package Manager

Open PowerShell or Command Prompt and run:

```powershell
pip install uv
```

Or install via the official method:
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 3. Navigate to Your Project

```powershell
cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer
```

### 4. Create Your Environment File

Copy the template to create your `.env` file:

```powershell
copy env.template .env
```

Then edit `.env` with your favorite text editor and fill in your real credentials:
- Notepad: `notepad .env`
- VSCode: `code .env`

### 5. Install Dependencies

```powershell
uv pip install -e .
```

Or if you prefer using regular pip:
```powershell
pip install -e .
```

### 6. Run a Test

To verify everything works:

```powershell
uv run walters-analyzer --help
```

Or run the tests:
```powershell
pytest
```

## Project Structure

Your project contains:
- `walters_analyzer/` - Main Python package
- `tests/` - Test files
- `data/` - Data directories (injuries, odds, schedules)
- `scripts/` - Utility scripts
- `scrapers/` - Web scraping modules
- `cards/` - Betting card configurations
- Documentation files (*.md)

## Key Files

- `pyproject.toml` - Project configuration and dependencies
- `env.template` - Template for environment variables
- `README.md` - Main project documentation
- `QUICKSTART.md` - Quick start guide
- `USAGE_GUIDE.md` - Detailed usage instructions

## No More Git/GitHub

Since you removed Git:
- You won't need to commit or push changes
- No branches to manage
- Changes are automatically saved locally
- Your WSL copy serves as a backup

## Tips for Windows

1. **Use PowerShell** instead of Command Prompt for better experience
2. **Windows Terminal** (free from Microsoft Store) is even better
3. File paths use backslashes: `C:\path\to\file`
4. You can still use forward slashes in Python code
5. The `.env` file won't show in File Explorer by default (it's hidden)

## If You Need Help

- Check `README.md` for project overview
- See `QUICKSTART.md` for getting started
- Review `USAGE_GUIDE.md` for detailed instructions
- All your documentation is in the project folder

## WSL Backup Location

Your original WSL project is still available at:
```
/home/omalleyandy/billy-walters-sports-analyzer
```

You can access it from Windows File Explorer at:
```
\\wsl$\Ubuntu\home\omalleyandy\billy-walters-sports-analyzer
```

---

**You're all set!** Open your project in your favorite Windows code editor and start working.

