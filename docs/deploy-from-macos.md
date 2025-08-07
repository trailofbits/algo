# Deploy from macOS

You can install the Algo scripts on a macOS system and use them to deploy your AlgoVPN to a cloud provider.

## Installation

Algo handles all Python setup automatically. Simply:

1. Get Algo: `git clone https://github.com/trailofbits/algo.git && cd algo`
2. Run Algo: `./algo`

The first time you run `./algo`, it will automatically install the required Python environment (Python 3.11+) using [uv](https://docs.astral.sh/uv/), a fast Python package manager. This works on all macOS versions without any manual Python installation.

## What happens automatically

When you run `./algo` for the first time:
- uv is installed automatically using curl
- Python 3.11+ is installed and managed by uv
- All required dependencies (Ansible, etc.) are installed
- Your VPN deployment begins

No manual Python installation, virtual environments, or dependency management required!
