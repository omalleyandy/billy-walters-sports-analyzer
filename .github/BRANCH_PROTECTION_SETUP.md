# Branch Protection Setup Guide

## Overview

Branch protection rules ensure that all code merged into `main` meets quality standards by requiring CI checks to pass and preventing accidental force pushes.

## Step-by-Step Setup

### 1. Navigate to Branch Protection Settings

1. Go to your GitHub repository: https://github.com/omalleyandy/billy-walters-sports-analyzer
2. Click on **Settings** (top navigation bar)
3. In the left sidebar, click **Branches** under "Code and automation"
4. Click **Add branch protection rule** (or **Add rule**)

### 2. Configure Branch Name Pattern

- **Branch name pattern**: Enter `main`
  - This applies the rule to your main branch

### 3. Enable Required Settings

Check the following boxes:

#### Require a pull request before merging
- Check this box
- **Required approvals**: Set to `1` (or higher if you have team members)
- Optional: Check "Dismiss stale pull request approvals when new commits are pushed"

#### Require status checks to pass before merging
- Check this box
- Check "Require branches to be up to date before merging"
- In the search box, type and select each of these status checks:
  - `Test (ubuntu-latest, 3.11)` - Ubuntu Python 3.11 tests
  - `Test (ubuntu-latest, 3.12)` - Ubuntu Python 3.12 tests
  - `Test (windows-latest, 3.11)` - Windows Python 3.11 tests
  - `Test (windows-latest, 3.12)` - Windows Python 3.12 tests
  - `Lint and Format` - Ruff formatting and linting
  - `Type Check` - Pyright type checking
  - `Security Scan` - Security scanning

**Note**: These checks will only appear in the dropdown AFTER the first CI run completes. You may need to:
1. Save the rule with just the basic settings first
2. Wait for the CI workflow to complete (check Actions tab)
3. Come back and add the specific status checks

#### Require conversation resolution before merging
- Optional but recommended: Check this box
- Ensures all PR comments are addressed before merging

#### Do not allow bypassing the above settings
- Check this box
- Prevents even administrators from bypassing these rules
- **Important**: Only check this if you're comfortable with strict enforcement

#### Additional Recommended Settings

- **Require signed commits**: Optional, enhances security
- **Require linear history**: Optional, keeps commit history clean
- **Include administrators**: Recommended - applies rules to everyone including admins

### 4. Save Changes

Click **Create** (or **Save changes** if editing existing rule)

## Verification

After setup, verify the protection is active:

1. Go to your repository's main page
2. Look for a shield icon next to the branch name dropdown
3. Try to push directly to main - it should be blocked

## Working with Branch Protection

### Normal Workflow

1. Create a feature branch: `git checkout -b feat/my-feature`
2. Make changes and commit
3. Push branch: `git push origin feat/my-feature`
4. Open a Pull Request on GitHub
5. Wait for all CI checks to pass (green checkmarks)
6. Request review (if required)
7. Merge the PR once approved and all checks pass

### If CI Checks Fail

1. Review the failed check in the PR
2. Fix the issue locally on your feature branch
3. Commit and push the fix
4. CI will automatically re-run
5. Merge once all checks pass

## Troubleshooting

### Status checks not appearing in dropdown

**Problem**: After enabling "Require status checks to pass before merging", the specific checks don't appear in the search box.

**Solution**:
1. Go to the **Actions** tab in your repository
2. Wait for the CI workflow to complete at least once
3. Return to branch protection settings
4. The checks should now appear in the dropdown

### Can't push directly to main anymore

**This is expected behavior!** Branch protection is working correctly.

**Solution**:
1. Use feature branches for all work
2. Create pull requests to merge into main
3. This ensures all code is reviewed and tested

### Need to bypass protection temporarily

**Not recommended**, but if absolutely necessary:
1. Go to Settings > Branches
2. Edit the branch protection rule
3. Temporarily uncheck "Do not allow bypassing the above settings"
4. Make your change
5. **Immediately re-enable the protection**

## Benefits

With branch protection enabled:

- All code is automatically tested before merge
- Code quality standards are enforced
- Prevents accidental force pushes to main
- Creates audit trail through pull requests
- Reduces bugs in production code
- Ensures team collaboration and code review

## Next Steps

After setting up branch protection:

1. Test the workflow by creating a test PR
2. Verify all CI checks run and pass
3. Document the process for team members
4. Consider adding CODEOWNERS file for automatic reviewers
