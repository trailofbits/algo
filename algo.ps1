# PowerShell script for Windows users to run Algo VPN
param(
    [Parameter(ValueFromRemainingArguments)]
    [string[]]$Arguments
)

# Function to install uv via package managers
function Install-UvViaPackageManager {
    Write-Host "Attempting to install uv via system package manager..."
    
    # Try winget (Windows Package Manager)
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "Using winget..."
        try {
            winget install --id=astral-sh.uv -e --silent
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
    Write-Host "⚠️  SECURITY NOTICE ⚠️"
    Write-Host "uv is not available via system package managers on this system."
    Write-Host "To continue, we need to download and execute an installation script from:"
    Write-Host "  https://astral.sh/uv/install.ps1 (Windows)"
    Write-Host ""
    Write-Host "For maximum security, you can install uv manually instead:"
    Write-Host "  1. Visit: https://docs.astral.sh/uv/getting-started/installation/"
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
    # Check if uv is installed
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host "uv (Python package manager) not found. Installing..."
        
        # Try package managers first (most secure)
        $packageInstalled = Install-UvViaPackageManager
        
        # Fall back to download if package managers failed
        if (-not $packageInstalled) {
            $downloadInstalled = Install-UvViaDownload
            if (-not $downloadInstalled) {
                throw "uv installation failed"
            }
        }
        
        # Refresh PATH to find uv
        Update-PathEnvironment
        
        # Verify installation worked
        if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
            throw "uv installation failed. Please restart your terminal and try again."
        }
        
        Write-Host "✓ uv installed successfully!"
    }
    
    # Run the appropriate playbook
    if ($Arguments.Count -gt 0 -and $Arguments[0] -eq "update-users") {
        $remainingArgs = $Arguments[1..($Arguments.Count-1)]
        & uv run ansible-playbook users.yml @remainingArgs -t update-users
    } else {
        & uv run ansible-playbook main.yml @Arguments
    }
    
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Or install manually from: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
}