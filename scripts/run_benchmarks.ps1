param (
    [string]$TestType = "all",
    [string]$TargetHost = "http://localhost:8000"
)

# 1. Find Python
$pythonPath = Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
if (-not $pythonPath) {
    # Check common paths
    $commonPaths = @(
        "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python312\python.exe",
        "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311\python.exe",
        "C:\Python312\python.exe",
        "C:\Python311\python.exe"
    )
    foreach ($path in $commonPaths) {
        if (Test-Path $path) {
            $pythonPath = $path
            break
        }
    }
}

if (-not $pythonPath) {
    Write-Error "Python not found! Please install Python 3.10+ and add it to PATH."
    exit 1
}

Write-Host "Using Python at: $pythonPath" -ForegroundColor Green

# 2. Check/Install Dependencies
Write-Host "Checking dependencies..."
& $pythonPath -m pip install locust pytest pandas requests

# 3. Helpers
function Run-Locust {
    param($Users, $SpawnRate, $Time, $Csv)
    Write-Host "Running Locust: $Users users, $SpawnRate spawn rate, $Time duration against $TargetHost..."
    & $pythonPath -m locust -f tests/load/locustfile.py --headless -u $Users -r $SpawnRate --run-time $Time --csv $Csv --host $TargetHost
}

function Generate-Report {
    Write-Host "Generating Report..."
    & $pythonPath ops/benchmarks/generate_report.py
}

# 4. Run Tests
if (-not $env:WM_TOKEN) { $env:WM_TOKEN = "changeme" }
if (-not $env:WM_WORKSPACE) { $env:WM_WORKSPACE = "demo" }
$env:TARGET_HOST = $TargetHost

if ($TestType -eq "load-test" -or $TestType -eq "all") {
    Run-Locust -Users 10 -SpawnRate 2 -Time "30s" -Csv "ops/benchmarks/results/load_run"
    Generate-Report
}

if ($TestType -eq "stress-test" -or $TestType -eq "all") {
    Write-Host "Running Stress Test..."
    & $pythonPath tests/load/stress_test.py
}

if ($TestType -eq "soak-test" -or $TestType -eq "all") {
    Write-Host "Running Soak Test..."
    & $pythonPath tests/load/soak_test.py
}

if ($TestType -eq "multitenant" -or $TestType -eq "all") {
    Write-Host "Running Multi-tenant Test..."
    & $pythonPath -m pytest tests/multitenant/test_isolation.py
}

if ($TestType -eq "resilience" -or $TestType -eq "all") {
    Write-Host "Running Resilience Test..."
    & $pythonPath -m pytest tests/resilience/test_chaos.py
}

if ($TestType -eq "security" -or $TestType -eq "all") {
    Write-Host "Running Security Test..."
    & $pythonPath -m pytest tests/security/test_smoke.py
}

Write-Host "Done!" -ForegroundColor Green
