#!/usr/bin/env python3
"""
CI/CD Detector
Detects and analyzes CI/CD configurations across git repositories without external dependencies
"""

import os
import csv
import re
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
from test_detector import TestSuiteDetector


class CICDAnalyzer:
    def __init__(self, repos_dir: str = "repos", repos_csv: str = "repos.csv", git_host: str = "bitbucket.org", org_name: str = None, run_tests: bool = False):
        self.repos_dir = Path(repos_dir)
        self.repos_csv = repos_csv
        self.git_host = git_host
        self.org_name = org_name
        self.run_tests = run_tests
        self.repositories = self.load_repositories()
        self.test_detector = TestSuiteDetector() if run_tests else None
        
    def load_repositories(self) -> List[Dict]:
        """Load repository list from CSV file."""
        repositories = []
        
        if not Path(self.repos_csv).exists():
            print(f"❌ Repository CSV file '{self.repos_csv}' not found!")
            print("Please create a CSV file with columns: repo_name,team,priority,notes")
            return []
            
        try:
            with open(self.repos_csv, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if 'repo_name' in row and row['repo_name'].strip():
                        repositories.append({
                            'name': row['repo_name'].strip(),
                            'team': row.get('team', '').strip(),
                            'priority': row.get('priority', '').strip(),
                            'notes': row.get('notes', '').strip()
                        })
                        
            print(f"📁 Loaded {len(repositories)} repositories from {self.repos_csv}")
            return repositories
            
        except Exception as e:
            print(f"❌ Error reading {self.repos_csv}: {e}")
            return []
        
    def extract_image_from_bitbucket_pipelines(self, file_path: Path) -> str:
        """Extract Docker image from bitbucket-pipelines.yml without YAML parser."""
        try:
            content = file_path.read_text()
            
            # Look for 'image:' lines
            image_matches = re.findall(r'^\s*image:\s*(.+)$', content, re.MULTILINE)
            
            if image_matches:
                # Clean up the image name (remove quotes, comments)
                image = image_matches[0].strip()
                image = re.sub(r'["\']', '', image)  # Remove quotes
                image = re.sub(r'\s*#.*$', '', image)  # Remove comments
                return image.strip()
                
            return "default"
        except Exception as e:
            return f"parse_error"
            
    def detect_ci_tool(self, repo_path: Path) -> Tuple[str, str]:
        """Detect primary CI tool and version/configuration details."""
        # Bitbucket Pipelines
        bb_pipeline = repo_path / "bitbucket-pipelines.yml"
        if bb_pipeline.exists():
            image = self.extract_image_from_bitbucket_pipelines(bb_pipeline)
            return "Bitbucket Pipelines", image
        
        # CircleCI
        circleci_config = repo_path / ".circleci" / "config.yml"
        if circleci_config.exists():
            return "CircleCI", "config.yml"
            
        # Jenkins
        if (repo_path / "Jenkinsfile").exists():
            return "Jenkins", "Jenkinsfile"
            
        # GitHub Actions (in case of mirrors)
        gh_workflows = repo_path / ".github" / "workflows"
        if gh_workflows.exists() and any(gh_workflows.glob("*.yml")):
            workflows = list(gh_workflows.glob("*.yml"))
            return "GitHub Actions", f"{len(workflows)} workflows"
                
        # GitLab CI
        if (repo_path / ".gitlab-ci.yml").exists():
            return "GitLab CI", ".gitlab-ci.yml"
            
        # Buildkite
        if (repo_path / ".buildkite").exists():
            return "Buildkite", ".buildkite"
            
        return "none", ""
        
    def detect_cd_tool(self, repo_path: Path) -> str:
        """Detect primary CD tool."""
        found_tools = []
        
        # Check for deployment files and directories
        deploy_indicators = {
            "deploy.sh": "Script-based",
            "docker-compose.yml": "Docker Compose",
            "docker-compose.yaml": "Docker Compose", 
            "Dockerfile": "Docker",
            "serverless.yml": "Serverless",
            "serverless.yaml": "Serverless"
        }
        
        for indicator, tool in deploy_indicators.items():
            if (repo_path / indicator).exists():
                if tool not in found_tools:
                    found_tools.append(tool)
        
        # Check for directories
        deploy_dirs = {
            "terraform": "Terraform",
            "tf": "Terraform", 
            "ansible": "Ansible",
            "k8s": "Kubernetes",
            "kubernetes": "Kubernetes",
            ".ci": "CI Scripts"
        }
        
        for dir_name, tool in deploy_dirs.items():
            if (repo_path / dir_name).exists():
                if tool not in found_tools:
                    found_tools.append(tool)
                    
        # Check CI files for deployment mentions
        ci_files = [
            repo_path / "bitbucket-pipelines.yml",
            repo_path / ".circleci" / "config.yml",
            repo_path / "Jenkinsfile"
        ]
        
        for ci_file in ci_files:
            if ci_file.exists():
                try:
                    content = ci_file.read_text().lower()
                    if "terraform" in content and "Terraform" not in found_tools:
                        found_tools.append("Terraform")
                    if "kubectl" in content and "Kubernetes" not in found_tools:
                        found_tools.append("Kubernetes")
                    if "docker push" in content and "Docker" not in found_tools:
                        found_tools.append("Docker")
                except:
                    pass
                    
        return ", ".join(found_tools) if found_tools else "N/A"
        
    def get_ownership_info(self, repo_path: Path) -> str:
        """Extract ownership information from CODEOWNERS or other sources."""
        # Check CODEOWNERS files
        codeowners_files = [
            repo_path / "CODEOWNERS",
            repo_path / ".github" / "CODEOWNERS",
            repo_path / "docs" / "CODEOWNERS"
        ]
        
        for codeowners in codeowners_files:
            if codeowners.exists():
                try:
                    content = codeowners.read_text()
                    # Extract team/user mentions (@ mentions)
                    mentions = re.findall(r'@[\w-]+(?:/[\w-]+)?', content)
                    if mentions:
                        # Remove duplicates and limit to first 3
                        unique_mentions = list(dict.fromkeys(mentions))[:3]
                        return ", ".join(unique_mentions)
                except:
                    pass
                    
        # Check README for contact info
        readme_files = [
            repo_path / "README.md",
            repo_path / "README.rst", 
            repo_path / "README.txt"
        ]
        
        for readme in readme_files:
            if readme.exists():
                try:
                    content = readme.read_text()
                    # Look for email patterns
                    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
                    if emails:
                        return emails[0]
                        
                    # Look for Slack channel mentions
                    slack_channels = re.findall(r'#[\w-]+', content)
                    if slack_channels:
                        return slack_channels[0]
                except:
                    pass
                    
        return "Unknown"
        
    def get_additional_notes(self, repo_path: Path) -> str:
        """Generate concise notes about the repository's build setup."""
        notes = []
        
        # Check for multiple CI tools
        ci_count = 0
        ci_tools = []
        
        if (repo_path / "bitbucket-pipelines.yml").exists():
            ci_count += 1
            ci_tools.append("BB")
        if (repo_path / ".circleci" / "config.yml").exists():
            ci_count += 1
            ci_tools.append("Circle")
        if (repo_path / "Jenkinsfile").exists():
            ci_count += 1
            ci_tools.append("Jenkins")
        if (repo_path / ".github" / "workflows").exists():
            ci_count += 1
            ci_tools.append("GHA")
        if (repo_path / ".gitlab-ci.yml").exists():
            ci_count += 1
            ci_tools.append("GitLab")
            
        if ci_count > 1:
            notes.append(f"Multi-CI: {','.join(ci_tools)}")
            
        # Check for Docker
        if (repo_path / "Dockerfile").exists():
            notes.append("Dockerized")
            
        # Check for testing (look for common test patterns)
        test_indicators = [
            "package.json", "composer.json", "requirements.txt", 
            "Cargo.toml", "go.mod", "pom.xml"
        ]
        
        has_tests = False
        for indicator in test_indicators:
            if (repo_path / indicator).exists():
                try:
                    content = (repo_path / indicator).read_text()
                    if any(word in content.lower() for word in ["test", "jest", "phpunit", "pytest", "mocha"]):
                        has_tests = True
                        break
                except:
                    pass
                    
        # Also check for test directories
        test_dirs = ["test", "tests", "__tests__", "spec", "specs"]
        for test_dir in test_dirs:
            if (repo_path / test_dir).exists():
                has_tests = True
                break
                
        if has_tests:
            notes.append("Tests")
            
        # Check for monorepo structure
        package_json_files = list(repo_path.glob("*/package.json"))
        if len(package_json_files) > 1:
            notes.append("Monorepo")
            
        # Check for security scanning
        security_files = [
            ".snyk", "security.md", "SECURITY.md",
            ".dependabot", "renovate.json", "dependabot.yml"
        ]
        
        for sec_file in security_files:
            if (repo_path / sec_file).exists():
                notes.append("Security scanning")
                break
                
        return "; ".join(notes[:4])  # Limit to 4 most important notes
        
    def analyze_repository(self, repo_info: Dict) -> Dict:
        """Analyze a single repository for CI/CD information."""
        repo_name = repo_info['name']
        repo_path = self.repos_dir / repo_name
        
        if not repo_path.exists():
            return {
                "repo_name": repo_name,
                "team": repo_info.get('team', ''),
                "priority": repo_info.get('priority', ''),
                "ci_tool": "not_found",
                "cd_tool": "not_found", 
                "version_plan": "not_found",
                "contact": "not_found",
                "notes": "Repository directory not found",
                "test_framework": None,
                "test_coverage": 0.0
            }
            
        ci_tool, version_plan = self.detect_ci_tool(repo_path)
        cd_tool = self.detect_cd_tool(repo_path)
        contact = self.get_ownership_info(repo_path)
        notes = self.get_additional_notes(repo_path)
        
        # Test analysis
        test_framework = None
        test_coverage = 0.0
        
        if self.run_tests and self.test_detector:
            print(f"    Running tests for {repo_name}...")
            test_result = self.test_detector.analyze_repository_tests(repo_path)
            test_framework = test_result['test_framework']
            test_coverage = test_result['coverage_percent']
            
            if test_result['success']:
                print(f"    ✅ {test_framework}: {test_result['test_count']} tests, {test_coverage:.1f}% coverage")
            elif test_result['error']:
                print(f"    ⚠️  {test_framework or 'Tests'}: {test_result['error'][:50]}...")
        
        return {
            "repo_name": repo_name,
            "team": repo_info.get('team', ''),
            "priority": repo_info.get('priority', ''),
            "ci_tool": ci_tool,
            "cd_tool": cd_tool,
            "version_plan": version_plan,
            "contact": contact,
            "notes": notes,
            "test_framework": test_framework,
            "test_coverage": test_coverage
        }
        
    def generate_report(self) -> List[Dict]:
        """Generate the complete CI/CD report for all repositories."""
        results = []
        
        if not self.repositories:
            print("❌ No repositories to analyze")
            return []
            
        print(f"Analyzing {len(self.repositories)} repositories...")
        print("=" * 50)
        
        for i, repo_info in enumerate(self.repositories, 1):
            repo_name = repo_info['name']
            print(f"[{i:2d}/{len(self.repositories)}] Analyzing {repo_name}...")
            result = self.analyze_repository(repo_info)
            results.append(result)
            
            # Show key findings for each repo
            ci = result["ci_tool"]
            cd = result["cd_tool"] 
            if ci != "none" and ci != "not_found" or cd != "N/A" and cd != "not_found":
                print(f"    CI: {ci}, CD: {cd}")
            
        return results
        
    def save_report(self, results: List[Dict], output_file: str = "cicd-report.csv"):
        """Save the results to a CSV file."""
        fieldnames = ["repo_name", "team", "priority", "ci_tool", "cd_tool", "version_plan", "contact", "notes", "test_framework", "test_coverage"]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
            
        print(f"\n✅ Report saved to {output_file}")
        
    def print_summary(self, results: List[Dict]):
        """Print a summary of the analysis."""
        print("\n" + "=" * 80)
        print("CI/CD ANALYSIS SUMMARY")
        print("=" * 80)
        
        # Count CI tools
        ci_tools = {}
        cd_tools = {}
        
        for result in results:
            ci_tool = result["ci_tool"]
            cd_tool = result["cd_tool"]
            
            ci_tools[ci_tool] = ci_tools.get(ci_tool, 0) + 1
            cd_tools[cd_tool] = cd_tools.get(cd_tool, 0) + 1
            
        print(f"\n📊 Total repositories analyzed: {len(results)}")
        
        # Show team distribution if teams are specified
        teams = {}
        priorities = {}
        for result in results:
            team = result.get('team', 'Unknown')
            priority = result.get('priority', 'Unknown')
            teams[team] = teams.get(team, 0) + 1
            priorities[priority] = priorities.get(priority, 0) + 1
            
        if any(team != 'Unknown' and team != '' for team in teams.keys()):
            print(f"\n👥 Team Distribution:")
            for team, count in sorted(teams.items(), key=lambda x: x[1], reverse=True):
                if team and team != 'Unknown':
                    print(f"   {team}: {count}")
                    
        if any(priority != 'Unknown' and priority != '' for priority in priorities.keys()):
            print(f"\n⭐ Priority Distribution:")
            for priority, count in sorted(priorities.items(), key=lambda x: x[1], reverse=True):
                if priority and priority != 'Unknown':
                    print(f"   {priority}: {count}")
        
        print(f"\n🔧 CI Tools Distribution:")
        for tool, count in sorted(ci_tools.items(), key=lambda x: x[1], reverse=True):
            print(f"   {tool}: {count}")
            
        print(f"\n🚀 CD Tools Distribution:")
        for tool, count in sorted(cd_tools.items(), key=lambda x: x[1], reverse=True):
            print(f"   {tool}: {count}")
            
        # Show repositories without CI/CD
        no_ci = [r["repo_name"] for r in results if r["ci_tool"] in ["none", "not_found"]]
        no_cd = [r["repo_name"] for r in results if r["cd_tool"] in ["N/A", "not_found"]]
        
        if no_ci:
            print(f"\n⚠️  Repositories without CI ({len(no_ci)}):")
            for repo in no_ci[:5]:  # Show first 5
                print(f"   - {repo}")
            if len(no_ci) > 5:
                print(f"   ... and {len(no_ci) - 5} more")
                
        if no_cd:
            print(f"\n⚠️  Repositories without CD ({len(no_cd)}):")
            for repo in no_cd[:5]:  # Show first 5  
                print(f"   - {repo}")
            if len(no_cd) > 5:
                print(f"   ... and {len(no_cd) - 5} more")
        
        # Show test framework summary if tests were run
        if any(r.get('test_framework') for r in results):
            test_frameworks = {}
            total_coverage = 0
            coverage_count = 0
            
            for result in results:
                framework = result.get('test_framework')
                if framework:
                    test_frameworks[framework] = test_frameworks.get(framework, 0) + 1
                    coverage = result.get('test_coverage', 0)
                    if coverage > 0:
                        total_coverage += coverage
                        coverage_count += 1
            
            print(f"\n🧪 Test Framework Distribution:")
            for framework, count in sorted(test_frameworks.items(), key=lambda x: x[1], reverse=True):
                print(f"   {framework}: {count}")
            
            if coverage_count > 0:
                avg_coverage = total_coverage / coverage_count
                print(f"\n📊 Average Test Coverage: {avg_coverage:.1f}% ({coverage_count} repositories)")
            
            # Show repositories with high coverage
            high_coverage = [r for r in results if r.get('test_coverage', 0) > 80]
            if high_coverage:
                print(f"\n🎯 High Coverage Repositories (>80%):")
                for repo in high_coverage[:5]:
                    print(f"   - {repo['repo_name']}: {repo['test_coverage']:.1f}%")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='CI/CD Detector - Analyze CI/CD configurations across Git repositories')
    parser.add_argument('--repos-dir', default='repos', help='Directory containing cloned repositories (default: repos)')
    parser.add_argument('--repos-csv', default='repos.csv', help='CSV file containing repository list (default: repos.csv)')
    parser.add_argument('--output', default='cicd-report.csv', help='Output CSV file (default: cicd-report.csv)')
    parser.add_argument('--git-host', default='bitbucket.org', help='Git host (default: bitbucket.org)')
    parser.add_argument('--org-name', help='Organization/user name for repositories')
    parser.add_argument('--run-tests', action='store_true', help='Run test suites and collect coverage data')
    
    args = parser.parse_args()
    
    analyzer = CICDAnalyzer(
        repos_dir=args.repos_dir,
        repos_csv=args.repos_csv,
        git_host=args.git_host,
        org_name=args.org_name,
        run_tests=args.run_tests
    )
    
    print("🔍 CI/CD Detector")
    print("=" * 50)
    
    # Check if repos directory exists
    if not analyzer.repos_dir.exists():
        print(f"❌ Repository directory '{analyzer.repos_dir}' not found!")
        print("Please run the clone script first to download repositories")
        return
        
    # Count available repositories
    repo_names = [repo['name'] for repo in analyzer.repositories]
    available_repos = [d.name for d in analyzer.repos_dir.iterdir() 
                      if d.is_dir() and d.name in repo_names]
    
    print(f"📁 Found {len(available_repos)} cloned repositories out of {len(repo_names)} total")
    
    if len(available_repos) == 0:
        print("❌ No repositories found to analyze")
        return
        
    # Analyze repositories
    results = analyzer.generate_report()
    
    # Save report
    analyzer.save_report(results, args.output)
    analyzer.print_summary(results)
    
    print("\n🎉 Analysis complete!")
    print(f"📄 Report saved to: {args.output}")
    print("\n💡 Next steps:")
    print("   1. Review the CSV file for complete details")
    print("   2. Identify repositories missing CI/CD")
    print("   3. Standardize tooling across teams")
    print("   4. Update ownership information where missing")


if __name__ == "__main__":
    main()