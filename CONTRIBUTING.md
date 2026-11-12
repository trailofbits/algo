### Filing New Issues

* We welcome bug reports! Before filing, a quick check of the [FAQ](docs/faq.md) or [troubleshooting](docs/troubleshooting.md) docs might have your answer
* Algo automatically installs dependencies with uv - no manual setup required
* We support modern clients: macOS 12+, iOS 15+, Windows 11+, Ubuntu 22.04+, etc.
* Supported cloud providers: DigitalOcean, AWS, Azure, GCP, Vultr, Hetzner, Linode, OpenStack, CloudStack
* If you need to file a new issue, fill out any relevant fields in the Issue Template

### Pull Requests

* Run the full linter suite: `./scripts/lint.sh`
* Test your changes on multiple platforms when possible
* Use conventional commit messages that clearly describe your changes
* Pin dependency versions rather than using ranges (e.g., `==1.2.3` not `>=1.2.0`)

### Development Setup

* Clone the repository: `git clone https://github.com/trailofbits/algo.git`
* Run Algo: `./algo` (dependencies installed automatically via uv)
* Audit and install development dependencies: `uv audit --locked && uv sync --locked --python 3.11`
* Install git hooks: `uv run --locked prek install`
* Run the same hooks as CI: `./scripts/lint.sh`. Hook tools are installed automatically.
* Run the full Python test suite: `uv run --locked pytest -q`
* Update managed hooks: `uv run --locked prek update --cooldown-days 7 --freeze`
* For local testing, consider using Docker or a cloud provider test instance

Thanks!
