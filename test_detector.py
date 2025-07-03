#!/usr/bin/env python3
"""
Test Suite Detection and Execution for CI/CD Detector
Detects and runs test suites with coverage reporting
"""

import os
import subprocess
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class TestSuiteDetector:
    """Detects and executes test suites for various frameworks."""
    
    def __init__(self, timeout: int = 120):
        self.timeout = timeout
        self.results = []
        
    def detect_test_framework(self, repo_path: Path) -> List[Dict]:
        """Detect available test frameworks in the repository."""
        frameworks = []
        
        # PHPUnit detection
        phpunit_configs = [
            repo_path / "phpunit.xml",
            repo_path / "phpunit.xml.dist", 
            repo_path / "phpunit.xml.example"
        ]
        
        for config in phpunit_configs:
            if config.exists():
                frameworks.append({
                    'type': 'phpunit',
                    'name': 'PHPUnit',
                    'config': str(config),
                    'test_dir': str(repo_path / 'tests') if (repo_path / 'tests').exists() else None
                })
                break
        
        # Pest detection (Laravel testing framework)
        pest_configs = [
            repo_path / "tests" / "Pest.php",
            repo_path / "Pest.php"
        ]
        
        for config in pest_configs:
            if config.exists():
                frameworks.append({
                    'type': 'pest',
                    'name': 'Pest',
                    'config': str(config),
                    'test_dir': str(repo_path / 'tests')
                })
                break
        
        # Laravel Dusk detection
        dusk_indicators = [
            repo_path / "tests" / "Browser",
            repo_path / "tests" / "DuskTestCase.php"
        ]
        
        for indicator in dusk_indicators:
            if indicator.exists():
                frameworks.append({
                    'type': 'dusk',
                    'name': 'Laravel Dusk',
                    'config': str(indicator),
                    'test_dir': str(repo_path / 'tests')
                })
                break
        
        # Python test frameworks
        python_test_files = list(repo_path.glob("**/test_*.py")) + list(repo_path.glob("**/*_test.py"))
        
        if python_test_files:
            # Check for pytest
            if (repo_path / "pytest.ini").exists() or (repo_path / "setup.cfg").exists():
                frameworks.append({
                    'type': 'pytest',
                    'name': 'pytest',
                    'config': 'pytest.ini' if (repo_path / "pytest.ini").exists() else 'setup.cfg',
                    'test_dir': str(repo_path / 'tests') if (repo_path / 'tests').exists() else None
                })
            else:
                # Default to unittest
                frameworks.append({
                    'type': 'unittest',
                    'name': 'unittest',
                    'config': None,
                    'test_dir': str(repo_path / 'tests') if (repo_path / 'tests').exists() else None
                })
        
        # Node.js test frameworks
        package_json = repo_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    package_data = json.load(f)
                    
                scripts = package_data.get('scripts', {})
                dev_deps = package_data.get('devDependencies', {})
                deps = package_data.get('dependencies', {})
                
                # Check for Jest
                if 'jest' in dev_deps or 'jest' in deps or 'test' in scripts:
                    frameworks.append({
                        'type': 'jest',
                        'name': 'Jest',
                        'config': 'package.json',
                        'test_dir': str(repo_path / '__tests__') if (repo_path / '__tests__').exists() else None
                    })
                
                # Check for Mocha
                elif 'mocha' in dev_deps or 'mocha' in deps:
                    frameworks.append({
                        'type': 'mocha',
                        'name': 'Mocha',
                        'config': 'package.json',
                        'test_dir': str(repo_path / 'test') if (repo_path / 'test').exists() else None
                    })
                    
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        return frameworks
    
    def run_phpunit_tests(self, repo_path: Path, config_path: str) -> Dict:
        """Run PHPUnit tests with coverage."""
        try:
            # Check if composer.json exists
            if not (repo_path / "composer.json").exists():
                return {
                    'success': False,
                    'error': 'No composer.json found',
                    'coverage': 0.0
                }
            
            # Try to install dependencies (silently)
            composer_install = subprocess.run(
                ["composer", "install", "--no-interaction", "--quiet"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            # Check if vendor/bin/phpunit exists
            phpunit_path = repo_path / "vendor" / "bin" / "phpunit"
            if not phpunit_path.exists():
                return {
                    'success': False,
                    'error': 'PHPUnit not installed',
                    'coverage': 0.0
                }
            
            # Run tests without coverage first (faster)
            test_cmd = [str(phpunit_path), "--colors=never"]
            if (repo_path / "tests").exists():
                test_cmd.append("tests")
            
            result = subprocess.run(
                test_cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            # Parse test results
            if result.returncode == 0:
                # Extract test count and assertions
                output = result.stdout
                test_match = re.search(r'OK \((\d+) tests?, (\d+) assertions?\)', output)
                if test_match:
                    test_count = int(test_match.group(1))
                    assertion_count = int(test_match.group(2))
                    
                    return {
                        'success': True,
                        'test_count': test_count,
                        'assertion_count': assertion_count,
                        'coverage': 0.0,  # No coverage driver available
                        'error': None
                    }
            
            return {
                'success': False,
                'error': f'Tests failed: {result.stderr.strip()[:100]}',
                'coverage': 0.0
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Test execution timed out',
                'coverage': 0.0
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Execution error: {str(e)[:100]}',
                'coverage': 0.0
            }
    
    def run_python_tests(self, repo_path: Path, framework_type: str) -> Dict:
        """Run Python tests with coverage."""
        try:
            # Check for requirements.txt
            requirements_file = repo_path / "requirements.txt"
            if requirements_file.exists():
                # Try to install requirements (this might fail, but we'll try running tests anyway)
                try:
                    subprocess.run(
                        ["pip", "install", "-r", "requirements.txt", "--quiet"],
                        cwd=repo_path,
                        capture_output=True,
                        timeout=60
                    )
                except:
                    pass
            
            if framework_type == 'pytest':
                # Try pytest with coverage
                cmd = ["python", "-m", "pytest", "--tb=short", "-v"]
                
                # Add coverage if pytest-cov is available
                try:
                    subprocess.run(["python", "-c", "import pytest_cov"], capture_output=True, check=True)
                    cmd.extend(["--cov=.", "--cov-report=term-missing", "--cov-report=json:coverage.json"])
                except:
                    pass
                
            else:  # unittest
                cmd = ["python", "-m", "unittest", "discover", "-s", ".", "-p", "test_*.py", "-v"]
            
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            # Parse results
            if result.returncode == 0:
                # Extract test count from output
                output = result.stdout
                
                # Try to read coverage from JSON file
                coverage_file = repo_path / "coverage.json"
                coverage_percent = 0.0
                
                if coverage_file.exists():
                    try:
                        with open(coverage_file, 'r') as f:
                            coverage_data = json.load(f)
                            coverage_percent = coverage_data.get('totals', {}).get('percent_covered', 0.0)
                        # Clean up coverage file
                        coverage_file.unlink()
                    except:
                        pass
                
                # Count tests
                if framework_type == 'pytest':
                    test_match = re.search(r'(\d+) passed', output)
                    test_count = int(test_match.group(1)) if test_match else 0
                else:
                    test_match = re.search(r'Ran (\d+) tests', output)
                    test_count = int(test_match.group(1)) if test_match else 0
                
                return {
                    'success': True,
                    'test_count': test_count,
                    'coverage': coverage_percent,
                    'error': None
                }
            
            return {
                'success': False,
                'error': f'Tests failed: {result.stderr.strip()[:100]}',
                'coverage': 0.0
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Test execution timed out',
                'coverage': 0.0
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Execution error: {str(e)[:100]}',
                'coverage': 0.0
            }
    
    def run_node_tests(self, repo_path: Path, framework_type: str) -> Dict:
        """Run Node.js tests with coverage."""
        try:
            # Check for package.json
            package_json = repo_path / "package.json"
            if not package_json.exists():
                return {
                    'success': False,
                    'error': 'No package.json found',
                    'coverage': 0.0
                }
            
            # Try to install dependencies (might fail, but we'll try running tests)
            try:
                subprocess.run(
                    ["npm", "install", "--silent"],
                    cwd=repo_path,
                    capture_output=True,
                    timeout=90
                )
            except:
                pass
            
            # Run tests
            if framework_type == 'jest':
                cmd = ["npx", "jest", "--coverage", "--silent", "--no-colors"]
            else:  # mocha
                cmd = ["npx", "mocha", "--reporter", "json"]
            
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode == 0:
                # Parse Jest output for coverage
                if framework_type == 'jest':
                    coverage_match = re.search(r'All files\s+\|\s+(\d+\.?\d*)', result.stdout)
                    coverage_percent = float(coverage_match.group(1)) if coverage_match else 0.0
                else:
                    coverage_percent = 0.0
                
                # Count tests
                test_match = re.search(r'(\d+) passing', result.stdout)
                test_count = int(test_match.group(1)) if test_match else 0
                
                return {
                    'success': True,
                    'test_count': test_count,
                    'coverage': coverage_percent,
                    'error': None
                }
            
            return {
                'success': False,
                'error': f'Tests failed: {result.stderr.strip()[:100]}',
                'coverage': 0.0
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Test execution timed out',
                'coverage': 0.0
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Execution error: {str(e)[:100]}',
                'coverage': 0.0
            }
    
    def analyze_repository_tests(self, repo_path: Path) -> Dict:
        """Analyze and run tests for a single repository."""
        if not repo_path.exists():
            return {
                'test_framework': None,
                'coverage_percent': 0.0,
                'test_count': 0,
                'success': False,
                'error': 'Repository not found'
            }
        
        # Detect test frameworks
        frameworks = self.detect_test_framework(repo_path)
        
        if not frameworks:
            return {
                'test_framework': None,
                'coverage_percent': 0.0,
                'test_count': 0,
                'success': False,
                'error': 'No test framework detected'
            }
        
        # Try to run tests with the first detected framework
        framework = frameworks[0]
        framework_type = framework['type']
        
        if framework_type in ['phpunit', 'pest']:
            result = self.run_phpunit_tests(repo_path, framework['config'])
        elif framework_type in ['pytest', 'unittest']:
            result = self.run_python_tests(repo_path, framework_type)
        elif framework_type in ['jest', 'mocha']:
            result = self.run_node_tests(repo_path, framework_type)
        else:
            return {
                'test_framework': framework['name'],
                'coverage_percent': 0.0,
                'test_count': 0,
                'success': False,
                'error': 'Unsupported test framework'
            }
        
        return {
            'test_framework': framework['name'],
            'coverage_percent': result.get('coverage', 0.0),
            'test_count': result.get('test_count', 0),
            'success': result.get('success', False),
            'error': result.get('error')
        }


def main():
    """Example usage of the TestSuiteDetector."""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python test_detector.py <repo_path>")
        sys.exit(1)
    
    repo_path = Path(sys.argv[1])
    detector = TestSuiteDetector()
    
    result = detector.analyze_repository_tests(repo_path)
    print(f"Repository: {repo_path.name}")
    print(f"Test Framework: {result['test_framework']}")
    print(f"Test Count: {result['test_count']}")
    print(f"Coverage: {result['coverage_percent']:.1f}%")
    print(f"Success: {result['success']}")
    if result['error']:
        print(f"Error: {result['error']}")


if __name__ == "__main__":
    main()