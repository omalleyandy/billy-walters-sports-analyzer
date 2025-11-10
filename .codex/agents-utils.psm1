#requires -Version 7.2
    'Error'   { Write-Host $Message -ForegroundColor Red }
    'Success' { Write-Host $Message -ForegroundColor Green }
  }
}

# Repo state & header
function Get-RepoState {
  param([string]$Path)
  $sha   = (git -C $Path rev-parse --short HEAD 2>$null)
  $dirty = if ((git -C $Path status --porcelain 2>$null)) { 'dirty' } else { 'clean' }
  return [pscustomobject]@{ Sha=$sha; Dirty=$dirty }
}

function Write-RunHeader {
  param([string]$ToolName='unknown',[string]$Project=$env:WIN_PROJECT)
  $ts = (Get-Date).ToString('yyyy-MM-ddTHH:mm:sszzz')
  $state = Get-RepoState -Path $Project
  Write-Colored -Level Header -Message "[agent] ts=$ts tool=$ToolName tz=America/Los_Angeles"
  Write-Colored -Level Info   -Message "repo=omalleyandy/billy-walters-sports-analyzer@$($state.Sha) state=$($state.Dirty)"
  Write-Colored -Level Info   -Message "roots: WIN_HOME=$($env:WIN_HOME) WIN_PROJECT=$Project"
}

# Guards
function Assert-ProjectPresent { if (-not (Test-Path $env:WIN_PROJECT)) { throw "Project path missing: $env:WIN_PROJECT" } }
function Assert-Uv { if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw "uv not found. Install via winget: Astral.UV" } }

# Env checks
function Test-EnvVars {
  param([string[]]$Names)
  $missing = @()
  foreach ($n in $Names) { if (-not $env:$n) { $missing += $n } }
  return $missing
}

# JSON writer
function Write-RunMeta {
  param([string]$ToolName,[string]$Project=$env:WIN_PROJECT)
  $date = Get-Date -Format 'yyyy-MM-dd'
  $runDir = Join-Path $Project ".runs/$date"
  New-Item -ItemType Directory -Force -Path $runDir | Out-Null
  $state = Get-RepoState -Path $Project
  $meta = [ordered]@{
    tool  = $ToolName
    ts    = (Get-Date).ToString('yyyy-MM-ddTHH:mm:sszzz')
    tz    = 'America/Los_Angeles'
    repo  = 'omalleyandy/billy-walters-sports-analyzer'
    sha   = $state.Sha
    state = $state.Dirty
    roots = @{ WIN_HOME=$env:WIN_HOME; WIN_PROJECT=$Project }
  }
  $out = Join-Path $runDir "$ToolName.json"
  $meta | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $out
  Write-Colored -Level Success -Message "[post] wrote $ToolName metadata to $out"
}

# GitHub helpers (require gh or GH_TOKEN + repo)
function Invoke-GH-Comment {
  param([string]$Owner='omalleyandy',[string]$Repo='billy-walters-sports-analyzer',[int]$PR,[string]$Body)
  if (Get-Command gh -ErrorAction SilentlyContinue) {
    gh pr comment $PR --body $Body
    return
  }
  if (-not $env:GH_TOKEN) { throw 'GH_TOKEN missing and gh CLI not found.' }
  $uri = "https://api.github.com/repos/$Owner/$Repo/issues/$PR/comments"
  $headers = @{ Authorization = "Bearer $($env:GH_TOKEN)"; 'User-Agent'='codex-agent' }
  Invoke-RestMethod -Method Post -Uri $uri -Headers $headers -Body (@{ body=$Body } | ConvertTo-Json) -ContentType 'application/json'
}

function Invoke-GH-Merge {
  param([string]$Owner='omalleyandy',[string]$Repo='billy-walters-sports-analyzer',[int]$PR,[ValidateSet('merge','squash')] [string]$Method='merge')
  if (Get-Command gh -ErrorAction SilentlyContinue) {
    $flag = if ($Method -eq 'squash') { '--squash' } else { '--merge' }
    gh pr merge $PR $flag --auto --delete-branch
    return
  }
  if (-not $env:GH_TOKEN) { throw 'GH_TOKEN missing and gh CLI not found.' }
  $uri = "https://api.github.com/repos/$Owner/$Repo/pulls/$PR/merge"
  $headers = @{ Authorization = "Bearer $($env:GH_TOKEN)"; 'User-Agent'='codex-agent' }
  $payload = @{ merge_method = $Method } | ConvertTo-Json
  Invoke-RestMethod -Method Put -Uri $uri -Headers $headers -Body $payload -ContentType 'application/json'
}

Export-ModuleMember -Function *