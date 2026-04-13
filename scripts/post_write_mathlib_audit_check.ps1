$ErrorActionPreference = "Stop"

$pluginRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$workspaceRoot = (Resolve-Path (Join-Path $pluginRoot "..\\..")).Path
$requiredSections = @(
  "Proposed architecture",
  "Formal evidence from mathlib",
  "Engineering inference built on top of formal facts",
  "Gaps requiring benchmarks or papers",
  "Risks"
)

function Write-Status([string]$message) {
  Write-Host "[mathlib-ml-arch] $message"
}

function Get-CandidateReportsDirs {
  $dirs = @(
    (Join-Path $pluginRoot "reports"),
    (Join-Path $workspaceRoot "reports")
  ) | Where-Object { Test-Path -LiteralPath $_ }

  return $dirs | ForEach-Object { (Resolve-Path -LiteralPath $_).Path } | Select-Object -Unique
}

function Get-LatestReport([string[]]$candidateDirs) {
  $files = foreach ($dir in $candidateDirs) {
    Get-ChildItem -Path $dir -File -ErrorAction SilentlyContinue |
      Where-Object { $_.Name -eq "report.md" -or $_.Name -like "architecture_audit_report*.md" }
  }

  return $files |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
}

$candidateDirs = @(Get-CandidateReportsDirs)
if (-not $candidateDirs) {
  Write-Status "No reports directory yet."
  exit 0
}

$report = Get-LatestReport $candidateDirs

if (-not $report) {
  Write-Status "No report.md or architecture_audit_report*.md found."
  exit 0
}

$reportContent = Get-Content -LiteralPath $report.FullName -Raw
$missingSections = @()
foreach ($section in $requiredSections) {
  if ($reportContent -notmatch [regex]::Escape($section)) {
    $missingSections += $section
  }
}

$evidence = Get-ChildItem -Path $report.DirectoryName -Filter "evidence.json" -File -ErrorAction SilentlyContinue |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1

$evidenceIssues = @()
if (-not $evidence) {
  $evidenceIssues += "Missing evidence.json"
} else {
  try {
    $payload = Get-Content -LiteralPath $evidence.FullName -Raw | ConvertFrom-Json
  } catch {
    $evidenceIssues += "evidence.json is not valid JSON"
    $payload = $null
  }

  if ($null -ne $payload) {
    $records = @()
    if ($payload -is [System.Array]) {
      $records = $payload
    } elseif ($payload.PSObject.Properties.Name -contains "records") {
      $records = @($payload.records)
    } elseif ($payload.PSObject.Properties.Name -contains "claims") {
      $records = @($payload.claims)
    } else {
      $evidenceIssues += "evidence.json should be an array or expose records/claims"
    }

    $requiredFields = @(
      "name",
      "import_path",
      "plain_language_meaning",
      "supported_subclaim",
      "unsupported_boundary",
      "claim_label"
    )

    foreach ($record in $records) {
      foreach ($field in $requiredFields) {
        if (-not ($record.PSObject.Properties.Name -contains $field)) {
          $evidenceIssues += "Missing field '$field' in evidence record"
        }
      }
    }
  }
}

if ($missingSections.Count -gt 0 -or $evidenceIssues.Count -gt 0) {
  Write-Status "Audit bundle warnings for $($report.Name):"
  foreach ($section in $missingSections) {
    Write-Status "  missing section: $section"
  }
  foreach ($issue in $evidenceIssues) {
    Write-Status "  evidence issue: $issue"
  }
  exit 0
}

Write-Status "Audit bundle looks structurally complete: $($report.Name)"
exit 0
