$ErrorActionPreference = 'Continue'
$projectRoot = Split-Path -Parent $PSScriptRoot
$logDirectory = Join-Path $projectRoot 'logs'
if (-not (Test-Path -LiteralPath $logDirectory)) {
    New-Item -ItemType Directory -Path $logDirectory -ErrorAction Stop | Out-Null
}
$stamp = [DateTimeOffset]::UtcNow.ToOffset([TimeSpan]::FromHours(8)).ToString('yyyyMMdd-HHmmss-fff')
$logPath = Join-Path $logDirectory "day01-environment-$stamp.txt"
$result = & {
    "Checked at (Asia/Shanghai): $([DateTimeOffset]::UtcNow.ToOffset([TimeSpan]::FromHours(8)).ToString('o'))"
    "Project: $projectRoot"
    '=== Windows ==='
    [System.Runtime.InteropServices.RuntimeInformation]::OSDescription
    Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion' |
        Select-Object ProductName, DisplayVersion, CurrentBuild, UBR, EditionID | Format-List
    "PowerShell: $($PSVersionTable.PSVersion) $($PSVersionTable.PSEdition)"
    '=== Python and packages ==='
    Get-Command python, py -ErrorAction SilentlyContinue | Select-Object Name, Source | Format-Table
    python --version
    py -0p
    python -c "import sys,numpy,pandas,scipy,io; print('Python executable:',sys.executable); print('Python:',sys.version); print('numpy:',numpy.__version__); print('pandas:',pandas.__version__); print('scipy:',scipy.__version__); x=numpy.loadtxt(io.StringIO('0.1 0.2 0.3\n0.4 0.5 0.6\n')); y=numpy.loadtxt(io.StringIO('1\n2\n'),dtype=int); print('Synthetic whitespace text read: X=',x.shape,'y=',y.shape,'finite=',bool(numpy.isfinite(x).all())); assert x.shape == (2,3) and y.shape == (2,)"
    "Text read check exit code: $LASTEXITCODE"
    python -c "import torch; print('PyTorch:',torch.__version__); print('Bundled CUDA runtime:',torch.version.cuda); print('CUDA available:',torch.cuda.is_available()); print('GPU count:',torch.cuda.device_count()); print('cuDNN:',torch.backends.cudnn.version())"
    "PyTorch check exit code: $LASTEXITCODE"
    '=== NVIDIA driver and CUDA toolkit ==='
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
    nvidia-smi
    if (Get-Command nvcc -ErrorAction SilentlyContinue) {
        Get-Command nvcc | Select-Object Source | Format-List
        nvcc --version
    } else { 'nvcc not found on PATH' }
    '=== Git and push prerequisites ==='
    git --version
    $gitRoot = git -C $projectRoot rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -eq 0) {
        "Repository root: $gitRoot"
        git -C $projectRoot branch --show-current
        git -C $projectRoot status --short --branch
        # Strip URL userinfo and query strings before writing remote information.
        git -C $projectRoot remote -v | ForEach-Object {
            $_ -replace '(https?://)[^/\s@]+@', '$1[REDACTED]@' -replace '\?\S+', '?[REDACTED]'
        }
    } else {
        'Repository: absent; remote: N/A; branch: N/A; status: N/A'
    }
    foreach ($key in @('user.name','user.email')) {
        $configuredValue = git -C $projectRoot config --get $key
        "$key configured: $([bool]$configuredValue) (value intentionally omitted)"
    }
    $helper = git -C $projectRoot config --get credential.helper
    "Credential helper configured: $([bool]$helper)"
    "GitHub CLI available: $([bool](Get-Command gh -ErrorAction SilentlyContinue))"
    'GitHub authentication, repository permissions, and network push access: not verified.'
    'No credentials read; no remote configured; no commit, push, download, training, or package installation performed.'
    '=== Project inventory ==='
    Get-ChildItem -Force -LiteralPath $projectRoot | Select-Object Mode, Name | Format-Table
} 2>&1 | Out-String -Width 220
$stream = [System.IO.File]::Open($logPath, [System.IO.FileMode]::CreateNew)
try {
    $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes($result)
    $stream.Write($bytes, 0, $bytes.Length)
} finally { $stream.Dispose() }
Write-Output $result
Write-Output "Saved log: $logPath"
