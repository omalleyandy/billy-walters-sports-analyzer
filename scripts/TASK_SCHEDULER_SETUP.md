# Windows Task Scheduler Setup - Simplified Method

## Method 1: Create Task Without Password Requirement

This method avoids the MMC error by using "Run only when user is logged in".

### Step-by-Step Instructions:

1. **Open Task Scheduler as Administrator**
   - Press `Win + S` and search "Task Scheduler"
   - Right-click and select "Run as administrator"

2. **Create Basic Task**
   - In the Actions panel (right side), click "Create Basic Task..."
   - Name: `Billy Walters NFL Weekly Update`
   - Description: `Automatically updates NFL power ratings every Tuesday at 6 AM`
   - Click Next

3. **Set Trigger**
   - Select "Weekly"
   - Click Next
   - Start: Choose next Tuesday (or today's date)
   - Time: `6:00:00 AM`
   - Recur every: `1` weeks
   - Check only: **Tuesday**
   - Click Next

4. **Set Action**
   - Select "Start a program"
   - Click Next
   - Program/script:
     ```
     C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer\scripts\weekly_power_ratings_update_auto.bat
     ```
   - Start in:
     ```
     C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer
     ```
   - Click Next

5. **Finish - IMPORTANT**
   - **CHECK** the box: "Open the Properties dialog for this task when I click Finish"
   - Click Finish

6. **Configure Properties (This will open automatically)**

   **General Tab:**
   - Under "Security options":
     - Select: **"Run only when user is logged in"** (avoids password prompt)
     - Check: "Run with highest privileges"

   **Triggers Tab:**
   - Select the trigger and click Edit
   - Under "Advanced settings":
     - Check "Enabled"
     - Stop task if it runs longer than: `2 hours`
   - Click OK

   **Conditions Tab:**
   - Under "Power":
     - **UNCHECK** "Start the task only if the computer is on AC power"
     - **UNCHECK** "Stop if the computer switches to battery power"
   - Under "Network":
     - **CHECK** "Start only if the following network connection is available"
     - Select: **Any connection**

   **Settings Tab:**
   - Check: "Allow task to be run on demand"
   - Check: "Run task as soon as possible after a scheduled start is missed"
   - Check: "If the task fails, restart every": `15 minutes`, Attempts: `3`
   - If the running task does not end when requested, force it to stop: **Checked**
   - If the task is already running: "Do not start a new instance"

   - Click **OK**

7. **Test the Task**
   - In Task Scheduler Library, find "Billy Walters NFL Weekly Update"
   - Right-click and select **"Run"**
   - Status should change to "Running" then "Ready"
   - Check "Last Run Result" column - should show `(0x0)` for success

---

## Method 2: Using Command Line (Alternative)

If the GUI continues to have issues, create the task via PowerShell:

```powershell
# Run PowerShell as Administrator
# Copy and paste this entire block:

$action = New-ScheduledTaskAction -Execute "C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer\scripts\weekly_power_ratings_update_auto.bat" -WorkingDirectory "C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer"

$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Tuesday -At 6:00AM

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 15)

$principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType Interactive -RunLevel Highest

Register-ScheduledTask -TaskName "Billy Walters NFL Weekly Update" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Automatically updates NFL power ratings every Tuesday at 6 AM"
```

This creates the task with:
- Weekly trigger (Tuesday 6 AM)
- Run with highest privileges
- Restart on failure (3 attempts)
- Run on battery power

---

## Troubleshooting

### Error: "MMC has detected an error in a snap-in"
**Solution**: Use Method 1 with "Run only when user is logged in" OR use Method 2 (PowerShell)

### Error: Task created but won't run
**Check**:
1. Verify batch file path is correct
2. Ensure Task Scheduler service is running:
   - Press `Win + R`, type `services.msc`
   - Find "Task Scheduler"
   - Status should be "Running"

### Error: Task runs but shows error code
**Check Last Run Result**:
- `(0x0)` = Success
- `(0x1)` = General error (check permissions)
- `(0xFF)` = Application error (test batch file manually)

**Manual Test**:
```cmd
cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer
scripts\weekly_power_ratings_update_auto.bat
```

---

## Verification

After creating the task, verify it's working:

1. **Manual Test Run**:
   - Task Scheduler → Right-click task → Run
   - Check `scripts\update_log.txt` for new entry

2. **Check Log File**:
   ```
   C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer\scripts\update_log.txt
   ```
   Should contain: `11/01/2025 [time] - Week [N] - SUCCESS`

3. **Check Power Ratings Updated**:
   ```
   C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer\data\power_ratings\team_ratings.json
   ```
   File modified timestamp should be recent

---

## Notes

- **"Run only when user is logged in"** means the task only runs if you're logged into Windows (not locked/logged out)
- **"Run whether user is logged on or not"** requires a password and can run when logged out, but often causes the MMC error
- For weekly NFL updates, "Run only when user is logged in" is usually fine since you'll likely be logged in on Tuesday mornings
- The task will still run if the computer is locked, just not if you're completely logged out
