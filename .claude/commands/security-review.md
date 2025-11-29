Perform a security review of the codebase, checking for common vulnerabilities and security best practices.

This command runs security checks on the Billy Walters Sports Analyzer codebase.

**What This Command Does:**

1. **Git Status Check**
   - Verify working tree status
   - Check for uncommitted sensitive files
   - Review .gitignore coverage

2. **Environment Security**
   - Verify .env files are gitignored
   - Check for hardcoded credentials
   - Validate API key handling

3. **Code Security Patterns**
   - SQL injection prevention (parameterized queries)
   - Input validation patterns
   - Authentication handling

4. **Dependency Security**
   - Check for known vulnerabilities
   - Review dependency versions

**Usage:**
```bash
/security-review
```

**Security Checklist:**

- [ ] No API keys in source code
- [ ] .env files gitignored
- [ ] No hardcoded passwords
- [ ] SQL queries parameterized
- [ ] User input validated
- [ ] Dependencies up to date

**Files to Review:**
- `.env.example` - Template without real values
- `.gitignore` - Sensitive file exclusions
- `src/data/*.py` - API clients
- `src/db/*.py` - Database queries

**Expected Output:**
- Security findings summary
- Risk assessment (LOW/MEDIUM/HIGH)
- Recommendations for remediation
