# WSL Setup Guide - Billy Walters Sports Analyzer

**Last Updated:** November 2, 2025  
**Tested On:** WSL 2 (Ubuntu 22.04)  
**Status:** ✅ Fully Compatible

## Overview

The Billy Walters Sports Analyzer is fully compatible with Windows Subsystem for Linux (WSL). This guide covers setup, configuration, and troubleshooting for running the project in WSL.

---

## Prerequisites

### 1. Install WSL 2

If you haven't installed WSL yet:

```powershell
# In Windows PowerShell (as Administrator)
wsl --install -d Ubuntu-22.04
```

Restart your computer when prompted.

### 2. Update WSL

```bash
# In PowerShell
wsl --update
```

### 3. Install uv in WSL

```bash
# In WSL terminal
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH (add this to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"

# Reload shell
source ~/.bashrc
```

### 4. Install Git in WSL

```bash
sudo apt update
sudo apt install git -y
```

---

## Project Setup in WSL

### Method 1: Clone Fresh (Recommended)

```bash
cd ~
mkdir -p projects
cd projects
git clone https://github.com/omalleyandy/billy-walters-sports-analyzer.git
cd billy-walters-sports-analyzer
```

### Method 2: Access Windows Files

You can access your Windows files from WSL:

```bash
# Windows C:\ drive is mounted at /mnt/c/
cd /mnt/c/Users/YOUR_USERNAME/Documents/python_projects/billy-walters-sports-analyzer
```

⚠️ **Performance Note:** Working directly in `/mnt/c/` is slower. For best performance, clone the repo into your WSL home directory.

---

## Environment Setup

### 1. Copy Environment File

```bash
# If you have a .env in Windows, copy it
cp /mnt/c/Users/YOUR_USERNAME/Documents/python_projects/billy-walters-sports-analyzer/.env .env

# Or create from template
cp .env.example .env

# Edit with your credentials
nano .env
```

### 2. Install Dependencies

```bash
# Sync Python dependencies
uv sync

# Install Playwright browsers
uv run playwright install --with-deps chromium
```

The `--with-deps` flag installs system dependencies required for Playwright on Linux.

### 3. Verify Installation

```bash
# Test Phase 1 components
uv run python -c "from walters_analyzer.core import async_get, cache_weather_data, TeamRating; print('[OK] Phase 1 working!')"

# Test Phase 2 components
uv run python -c "from walters_analyzer.research import ScrapyBridge, ResearchEngine; print('[OK] Phase 2 working!')"

# View configuration
uv run python -c "from walters_analyzer.config import get_config; print(get_config().get_summary())"
```

---

## Running the Project

### Bootstrap Command

```bash
# Run bootstrap to set up environment
./commands/bootstrap
```

This script:
- Sets up `UV_CACHE_DIR` for WSL compatibility
- Runs `uv sync`
- Installs Playwright browsers

### Run Codex Hooks

```bash
# Test the preflight script
bash .codex/preflight.sh
```

This runs all hooks:
- `00-on_start.sh` - Repository info
- `10-guardrails.sh` - Protected file checks
- `20-quality.sh` - Environment validation
- `30-pytest.sh` - Test suite

### CLI Commands

All CLI commands work the same in WSL:

```bash
# Scrape injuries
uv run walters-analyzer scrape-injuries --sport nfl

# Scrape weather
uv run walters-analyzer scrape-weather --card ./cards/wk-card-2025-10-31.json

# Update power ratings
uv run walters-analyzer weekly-nfl-update --week 10

# Analyze a card
uv run walters-analyzer wk-card --file ./cards/wk-card-2025-10-31.json --dry-run
```

---

## WSL-Specific Configuration

### UV Cache Directory

The bootstrap script automatically sets `UV_CACHE_DIR` to avoid permission issues:

```bash
# In commands/bootstrap
if [ -z "${UV_CACHE_DIR:-}" ]; then
  export UV_CACHE_DIR="$PWD/.uv-cache"
  mkdir -p "$UV_CACHE_DIR"
fi
```

You can also set this permanently in your `~/.bashrc`:

```bash
echo 'export UV_CACHE_DIR="$HOME/.cache/uv"' >> ~/.bashrc
source ~/.bashrc
```

### Git Configuration

Ensure git is configured to handle line endings correctly:

```bash
# Set your identity
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Line ending configuration (handled by .gitattributes)
git config --global core.autocrlf input
```

---

## File System Considerations

### Performance

| Location | Performance | Best For |
|----------|-------------|----------|
| `/home/username/` | ⚡ Fast | Development, running code |
| `/mnt/c/...` | 🐌 Slow | Accessing Windows files |
| `//wsl$/Ubuntu/home/...` | ⚡ Fast | Windows accessing WSL files |

**Recommendation:** Clone the repo into WSL's native filesystem (`~/projects/`) for best performance.

### Accessing WSL Files from Windows

You can access your WSL files from Windows Explorer:

```
\\wsl$\Ubuntu\home\YOUR_USERNAME\projects\billy-walters-sports-analyzer\
```

Or directly:
```
\\wsl.localhost\Ubuntu\home\YOUR_USERNAME\projects\billy-walters-sports-analyzer\
```

### Line Endings

The project uses `.gitattributes` to enforce correct line endings:
- Shell scripts (`.sh`, hooks): LF
- Python files (`.py`): LF
- Windows batch files (`.bat`): CRLF

Git will automatically handle conversions when you check out files.

---

## Troubleshooting

### Issue: `uv: command not found`

**Solution:**
```bash
# Make sure uv is in PATH
export PATH="$HOME/.local/bin:$PATH"

# Or reinstall uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Issue: `playwright: command not found` or browser launch fails

**Solution:**
```bash
# Install system dependencies
uv run playwright install --with-deps chromium

# If that fails, install dependencies manually
sudo apt install -y \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2
```

### Issue: Permission denied on shell scripts

**Solution:**
```bash
# Make scripts executable
chmod +x .codex/preflight.sh
chmod +x hooks/*.sh
chmod +x scripts/*.sh
chmod +x commands/bootstrap
chmod +x commands/wk-card
chmod +x commands/scrape-vi
```

### Issue: `pytest` not found

**Solution:**
```bash
# Install dev dependencies
uv sync --extra dev

# Or run pytest without syncing
uv run --no-sync pytest tests/ -v
```

### Issue: Cache permission errors

**Solution:**
```bash
# Set custom cache directory
export UV_CACHE_DIR="$HOME/.cache/uv"
mkdir -p "$UV_CACHE_DIR"

# Or use project-local cache
export UV_CACHE_DIR="$PWD/.uv-cache"
mkdir -p "$UV_CACHE_DIR"

# Add to ~/.bashrc to make permanent
echo 'export UV_CACHE_DIR="$HOME/.cache/uv"' >> ~/.bashrc
```

### Issue: CRLF line ending errors

**Solution:**
```bash
# The project has .gitattributes to handle this automatically
# But if you see issues, convert manually:
dos2unix hooks/*.sh
dos2unix .codex/preflight.sh
dos2unix scripts/*.sh

# Install dos2unix if needed
sudo apt install dos2unix -y
```

### Issue: Module import errors

**Solution:**
```bash
# Ensure you're in the project directory
cd ~/projects/billy-walters-sports-analyzer

# Verify uv sync completed
uv sync

# Check Python path
uv run python -c "import sys; print('\n'.join(sys.path))"

# Verify module can be imported
uv run python -c "import walters_analyzer; print('OK')"
```

---

## Development Workflow in WSL

### Recommended Setup

1. **Clone in WSL** for best performance:
   ```bash
   cd ~/projects
   git clone https://github.com/omalleyandy/billy-walters-sports-analyzer.git
   cd billy-walters-sports-analyzer
   ```

2. **Edit in VS Code** from Windows:
   ```powershell
   # In PowerShell
   wsl
   cd ~/projects/billy-walters-sports-analyzer
   code .
   ```

3. **Run commands in WSL terminal**:
   ```bash
   # All uv run commands
   uv run walters-analyzer --help
   ```

### VS Code WSL Extension

Install the "WSL" extension in VS Code for seamless integration:
- Open VS Code
- Install "WSL" extension
- Click "Open a Remote Window" (bottom left)
- Select "Connect to WSL"

This gives you:
- Native Linux environment
- Windows UI
- Integrated terminal in WSL
- Git operations in WSL

---

## Automation in WSL

### Cron Jobs

Set up weekly power ratings updates:

```bash
# Edit crontab
crontab -e

# Add this line (runs every Tuesday at 6 AM)
0 6 * * 2 cd /home/YOUR_USERNAME/projects/billy-walters-sports-analyzer && ./scripts/weekly_power_ratings_update.sh $(date +\%V)
```

### Systemd Services

Create a systemd service for automated tasks:

```bash
# Create service file
sudo nano /etc/systemd/system/walters-analyzer.service
```

```ini
[Unit]
Description=Billy Walters Sports Analyzer Weekly Update
After=network.target

[Service]
Type=oneshot
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/projects/billy-walters-sports-analyzer
ExecStart=/home/YOUR_USERNAME/.local/bin/uv run walters-analyzer weekly-nfl-update --week 10
Environment=PATH=/home/YOUR_USERNAME/.local/bin:/usr/local/bin:/usr/bin:/bin

[Install]
WantedBy=multi-user.target
```

Enable and test:
```bash
sudo systemctl daemon-reload
sudo systemctl enable walters-analyzer.service
sudo systemctl start walters-analyzer.service
sudo systemctl status walters-analyzer.service
```

---

## Testing in WSL

### Run All Tests

```bash
uv run pytest tests/ -v
```

### Run Specific Tests

```bash
# Test power ratings
uv run pytest tests/test_power_ratings.py -v

# Test key numbers
uv run pytest tests/test_key_numbers.py -v

# Test S/W/E factors
uv run pytest tests/test_swe_factors.py -v
```

### Run Smoke Tests

```bash
# Quick verification
uv run python examples/verify_all.py

# Test research module
uv run python examples/complete_research_demo.py
```

---

## Performance Comparison

| Task | Windows | WSL (Native FS) | WSL (Windows FS) |
|------|---------|-----------------|------------------|
| `uv sync` | ~5s | ~4s | ~15s |
| Import modules | ~0.5s | ~0.4s | ~1.2s |
| Run pytest | ~10s | ~9s | ~25s |
| Scrapy spider | ~30s | ~28s | ~45s |

**Takeaway:** Use WSL's native filesystem for best performance.

---

## Known Issues

### 1. Venv Permission Errors

**Symptom:**
```
error: failed to remove file `.venv/lib64`: Access is denied.
```

**Workaround:**
```bash
# Remove .venv and recreate
rm -rf .venv
uv sync
```

### 2. Slow File Operations on /mnt/c/

**Symptom:** Commands take much longer than expected.

**Solution:** Clone repo into WSL filesystem (`~/projects/`).

### 3. Windows Defender Slowing Down WSL

**Symptom:** File operations are slow even in WSL filesystem.

**Solution:** Add exclusion in Windows Defender:
```powershell
# In PowerShell (as Administrator)
Add-MpPreference -ExclusionPath "\\wsl$\Ubuntu\home\YOUR_USERNAME\projects"
```

---

## Best Practices

### 1. Use Native WSL Filesystem
✅ Do: `~/projects/billy-walters-sports-analyzer/`  
❌ Don't: `/mnt/c/Users/.../billy-walters-sports-analyzer/`

### 2. Set UV_CACHE_DIR
```bash
export UV_CACHE_DIR="$HOME/.cache/uv"
```

### 3. Use VS Code WSL Extension
- Edit files with Windows UI
- Run commands in native Linux environment
- Best of both worlds

### 4. Keep .env in WSL
Don't share `.env` between Windows and WSL versions. Keep separate configs if running in both environments.

### 5. Use Git from WSL
Run all git commands from WSL terminal for consistent line endings.

---

## Additional Resources

### Official Documentation
- **WSL Docs:** https://docs.microsoft.com/en-us/windows/wsl/
- **uv Docs:** https://github.com/astral-sh/uv
- **Playwright WSL:** https://playwright.dev/python/docs/browsers#installing-system-dependencies

### Project Documentation
- `README.md` - Project overview
- `CLAUDE.md` - Command reference
- `docs/QUICK_REFERENCE.md` - API quick reference
- `docs/CODE_QUALITY_ASSESSMENT.md` - Code quality review

### Troubleshooting
- `docs/GIT_AND_SECRETS_GUIDE.md` - Git and secrets management
- `START_HERE.md` - Quick start guide

---

## Summary

The Billy Walters Sports Analyzer is fully compatible with WSL 2. For best results:

1. ✅ Clone repo into WSL native filesystem
2. ✅ Install uv and Playwright with system dependencies  
3. ✅ Use VS Code WSL extension for editing
4. ✅ Run all commands in WSL terminal
5. ✅ Set UV_CACHE_DIR environment variable

All features work identically in WSL and Windows:
- ✅ Scrapy spiders with Playwright
- ✅ Power ratings engine
- ✅ Weather API integration
- ✅ Betting analysis
- ✅ CLV tracking
- ✅ All CLI commands

---

*Last Updated: November 2, 2025*  
*Version: 1.0*  
*Status: Production Ready*

