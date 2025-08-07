# Deploy from Windows

You have three options to run Algo on Windows:

1. **PowerShell Script** (Recommended) - Automated WSL wrapper for easy use
2. **Windows Subsystem for Linux (WSL)** - Direct Linux environment access
3. **Git Bash/MSYS2** - Unix-like shell environment (limited compatibility)

## Option 1: PowerShell Script (Recommended)

The PowerShell script provides the easiest Windows experience by automatically using WSL when needed:

```powershell
git clone https://github.com/trailofbits/algo
cd algo
.\algo.ps1
```

**How it works:**
- Detects if you're already in WSL and uses the standard Unix approach
- On native Windows, automatically runs Algo via WSL (since Ansible requires Unix)
- Provides clear guidance if WSL isn't installed

**Requirements:**
- Windows Subsystem for Linux (WSL) with Ubuntu 22.04
- If WSL isn't installed, the script will guide you through installation

## Option 2: Windows Subsystem for Linux (WSL)

For users who prefer a full Linux environment or need advanced features:

### Prerequisites
* 64-bit Windows 10/11 (Anniversary update or later)

### Setup WSL
1. Install WSL from PowerShell (as Administrator):
```powershell
wsl --install -d Ubuntu-22.04
```

2. After restart, open Ubuntu and create your user account

### Install Algo in WSL
```bash
cd ~
git clone https://github.com/trailofbits/algo
cd algo
./algo
```

**Important**: Don't install Algo in `/mnt/c` directory due to file permission issues.

### WSL Configuration (if needed)

You may encounter permission issues if you clone Algo to a Windows drive (like `/mnt/c/`). Symptoms include:

- **Git errors**: "fatal: could not set 'core.filemode' to 'false'"
- **Ansible errors**: "ERROR! Skipping, '/mnt/c/.../ansible.cfg' as it is not safe to use as a configuration file"
- **SSH key errors**: "WARNING: UNPROTECTED PRIVATE KEY FILE!" or "Permissions 0777 for key are too open"

If you see these errors, configure WSL:

1. Edit `/etc/wsl.conf` to allow metadata:
```ini
[automount]
options = "metadata"
```

2. Restart WSL completely:
```powershell
wsl --shutdown
```

3. Fix directory permissions for Ansible:
```bash
chmod 744 .
```

**Why this happens**: Windows filesystems mounted in WSL (`/mnt/c/`) don't support Unix file permissions by default. Git can't set executable bits, and Ansible refuses to load configs from "world-writable" directories for security.

After deployment, copy configs to Windows:
```bash
cp -r configs /mnt/c/Users/$USER/
```

## Option 3: Git Bash/MSYS2

If you have Git for Windows installed, you can use the included Git Bash terminal:

```bash
git clone https://github.com/trailofbits/algo
cd algo
./algo
```

**Pros**: 
- Uses the standard Unix `./algo` script
- No WSL setup required
- Familiar Unix-like environment

**Cons**:
- **Limited compatibility**: Ansible may not work properly due to Windows/Unix differences
- **Not officially supported**: May encounter unpredictable issues
- Less robust than WSL or PowerShell options
- Requires Git for Windows installation

**Note**: This approach is not recommended due to Ansible's Unix requirements. Use WSL-based options instead.
