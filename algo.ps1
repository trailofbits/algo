# PowerShell script for Windows users to run Algo VPN
param(
    [Parameter(ValueFromRemainingArguments)]
    [string[]]$Arguments
)

# Check if we're running in WSL
function Test-WSL {
    return $env:WSL_DISTRO_NAME -or $env:WSLENV -or (Get-Command wsl -ErrorAction SilentlyContinue)
}

# Function to run Algo in WSL
function Invoke-AlgoInWSL {
    param($Arguments)
    
    Write-Host "NOTICE: Ansible requires a Unix-like environment."
    Write-Host "Attempting to run Algo via Windows Subsystem for Linux (WSL)..."
    Write-Host ""
    
    if (-not (Get-Command wsl -ErrorAction SilentlyContinue)) {
        Write-Host "ERROR: WSL is not installed or not available." -ForegroundColor Red
        Write-Host ""
        Write-Host "To use Algo on Windows, you need WSL. Please:"
        Write-Host "1. Install WSL: Run 'wsl --install -d Ubuntu-22.04' in PowerShell as Administrator"
        Write-Host "2. Restart your computer when prompted"
        Write-Host "3. Set up Ubuntu and try running this script again"
        Write-Host ""
        Write-Host "Alternatively, see: https://github.com/trailofbits/algo/blob/master/docs/deploy-from-windows.md"
        exit 1
    }
    
    # Check if a default WSL distribution is set
    $wslList = wsl -l -v 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: No WSL distributions found." -ForegroundColor Red
        Write-Host "Please install a Linux distribution: wsl --install -d Ubuntu-22.04"
        exit 1
    }
    
    Write-Host "Running Algo in WSL..."
    if ($Arguments.Count -gt 0 -and $Arguments[0] -eq "update-users") {
        $remainingArgs = $Arguments[1..($Arguments.Count-1)] -join " "
        wsl bash -c "cd /mnt/c/$(pwd | Split-Path -Leaf) && ./algo update-users $remainingArgs"
    } else {
        $allArgs = $Arguments -join " "
        wsl bash -c "cd /mnt/c/$(pwd | Split-Path -Leaf) && ./algo $allArgs"
    }
}

# Function to install uv via package managers (for WSL scenarios)
function Install-UvViaPackageManager {
    Write-Host "Attempting to install uv via system package manager..."
    
    # Try winget (Windows Package Manager)
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "Using winget..."
        try {
            winget install --id=astral-sh.uv -e --silent --accept-source-agreements --accept-package-agreements
            return $true
        } catch {
            Write-Host "winget installation failed: $($_.Exception.Message)"
        }
    }
    
    # Try scoop
    if (Get-Command scoop -ErrorAction SilentlyContinue) {
        Write-Host "Using scoop..."
        try {
            scoop install uv
            return $true
        } catch {
            Write-Host "scoop installation failed: $($_.Exception.Message)"
        }
    }
    
    return $false
}

# Function to install uv via download (with user consent)
function Install-UvViaDownload {
    Write-Host ""
    Write-Host "Security Notice: uv is not available via system package managers on this system."
    Write-Host "To continue, we need to download and execute an installation script from:"
    Write-Host "  https://astral.sh/uv/install.ps1 (Windows)"
    Write-Host ""
    Write-Host "For maximum security, you can install uv manually instead:"
    $installUrl = "https://docs.astral.sh/uv/getting-started/installation/"
    Write-Host "  1. Visit: $installUrl"
    Write-Host "  2. Download the binary for your platform from GitHub releases"
    Write-Host "  3. Verify checksums and install manually"
    Write-Host "  4. Then run: .\algo.ps1"
    Write-Host ""
    
    $consent = Read-Host "Continue with script download? (y/N)"
    if ($consent -ne "y" -and $consent -ne "Y") {
        Write-Host "Installation cancelled. Please install uv manually and retry."
        exit 1
    }
    
    Write-Host "Downloading uv installation script..."
    try {
        Invoke-RestMethod https://github.com/astral-sh/uv/releases/download/0.8.5/uv-installer.ps1 | Invoke-Expression
        return $true
    } catch {
        Write-Host "Error downloading or executing uv installer: $($_.Exception.Message)"
        return $false
    }
}

# Function to refresh PATH environment variable
function Update-PathEnvironment {
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + 
                [System.Environment]::GetEnvironmentVariable("PATH", "User")
}

# Main execution
try {
    # Check if we're in WSL already
    if (Test-WSL) {
        Write-Host "Running in WSL environment, using standard approach..."
        # In WSL, we can use the normal Linux approach
        & bash -c "./algo $($Arguments -join ' ')"
        exit $LASTEXITCODE
    }
    
    # We're on native Windows - Ansible won't work directly
    # Try to use WSL instead
    Invoke-AlgoInWSL $Arguments
    
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    $manualInstallUrl = "https://docs.astral.sh/uv/getting-started/installation/"
    Write-Host "For manual installation: $manualInstallUrl"
    Write-Host "For WSL setup: https://github.com/trailofbits/algo/blob/master/docs/deploy-from-windows.md"
    exit 1
}