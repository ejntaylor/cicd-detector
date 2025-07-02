# CI/CD Detector

A comprehensive tool for detecting and documenting CI/CD configurations across multiple git repositories. Creates a single source of truth for build and deployment mechanisms to help DevOps, security, and development teams understand their infrastructure landscape.

## Features

- **Multi-Platform Support** - Works with GitHub, Bitbucket, GitLab, and other git hosting services
- **CI Tool Detection** - Identifies Bitbucket Pipelines, CircleCI, Jenkins, GitHub Actions, GitLab CI, and Buildkite
- **CD Tool Detection** - Finds Docker, Kubernetes, Terraform, Ansible, and script-based deployments
- **Ownership Tracking** - Extracts team and contact information from CODEOWNERS and README files
- **Configurable** - CSV-based repository configuration with team and priority metadata
- **Zero Dependencies** - Pure Python with no external dependencies required

## Quick Start

### 1. Setup Repository List

Create a `repos.csv` file with your repositories:

```csv
repo_name,team,priority,notes
my-api,backend,high,Core API service
my-frontend,frontend,high,Main web application
my-tool,devops,medium,Internal tooling
```

### 2. Clone Repositories

```bash
# Clone all repositories from your organization
./clone-repos.sh --git-host github.com --org-name myorg

# Or use Bitbucket
./clone-repos.sh --git-host bitbucket.org --org-name myorg

# Force HTTPS if SSH isn't working
./clone-repos.sh --git-host github.com --org-name myorg --https
```

### 3. Analyze CI/CD Configurations

```bash
# Generate the CI/CD documentation
python3 cicd-detector.py

# With custom options
python3 cicd-detector.py --repos-dir my-repos --output my-report.csv
```

### 4. Review Results

Open `cicd-report.csv` to see the complete analysis with:
- Repository information and team ownership
- CI tools and configurations
- CD/deployment mechanisms
- Docker images and version information
- Additional notes about testing, security scanning, etc.

## Output Format

The generated report includes these columns:

| Column | Description | Example Values |
|--------|-------------|----------------|
| `repo_name` | Repository identifier | `my-api`, `my-frontend` |
| `team` | Owning team | `backend`, `frontend`, `devops` |
| `priority` | Business priority | `critical`, `high`, `medium`, `low` |
| `ci_tool` | Primary CI system | `GitHub Actions`, `Bitbucket Pipelines` |
| `cd_tool` | Deployment method | `Docker`, `Kubernetes`, `Terraform` |
| `version_plan` | CI environment info | `node:18`, `ubuntu-latest` |
| `contact` | Owner information | `@myorg/backend`, `team@example.com` |
| `notes` | Additional context | `Dockerized; Tests; Multi-CI` |

## Installation

### Prerequisites

- Python 3.6 or higher
- Git
- SSH key configured for your git hosting service (recommended)

### Clone and Setup

```bash
git clone https://github.com/ejntaylor/cicd-detector
cd cicd-detector
chmod +x *.sh *.py
```

No additional Python packages required!

## Configuration

### Repository CSV Format

The `repos.csv` file supports these columns:

- **repo_name** (required) - Repository name without organization
- **team** (optional) - Owning team or department
- **priority** (optional) - Business priority level
- **notes** (optional) - Additional context or description

### Command Line Options

#### Clone Script Options

```bash
./clone-repos.sh [OPTIONS]

Options:
  --repos-csv FILE    CSV file with repository list (default: repos.csv)
  --repos-dir DIR     Clone destination directory (default: repos)
  --git-host HOST     Git hosting service (default: bitbucket.org)
  --org-name ORG      Organization/user name (required)
  --https             Use HTTPS instead of SSH
  --help              Show help message
```

#### Detector Options

```bash
python3 cicd-detector.py [OPTIONS]

Options:
  --repos-dir DIR     Repository directory (default: repos)
  --repos-csv FILE    Repository CSV file (default: repos.csv)
  --output FILE       Output CSV file (default: cicd-report.csv)
  --git-host HOST     Git hosting service (default: bitbucket.org)
  --org-name ORG      Organization name
  --help              Show help message
```

## CI/CD Tools Detected

### Continuous Integration
- **Bitbucket Pipelines** (`bitbucket-pipelines.yml`)
- **GitHub Actions** (`.github/workflows/*.yml`)
- **CircleCI** (`.circleci/config.yml`)
- **Jenkins** (`Jenkinsfile`)
- **GitLab CI** (`.gitlab-ci.yml`)
- **Buildkite** (`.buildkite/`)

### Continuous Deployment
- **Docker** (`Dockerfile`, `docker-compose.yml`)
- **Kubernetes** (`k8s/`, `kubernetes/`)
- **Terraform** (`terraform/`, `*.tf` files)
- **Ansible** (`ansible/`, playbooks)
- **Serverless** (`serverless.yml`)
- **Script-based** (`deploy.sh`, custom scripts)

### Additional Detection
- **Testing frameworks** (Jest, PHPUnit, pytest, etc.)
- **Security scanning** (Snyk, Dependabot, etc.)
- **Monorepo structures**
- **Multi-CI setups**

## Troubleshooting

### Authentication Issues

Run the diagnostic script to check connectivity and authentication:

```bash
./diagnose-git-access.sh --git-host github.com --org-name myorg --test-repo myrepo
```

### Common Issues

**SSH Authentication Failed**
- Add your SSH key to your git hosting service
- Test with: `ssh -T git@github.com`

**Repository Not Found**
- Verify repository names in `repos.csv`
- Check organization name and permissions
- Ensure repositories exist and are accessible

**HTTPS Authentication**
- Use app passwords or personal access tokens
- Configure git credentials helper

### Getting Help

1. Run diagnostic script for connectivity issues
2. Check the troubleshooting section
3. Verify CSV file format and repository names
4. Test with a single repository first

## Security Considerations

This tool is designed for defensive security purposes:

- ✅ **Read-only analysis** - Only examines configuration files
- ✅ **No code execution** - Does not run build processes  
- ✅ **Local processing** - All analysis happens locally
- ✅ **Configurable exclusions** - `.gitignore` prevents sensitive data commits
- ✅ **Open source** - Transparent and auditable code

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

### Adding New CI/CD Tools

To add support for new tools:

1. Update `detect_ci_tool()` or `detect_cd_tool()` methods
2. Add file/directory patterns to check
3. Update documentation
4. Test with sample repositories

## Use Cases

### Security Teams
- **Vulnerability Assessment** - Identify repositories without security scanning
- **Compliance Auditing** - Ensure CI/CD standards are followed
- **Attack Surface Analysis** - Map all build and deployment mechanisms

### DevOps Teams  
- **Infrastructure Inventory** - Document all CI/CD tools and configurations
- **Migration Planning** - Understand current state before tool migrations
- **Standardization** - Identify inconsistencies across teams

### Development Teams
- **Onboarding** - Help new team members understand project setups
- **Maintenance** - Track which repositories need CI/CD updates
- **Best Practices** - Compare configurations across projects

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Changelog

### v1.0.0 - Initial Release
- Multi-platform support (GitHub, Bitbucket, GitLab)
- CSV-based repository configuration
- Comprehensive CI/CD tool detection (Pipelines, Actions, Jenkins, etc.)
- Team and priority-based analytics
- Zero external dependencies
- Open source with comprehensive documentation