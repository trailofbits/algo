# Deploy from Windows

You have three options to run Algo on Windows:

1. **PowerShell Script** (Recommended) - Native Windows support
2. **Windows Subsystem for Linux (WSL)** - Full Linux environment  
3. **Git Bash/MSYS2** - Unix-like shell environment

## Option 1: PowerShell Script (Recommended)

The easiest way to run Algo on Windows. Simply download the repository and run:

```powershell
git clone https://github.com/trailofbits/algo
cd algo
.\algo.ps1
```

The script will automatically:
- Install the Python package manager `uv` via winget or scoop
- Set up the required Python environment
- Run Algo with full functionality

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
- May have compatibility issues with some Ansible modules
- Less robust than WSL or PowerShell options
- Requires Git for Windows installation
