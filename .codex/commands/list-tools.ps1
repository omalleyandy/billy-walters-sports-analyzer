$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../hooks/pre_tool.ps1" -ToolName 'list-tools'
$cmdDir = Join-Path $PSScriptRoot '.'
Get-ChildItem -Path $cmdDir -Filter *.ps1 -File | ForEach-Object {
  $name = $_.BaseName
  if ($name -in @('list-tools')) { return }
  $first = (Get-Content $_.FullName -TotalCount 3) -join ' '
  $desc = if ($first -match '#\s*(.*)$') { $Matches[1] } else { '' }
  Write-Host ("- {0}{1}" -f $name, $(if($desc){" — $desc"} else {''}))
}
. "$PSScriptRoot/../hooks/post_tool.ps1" -ToolName 'list-tools'