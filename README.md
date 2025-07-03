# CI/CD Detector

A comprehensive tool for detecting and documenting CI/CD configurations, test suites, and deployment mechanisms across multiple git repositories. Creates a single source of truth for build, test, and deployment infrastructure to help DevOps, security, and development teams understand their complete development lifecycle.

## Features

- **Multi-Platform Support** - Works with GitHub, Bitbucket, GitLab, and other git hosting services
- **CI Tool Detection** - Identifies Bitbucket Pipelines, CircleCI, Jenkins, GitHub Actions, GitLab CI, and Buildkite
- **CD Tool Detection** - Finds Docker, Kubernetes, Terraform, Ansible, and script-based deployments
- **Test Suite Detection** - Discovers and executes PHPUnit, Pest, Dusk, pytest, Jest, Mocha, and other test frameworks
- **Coverage Analysis** - Runs test suites with coverage reporting to assess code quality
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
# Basic CI/CD detection
python3 cicd-detector.py

# Include test suite detection and execution
python3 cicd-detector.py --run-tests

# With custom options
python3 cicd-detector.py --repos-dir my-repos --output my-report.csv --run-tests
```

### 4. Review Results

Open `cicd-report.csv` to see the complete analysis with:
- Repository information and team ownership
- CI tools and configurations
- CD/deployment mechanisms
- Docker images and version information
- Test frameworks and coverage percentages
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
| `test_framework` | Test framework used | `PHPUnit`, `Jest`, `pytest` |
| `test_coverage` | Coverage percentage | `78.5`, `92.1`, `0.0` |

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
  --run-tests         Run test suites and collect coverage data
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

### Test Frameworks
- **PHP**: PHPUnit (`phpunit.xml`), Pest (`tests/Pest.php`), Laravel Dusk (`tests/Browser/`)
- **Python**: pytest (`pytest.ini`), unittest (`test_*.py` files)
- **JavaScript/Node.js**: Jest (`package.json` with jest), Mocha (`package.json` with mocha)
- **Coverage**: Automatically detects and runs coverage tools when available

### Additional Detection
- **Security scanning** (Snyk, Dependabot, etc.)
- **Monorepo structures**
- **Multi-CI setups**
- **Dockerized applications**

## Test Suite Execution

When using the `--run-tests` flag, the tool will:

1. **Detect** test frameworks in each repository
2. **Install** dependencies when possible (composer, npm, pip)
3. **Execute** test suites with coverage reporting
4. **Parse** results for test count and coverage percentage
5. **Handle** timeouts and execution errors gracefully

### Supported Test Execution

- **PHPUnit**: Runs with `composer install` + `vendor/bin/phpunit`
- **Pest**: Runs through PHPUnit integration
- **pytest**: Runs with coverage plugin when available
- **unittest**: Runs with `python -m unittest discover`
- **Jest**: Runs with `npx jest --coverage`
- **Mocha**: Runs with `npx mocha`

### Performance Considerations

- Test execution can be time-consuming for large codebases
- Use `--run-tests` only when you need coverage data
- The tool attempts to install dependencies but may fail on complex setups
- Consider running on a subset of repositories first to gauge execution time

## Sample Output

```
🔍 CI/CD Detector
==================================================
📁 Loaded 25 repositories from repos.csv
📁 Found 23 cloned repositories out of 25 total
Analyzing 25 repositories...
==================================================
[ 1/25] Analyzing api-core...
    Running tests for api-core...
    ✅ PHPUnit: 45 tests, 78.5% coverage
    CI: Bitbucket Pipelines, CD: Docker Compose
[ 2/25] Analyzing web-app...
    Running tests for web-app...
    ✅ Jest: 23 tests, 85.2% coverage
    CI: GitHub Actions, CD: Docker
[ 3/25] Analyzing legacy-app...
    Running tests for legacy-app...
    ⚠️  PHPUnit: Composer install failed...
    CI: none, CD: N/A
...

================================================================================
CI/CD ANALYSIS SUMMARY
================================================================================

📊 Total repositories analyzed: 25

👥 Team Distribution:
   backend: 8
   frontend: 6
   data: 4
   security: 7

🔧 CI Tools Distribution:
   Bitbucket Pipelines: 12
   GitHub Actions: 8
   none: 5

🚀 CD Tools Distribution:
   Docker: 15
   Docker Compose: 8
   Kubernetes: 3
   N/A: 4

🧪 Test Framework Distribution:
   PHPUnit: 8
   Jest: 6
   pytest: 4
   unittest: 2

📊 Average Test Coverage: 72.3% (20 repositories)

🎯 High Coverage Repositories (>80%):
   - web-app: 85.2%
   - api-auth: 92.1%
   - data-processor: 88.7%

✅ Report saved to cicd-report.csv
```

## Standalone Test Detection

You can also use the test detector independently:

```bash
python test_detector.py /path/to/repository
```

This will analyze a single repository and show:
- Detected test framework
- Number of tests
- Coverage percentage
- Execution success/failure

## Repository Structure

```
cicd-detector/
├── cicd-detector.py      # Main analysis script
├── test_detector.py      # Test suite detection and execution
├── clone-repos.sh        # Helper script to clone repositories
├── repos.csv            # Repository list (create this)
├── repos.csv.example    # Example repository list
├── cicd-report.csv      # Generated report
└── repos/               # Cloned repositories (auto-created)
```

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

**Test Execution Failed**
- Check if dependencies can be installed (composer, npm, pip)
- Verify test framework configuration files exist
- Consider network issues or package manager problems

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
- ✅ **No malicious code execution** - Does not run untrusted build processes  
- ✅ **Local processing** - All analysis happens locally
- ✅ **Configurable exclusions** - `.gitignore` prevents sensitive data commits
- ✅ **Open source** - Transparent and auditable code
- ✅ **Test sandboxing** - Test execution is isolated and time-limited

## Use Cases

### Security Teams
- **Vulnerability Assessment** - Identify repositories without security scanning or tests
- **Compliance Auditing** - Ensure CI/CD and testing standards are followed
- **Attack Surface Analysis** - Map all build, test, and deployment mechanisms
- **Code Quality Assessment** - Track test coverage across the organization

### DevOps Teams  
- **Infrastructure Inventory** - Document all CI/CD tools and test configurations
- **Migration Planning** - Understand current state before tool migrations
- **Standardization** - Identify inconsistencies across teams
- **Quality Metrics** - Track testing adoption and coverage trends

### Development Teams
- **Onboarding** - Help new team members understand project setups
- **Maintenance** - Track which repositories need CI/CD or test updates
- **Best Practices** - Compare configurations and coverage across projects
- **Technical Debt** - Identify repositories with poor test coverage

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

### Adding New Test Frameworks

To add support for new test frameworks:

1. Update `detect_test_framework()` in `test_detector.py`
2. Add execution logic for the new framework
3. Update documentation and examples
4. Test with sample repositories

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Changelog

### v1.1.0 - Test Suite Integration
- Added comprehensive test framework detection (PHPUnit, Pest, Dusk, pytest, Jest, Mocha)
- Implemented test execution with coverage reporting
- Enhanced CSV output with test framework and coverage columns
- Added standalone test detector utility
- Improved error handling and timeout management

### v1.0.0 - Initial Release
- Multi-platform support (GitHub, Bitbucket, GitLab)
- CSV-based repository configuration
- Comprehensive CI/CD tool detection (Pipelines, Actions, Jenkins, etc.)
- Team and priority-based analytics
- Zero external dependencies
- Open source with comprehensive documentation