# SPDX-License-Identifier: AGPL-3.0-or-later
# Launch a KeralaFloodBench batch fully detached (survives the launching terminal
# or agent session ending). Win32_Process.Create starts the process from the WMI
# service, outside any job object of the caller. Always passes --resume, so the
# same command continues an interrupted batch.
#
# Usage (from the repo root, PowerShell):
#   .\kerala\tools\launch_detached.ps1 -Model pc-gptoss20b -Batch matrix_gptoss_v1
#   .\kerala\tools\launch_detached.ps1 -Model cloud-flashlite -Batch matrix_cloud_v1
param(
    [Parameter(Mandatory = $true)][string]$Model,
    [Parameter(Mandatory = $true)][string]$Batch,
    [string]$Questions = "P01,P02,P03,P04,P05,P06,P07,P08,P09,P10,P11,P12,C01,C02,C03,C04,C05,C06,C07,C08",
    [string]$Arms = "noparam,inline,pack"
)
$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$logs = Join-Path $root "logs\claude_runs"
New-Item -ItemType Directory -Force $logs | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$out = Join-Path $logs "$Batch.$stamp.out.log"
$err = Join-Path $logs "$Batch.$stamp.err.log"
$python = Join-Path $root ".venv\Scripts\python.exe"
$cmd = "cmd.exe /c set PYTHONIOENCODING=utf-8&& `"$python`" -u -m kerala.bench.run_bench --model $Model --batch $Batch --questions $Questions --arms $Arms --resume > `"$out`" 2> `"$err`""
$result = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = $cmd; CurrentDirectory = $root }
if ($result.ReturnValue -ne 0) { throw "Win32_Process.Create failed with code $($result.ReturnValue)" }
"Launched PID $($result.ProcessId) (cmd wrapper) at $(Get-Date -Format s)"
"stdout: $out"
"stderr: $err"
