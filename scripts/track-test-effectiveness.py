#!/usr/bin/env python3
"""
Track test effectiveness by analyzing CI failures and correlating with issues/PRs
This helps identify which tests actually catch bugs vs just failing randomly
"""
import json
import subprocess
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path


def get_github_api_data(endpoint):
    """Fetch data from GitHub API"""
    cmd = ['gh', 'api', endpoint]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error fetching {endpoint}: {result.stderr}")
        return None
    return json.loads(result.stdout)


def analyze_workflow_runs(repo_owner, repo_name, days_back=30):
    """Analyze workflow runs to find test failures"""
    since = (datetime.now() - timedelta(days=days_back)).isoformat()

    # Get workflow runs
    runs = get_github_api_data(
        f'/repos/{repo_owner}/{repo_name}/actions/runs?created=>{since}&status=failure'
    )

    if not runs:
        return {}

    test_failures = defaultdict(list)

    for run in runs.get('workflow_runs', []):
        # Get jobs for this run
        jobs = get_github_api_data(
            f'/repos/{repo_owner}/{repo_name}/actions/runs/{run["id"]}/jobs'
        )

        if not jobs:
            continue

        for job in jobs.get('jobs', []):
            if job['conclusion'] == 'failure':
                # Try to extract which test failed from logs
                logs_url = job.get('logs_url')
                if logs_url:
                    # Parse logs to find test failures
                    test_name = extract_failed_test(job['name'], run['id'])
                    if test_name:
                        test_failures[test_name].append({
                            'run_id': run['id'],
                            'run_number': run['run_number'],
                            'date': run['created_at'],
                            'branch': run['head_branch'],
                            'commit': run['head_sha'][:7],
                            'pr': extract_pr_number(run)
                        })

    return test_failures


def extract_failed_test(job_name, run_id):
    """Extract test name from job - this is simplified"""
    # Map job names to test categories
    job_to_tests = {
        'Basic sanity tests': 'test_basic_sanity',
        'Ansible syntax check': 'ansible_syntax',
        'Docker build test': 'docker_tests',
        'Configuration generation test': 'config_generation',
        'Ansible dry-run validation': 'ansible_dry_run'
    }
    return job_to_tests.get(job_name, job_name)


def extract_pr_number(run):
    """Extract PR number from workflow run"""
    for pr in run.get('pull_requests', []):
        return pr['number']
    return None


def correlate_with_issues(repo_owner, repo_name, test_failures):
    """Correlate test failures with issues/PRs that fixed them"""
    correlations = defaultdict(lambda: {'caught_bugs': 0, 'false_positives': 0})

    for test_name, failures in test_failures.items():
        for failure in failures:
            if failure['pr']:
                # Check if PR was merged (indicating it fixed a real issue)
                pr = get_github_api_data(
                    f'/repos/{repo_owner}/{repo_name}/pulls/{failure["pr"]}'
                )

                if pr and pr.get('merged'):
                    # Check PR title/body for bug indicators
                    title = pr.get('title', '').lower()
                    body = pr.get('body', '').lower()

                    bug_keywords = ['fix', 'bug', 'error', 'issue', 'broken', 'fail']
                    is_bug_fix = any(keyword in title or keyword in body
                                    for keyword in bug_keywords)

                    if is_bug_fix:
                        correlations[test_name]['caught_bugs'] += 1
                    else:
                        correlations[test_name]['false_positives'] += 1

    return correlations


def generate_effectiveness_report(test_failures, correlations):
    """Generate test effectiveness report"""
    report = []
    report.append("# Test Effectiveness Report")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Summary
    report.append("## Summary")
    total_failures = sum(len(f) for f in test_failures.values())
    report.append(f"- Total test failures: {total_failures}")
    report.append(f"- Unique tests that failed: {len(test_failures)}")
    report.append("")

    # Effectiveness scores
    report.append("## Test Effectiveness Scores")
    report.append("| Test | Failures | Caught Bugs | False Positives | Effectiveness |")
    report.append("|------|----------|-------------|-----------------|---------------|")

    scores = []
    for test_name, failures in test_failures.items():
        failure_count = len(failures)
        caught = correlations[test_name]['caught_bugs']
        false_pos = correlations[test_name]['false_positives']

        # Calculate effectiveness (bugs caught / total failures)
        if failure_count > 0:
            effectiveness = caught / failure_count
        else:
            effectiveness = 0

        scores.append((test_name, failure_count, caught, false_pos, effectiveness))

    # Sort by effectiveness
    scores.sort(key=lambda x: x[4], reverse=True)

    for test_name, failures, caught, false_pos, effectiveness in scores:
        report.append(f"| {test_name} | {failures} | {caught} | {false_pos} | {effectiveness:.1%} |")

    # Recommendations
    report.append("\n## Recommendations")

    for test_name, failures, _caught, _false_pos, effectiveness in scores:
        if effectiveness < 0.2 and failures > 5:
            report.append(f"- ⚠️  Consider improving or removing `{test_name}` (only {effectiveness:.0%} effective)")
        elif effectiveness > 0.8:
            report.append(f"- ✅ `{test_name}` is highly effective ({effectiveness:.0%})")

    return '\n'.join(report)


def save_metrics(test_failures, correlations):
    """Save metrics to JSON for historical tracking"""
    metrics_file = Path('.metrics/test-effectiveness.json')
    metrics_file.parent.mkdir(exist_ok=True)

    # Load existing metrics
    if metrics_file.exists():
        with open(metrics_file) as f:
            historical = json.load(f)
    else:
        historical = []

    # Add current metrics
    current = {
        'date': datetime.now().isoformat(),
        'test_failures': {
            test: len(failures) for test, failures in test_failures.items()
        },
        'effectiveness': {
            test: {
                'caught_bugs': data['caught_bugs'],
                'false_positives': data['false_positives'],
                'score': data['caught_bugs'] / (data['caught_bugs'] + data['false_positives'])
                        if (data['caught_bugs'] + data['false_positives']) > 0 else 0
            }
            for test, data in correlations.items()
        }
    }

    historical.append(current)

    # Keep last 12 months of data
    cutoff = datetime.now() - timedelta(days=365)
    historical = [
        h for h in historical
        if datetime.fromisoformat(h['date']) > cutoff
    ]

    with open(metrics_file, 'w') as f:
        json.dump(historical, f, indent=2)


if __name__ == '__main__':
    # Configure these for your repo
    REPO_OWNER = 'trailofbits'
    REPO_NAME = 'algo'

    print("Analyzing test effectiveness...")

    # Analyze last 30 days of CI runs
    test_failures = analyze_workflow_runs(REPO_OWNER, REPO_NAME, days_back=30)

    # Correlate with issues/PRs
    correlations = correlate_with_issues(REPO_OWNER, REPO_NAME, test_failures)

    # Generate report
    report = generate_effectiveness_report(test_failures, correlations)

    print("\n" + report)

    # Save report
    report_file = Path('.metrics/test-effectiveness-report.md')
    report_file.parent.mkdir(exist_ok=True)
    with open(report_file, 'w') as f:
        f.write(report)
    print(f"\nReport saved to: {report_file}")

    # Save metrics for tracking
    save_metrics(test_failures, correlations)
    print("Metrics saved to: .metrics/test-effectiveness.json")
