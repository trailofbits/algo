# PowerShell script for Windows users to run Algo VPN
param(
    [Parameter(ValueFromRemainingArguments)]
    [string[]]$Arguments
)

# Check if we're actually running inside WSL (not just if WSL is available)
function Test-RunningInWSL {
    # These environment variables are only set when running inside WSL
    return $env:WSL_DISTRO_NAME -or $env:WSLENV
}

# Function to run Algo in WSL
function Invoke-AlgoInWSL {
    param($Arguments)
    
    Write-Host "NOTICE: Ansible requires a Unix-like environment and cannot run natively on Windows."
    Write-Host "Attempting to run Algo via Windows Subsystem for Linux (WSL)..."
    Write-Host ""
    
    if (-not (Get-Command wsl -ErrorAction SilentlyContinue)) {
        Write-Host "ERROR: WSL (Windows Subsystem for Linux) is not installed." -ForegroundColor Red
        Write-Host ""
        Write-Host "Algo requires WSL to run Ansible on Windows. To install WSL:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Step 1: Open PowerShell as Administrator and run:"
        Write-Host "          wsl --install -d Ubuntu-22.04" -ForegroundColor Cyan
        Write-Host "          (Note: 22.04 LTS recommended for WSL stability)" -ForegroundColor Gray
        Write-Host ""
        Write-Host "  Step 2: Restart your computer when prompted"
        Write-Host ""
        Write-Host "  Step 3: After restart, open Ubuntu from the Start menu"
        Write-Host "          and complete the initial setup (create username/password)"
        Write-Host ""
        Write-Host "  Step 4: Run this script again: .\algo.ps1"
        Write-Host ""
        Write-Host "For detailed instructions, see:" -ForegroundColor Yellow
        Write-Host "https://github.com/trailofbits/algo/blob/master/docs/deploy-from-windows.md"
        exit 1
    }
    
    # Check if any WSL distributions are installed and running
    Write-Host "Checking for WSL Linux distributions..."
    $wslList = wsl -l -v 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: WSL is installed but no Linux distributions are available." -ForegroundColor Red
        Write-Host ""
        Write-Host "You need to install Ubuntu. Run this command as Administrator:" -ForegroundColor Yellow
        Write-Host "  wsl --install -d Ubuntu-22.04" -ForegroundColor Cyan
        Write-Host "          (Note: 22.04 LTS recommended for WSL stability)" -ForegroundColor Gray
        Write-Host ""
        Write-Host "Then restart your computer and try again."
        exit 1
    }
    
    Write-Host "Successfully found WSL. Launching Algo..." -ForegroundColor Green
    Write-Host ""
    
    # Get current directory name for WSL path mapping
    $currentDir = Split-Path -Leaf (Get-Location)
    
    try {
        if ($Arguments.Count -gt 0 -and $Arguments[0] -eq "update-users") {
            $remainingArgs = $Arguments[1..($Arguments.Count-1)] -join " "
            wsl bash -c "cd /mnt/c/$currentDir 2>/dev/null || (echo 'Error: Cannot access directory in WSL. Make sure you are running from a Windows drive (C:, D:, etc.)' && exit 1) && ./algo update-users $remainingArgs"
        } else {
            $allArgs = $Arguments -join " "
            wsl bash -c "cd /mnt/c/$currentDir 2>/dev/null || (echo 'Error: Cannot access directory in WSL. Make sure you are running from a Windows drive (C:, D:, etc.)' && exit 1) && ./algo $allArgs"
        }
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host ""
            Write-Host "Algo finished with exit code: $LASTEXITCODE" -ForegroundColor Yellow
            if ($LASTEXITCODE -eq 1) {
                Write-Host "This may indicate a configuration issue or user cancellation."
            }
        }
    } catch {
        Write-Host ""
        Write-Host "ERROR: Failed to run Algo in WSL." -ForegroundColor Red
        Write-Host "Error details: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        Write-Host "Troubleshooting:" -ForegroundColor Yellow
        Write-Host "1. Make sure you're running from a Windows drive (C:, D:, etc.)"
        Write-Host "2. Try opening Ubuntu directly and running: cd /mnt/c/$currentDir && ./algo"
        Write-Host "3. See: https://github.com/trailofbits/algo/blob/master/docs/deploy-from-windows.md"
        exit 1
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
    # Check if we're actually running inside WSL
    if (Test-RunningInWSL) {
        Write-Host "Detected WSL environment. Running Algo using standard Unix approach..."
        
        # Verify bash is available (should be in WSL)
        if (-not (Get-Command bash -ErrorAction SilentlyContinue)) {
            Write-Host "ERROR: Running in WSL but bash is not available." -ForegroundColor Red
            Write-Host "Your WSL installation may be incomplete. Try running:" -ForegroundColor Yellow
            Write-Host "  wsl --shutdown" -ForegroundColor Cyan
            Write-Host "  wsl" -ForegroundColor Cyan
            exit 1
        }
        
        # Run the standard Unix algo script
        & bash -c "./algo $($Arguments -join ' ')"
        exit $LASTEXITCODE
    }
    
    # We're on native Windows - need to use WSL
    Invoke-AlgoInWSL $Arguments
    
} catch {
    Write-Host ""
    Write-Host "UNEXPECTED ERROR:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "If you continue to have issues:" -ForegroundColor Yellow
    Write-Host "1. Ensure WSL is properly installed and Ubuntu is set up"
    Write-Host "2. See troubleshooting guide: https://github.com/trailofbits/algo/blob/master/docs/deploy-from-windows.md"
    Write-Host "3. Or use WSL directly: open Ubuntu and run './algo'"
    exit 1
}