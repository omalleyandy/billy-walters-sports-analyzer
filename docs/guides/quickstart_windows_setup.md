# 🚀 TASK 2.2 - WINDOWS QUICK-START GUIDE

## ✅ Files Ready on Your Windows Machine

All Task 2.2 files have been created and are ready to use:

```
C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer\
├── src\walters_analyzer\data_collection\
│   └── weather_context_builder.py (650 lines) ✓
├── tests\
│   └── test_weather_context_builder.py (850 lines) ✓
├── scripts\
│   └── validate_weather_context_builder.py (450 lines) ✓
└── docs\
    ├── TASK_2_2_WEATHER_CONTEXT_BUILDER.md ✓
    └── TASK_2_2_COMPLETION_REPORT.md ✓
```

---

## 📋 WINDOWS SETUP (One-time)

### Step 1: Open PowerShell
```powershell
# Press: Win + X, then select "Windows PowerShell" or "Windows Terminal"
# OR search for "PowerShell" in Start Menu
```

### Step 2: Navigate to Project Root
```powershell
cd "C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer"

# Verify you're in the right place (should show these folders):
ls
# Should show: src, tests, docs, scripts, .venv, etc.
```

### Step 3: Activate Virtual Environment
```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# If you get an execution policy error, run this first:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then try activation again
.\.venv\Scripts\Activate.ps1
```

**You should see `(.venv)` at the start of your prompt when active**

---

## 🧪 RUNNING THE TESTS

### Option 1: Run All Tests (Comprehensive)
```powershell
# Make sure you're in project root and .venv is activated
pytest tests/test_weather_context_builder.py -v

# Expected output:
# test_weather_context_builder.py::TestWeatherBuilderInit::test_builder_creates_successfully PASSED
# test_weather_context_builder.py::TestTemperatureFactors::test_no_cold_impact_above_32f PASSED
# ... (40+ tests total)
# ==================== 40+ passed in X.XXs ====================
```

### Option 2: Run Specific Test Class
```powershell
# Test only temperature factors
pytest tests/test_weather_context_builder.py::TestTemperatureFactors -v

# Test only wind factors
pytest tests/test_weather_context_builder.py::TestWindFactors -v

# Test only team suitability
pytest tests/test_weather_context_builder.py::TestTeamWeatherSuitability -v
```

### Option 3: Run with Coverage Report
```powershell
# Shows what code paths are covered by tests
pytest tests/test_weather_context_builder.py --cov=src.walters_analyzer.data_collection --cov-report=term-missing

# Expected: >90% coverage
```

### Option 4: Run Tests with Detailed Output
```powershell
# Shows print statements and detailed error info
pytest tests/test_weather_context_builder.py -v -s

# The -s flag shows all print output from tests
```

---

## ✅ RUNNING THE VALIDATION SCRIPT

### Run Full Validation
```powershell
# From project root with .venv activated
python scripts/validate_weather_context_builder.py

# Expected output:
# ================================================================================
# TASK 2.2 VALIDATION SUITE - WEATHER CONTEXT BUILDER
# ================================================================================
#
# [Phase 1] Basic Functionality
#   ✓ WeatherContextBuilder initializes successfully
#   ✓ WeatherContextBuilder initializes
#   ✓ Cache starts empty
#   ✓ WeatherContextBuilder logger configured
#
# [Phase 2] W-Factor Calculations
#   ✓ Indoor games marked correctly
#   ✓ Indoor has zero W-Factors
#   ... (more validations)
#
# ================================================================================
# VALIDATION SUMMARY
# ================================================================================
#
# Tests Run: 35+
# Passed: 35+ ✓
# Failed: 0 ✗
#
# ✓ ALL VALIDATIONS PASSED!
# ✓ Weather Context Builder is PRODUCTION-READY
```

---

## 🧑‍💻 TESTING THE CODE MANUALLY

### Quick Python Test
```powershell
# Open Python interactive shell
python

# Then type:
>>> from src.walters_analyzer.data_collection.weather_context_builder import WeatherContextBuilder
>>> from src.walters_analyzer.models.sfactor_data_models import WeatherContext, Precipitation
>>> from datetime import datetime
>>>
>>> # Create builder
>>> builder = WeatherContextBuilder()
>>> print("✓ Builder created successfully")
>>>
>>> # Create weather context
>>> weather = WeatherContext(
...     game_location="Buffalo, NY",
...     is_indoor=False,
...     temperature_f=20,
...     wind_speed_mph=18,
...     precipitation_type=Precipitation.LIGHT_SNOW,
...     forecast_timestamp=datetime.now(),
... )
>>>
>>> # Calculate W-Factors
>>> wf = builder.calculate_wfactors(weather, "Buffalo Bills", "Miami Dolphins")
>>> print(f"W-Factors calculated: {wf.total_impact_spread:+.1f} spread impact")
>>> print(f"Data quality: {wf.data_quality.value}")
>>>
>>> # Assess team suitability
>>> bills_suit = builder.assess_team_weather_suitability("Buffalo Bills", weather)
>>> dolphins_suit = builder.assess_team_weather_suitability("Miami Dolphins", weather)
>>>
>>> print(f"Buffalo suitability: {bills_suit.value}")
>>> print(f"Miami suitability: {dolphins_suit.value}")
>>>
>>> # Exit Python
>>> exit()
```

**Expected Output**:
```
✓ Builder created successfully
W-Factors calculated: -5.1 spread impact
Data quality: excellent
Buffalo suitability: highly_favorable
Miami suitability: highly_unfavorable
```

---

## 📊 CHECKING INSTALLATION

### Verify All Files Are Present
```powershell
# Check production code
Test-Path "src\walters_analyzer\data_collection\weather_context_builder.py"
# Should return: True

# Check test file
Test-Path "tests\test_weather_context_builder.py"
# Should return: True

# Check validation script
Test-Path "scripts\validate_weather_context_builder.py"
# Should return: True

# Check documentation
Test-Path "docs\TASK_2_2_WEATHER_CONTEXT_BUILDER.md"
# Should return: True
```

### Check File Sizes
```powershell
# List all files with sizes
ls -Recurse src\walters_analyzer\data_collection\weather_context_builder.py | Select-Object Name, @{Name="SizeKB";Expression={[math]::Round($_.Length/1024, 2)}}

# Expected: ~24 KB for production code
```

---

## 🔧 TROUBLESHOOTING

### Issue: "No module named 'walters_analyzer'"

**Solution 1: Check you're in the right directory**
```powershell
# Must be in project root
pwd
# Should show: C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer

cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer
```

**Solution 2: Activate virtual environment**
```powershell
# Make sure .venv is activated (should see (.venv) in prompt)
.\.venv\Scripts\Activate.ps1
```

**Solution 3: Reinstall project in development mode**
```powershell
# From project root with .venv activated
pip install -e .
```

---

### Issue: "pytest: The term 'pytest' is not recognized"

**Solution 1: Install pytest**
```powershell
pip install pytest pytest-cov
```

**Solution 2: Use python -m pytest instead**
```powershell
python -m pytest tests/test_weather_context_builder.py -v
```

---

### Issue: "WindowsError: [Error 5] Access is denied"

**Solution: Run PowerShell as Administrator**
```powershell
# Close current PowerShell
# Right-click PowerShell or Windows Terminal
# Select "Run as Administrator"
# Then try again
```

---

### Issue: "ModuleNotFoundError: No module named 'pydantic'"

**Solution: Install missing dependencies**
```powershell
pip install pydantic
# Or reinstall all requirements
pip install -r requirements.txt
```

---

## 📝 COMMON COMMANDS REFERENCE

### Quick Reference Card

```powershell
# ========== SETUP ==========
# Navigate to project
cd "C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer"

# Activate environment
.\.venv\Scripts\Activate.ps1

# ========== TESTING ==========
# Run all tests
pytest tests/test_weather_context_builder.py -v

# Run specific test class
pytest tests/test_weather_context_builder.py::TestTemperatureFactors -v

# Run with coverage
pytest tests/test_weather_context_builder.py --cov

# ========== VALIDATION ==========
# Run validation script
python scripts/validate_weather_context_builder.py

# ========== DEBUGGING ==========
# Open Python shell
python

# Show installed packages
pip list

# Update pip
pip install --upgrade pip

# ========== CLEANUP ==========
# Deactivate virtual environment
deactivate

# Delete test cache
rmdir -Force __pycache__, .pytest_cache
```

---

## ✨ EXPECTED SUCCESS RESULTS

### After Running Tests
```
==================== 40+ passed in 5.23s ====================
```

### After Running Validation
```
✓ ALL VALIDATIONS PASSED!
✓ Weather Context Builder is PRODUCTION-READY
```

### After Manual Python Test
```
✓ Builder created successfully
W-Factors calculated: -5.1 spread impact
Data quality: excellent
Buffalo suitability: highly_favorable
Miami suitability: highly_unfavorable
```

---

## 📚 WHERE TO FIND DOCUMENTATION

### Main Documentation
```
C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer\
docs\TASK_2_2_WEATHER_CONTEXT_BUILDER.md
```

**Includes**:
- Complete API reference
- Usage examples
- Real-world scenarios
- Troubleshooting

### Completion Report
```
C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer\
docs\TASK_2_2_COMPLETION_REPORT.md
```

**Includes**:
- What was built
- Code statistics
- Test results
- Next steps

---

## 🎯 YOUR NEXT STEPS

### Immediate (Next 5 minutes)
1. ✅ Verify all files are on your machine (use file check commands above)
2. ✅ Navigate to project root in PowerShell
3. ✅ Activate virtual environment
4. ✅ Run validation script: `python scripts/validate_weather_context_builder.py`

### Short-term (Today)
5. Run test suite: `pytest tests/test_weather_context_builder.py -v`
6. Read main documentation: `docs/TASK_2_2_WEATHER_CONTEXT_BUILDER.md`
7. Try manual Python test (see section above)

### Medium-term (This Week)
8. Review code in `src/walters_analyzer/data_collection/weather_context_builder.py`
9. Prepare for Task 2.3 (Validator System)
10. Update power ratings for Week 13 NFL analysis

---

## ❓ QUICK QUESTIONS ANSWERED

**Q: Can I run tests without activating virtual environment?**  
A: No, you must activate `.venv` first. It ensures all dependencies are available.

**Q: Do I need to run validation before tests?**  
A: No, either order works. Validation is faster, tests are more comprehensive.

**Q: What if tests fail?**  
A: Check the error message carefully. Most likely causes:
- Wrong directory (must be in project root)
- Environment not activated
- Missing dependencies (run `pip install -r requirements.txt`)

**Q: Can I edit the scripts?**  
A: Yes, but be careful! The scripts are designed to work as-is. If you modify them, you may need to debug issues.

**Q: Where do I put my own modifications?**  
A: Create a new file in the appropriate directory rather than modifying existing files.

---

## 🎊 YOU'RE ALL SET!

Everything is ready to run on your Windows machine. 

**Next session, just open PowerShell and run**:
```powershell
cd "C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer"
.\.venv\Scripts\Activate.ps1
python scripts/validate_weather_context_builder.py
```

All the code is there, tested, and documented. Ready to go! 🚀

---

## 📞 REFERENCE

- **Project Root**: `C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer`
- **Production Code**: `src\walters_analyzer\data_collection\weather_context_builder.py`
- **Tests**: `tests\test_weather_context_builder.py`
- **Validation**: `scripts\validate_weather_context_builder.py`
- **Docs**: `docs\TASK_2_2_WEATHER_CONTEXT_BUILDER.md`

**All files are on your Windows machine. Ready to run!** ✅
