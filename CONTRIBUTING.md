### Filing New Issues

* Check that your issue is not already described in the [FAQ](docs/faq.md), [troubleshooting](docs/troubleshooting.md) docs, or an [existing issue](https://github.com/trailofbits/algo/issues)
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
* For local testing, consider using Docker or a cloud provider test instance

Thanks!
