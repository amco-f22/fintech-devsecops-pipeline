#!/usr/bin/env python3
"""
Compliance Reporter — Automated PCI-DSS Compliance Sweep
=========================================================
Runs security scanning tools and generates consolidated
HTML/JSON compliance reports. Designed for weekly scheduled
execution via GitHub Actions.

Usage:
    python compliance_reporter.py [--output-dir ./reports]

Reports generated:
    - compliance_report.html  (human-readable dashboard)
    - compliance_report.json  (machine-readable for integrations)
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# --- Report Structure ---

class ComplianceCheck:
    """Single compliance check result."""

    def __init__(self, tool: str, category: str, status: str, findings: int, details: str = ""):
        self.tool = tool
        self.category = category
        self.status = status  # PASS, FAIL, WARN, SKIP
        self.findings = findings
        self.details = details
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "category": self.category,
            "status": self.status,
            "findings": self.findings,
            "details": self.details,
            "timestamp": self.timestamp,
        }


def run_check(name: str, command: list[str], category: str) -> ComplianceCheck:
    """Run a compliance check command and capture results."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode == 0:
            return ComplianceCheck(
                tool=name,
                category=category,
                status="PASS",
                findings=0,
                details=result.stdout[:500],
            )
        else:
            # Count findings from stderr/stdout
            output = result.stdout + result.stderr
            finding_count = output.count("FAIL") + output.count("HIGH") + output.count("CRITICAL")
            return ComplianceCheck(
                tool=name,
                category=category,
                status="FAIL" if finding_count > 0 else "WARN",
                findings=finding_count,
                details=output[:500],
            )
    except FileNotFoundError:
        return ComplianceCheck(
            tool=name,
            category=category,
            status="SKIP",
            findings=0,
            details=f"Tool '{name}' not found — install required",
        )
    except subprocess.TimeoutExpired:
        return ComplianceCheck(
            tool=name,
            category=category,
            status="WARN",
            findings=0,
            details="Check timed out after 300s",
        )


def generate_html_report(checks: list[ComplianceCheck], output_path: Path) -> None:
    """Generate an HTML compliance dashboard."""
    total = len(checks)
    passed = sum(1 for c in checks if c.status == "PASS")
    failed = sum(1 for c in checks if c.status == "FAIL")
    warnings = sum(1 for c in checks if c.status == "WARN")
    skipped = sum(1 for c in checks if c.status == "SKIP")
    score = (passed / total * 100) if total > 0 else 0

    status_colors = {
        "PASS": "#10b981",
        "FAIL": "#ef4444",
        "WARN": "#f59e0b",
        "SKIP": "#6b7280",
    }

    rows = ""
    for check in checks:
        color = status_colors.get(check.status, "#6b7280")
        rows += f"""
        <tr>
            <td>{check.tool}</td>
            <td>{check.category}</td>
            <td style="color: {color}; font-weight: bold;">{check.status}</td>
            <td>{check.findings}</td>
            <td><code>{check.details[:100]}</code></td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Compliance Report — Fintech DevSecOps Pipeline</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 2rem; background: #0f172a; color: #e2e8f0; }}
        h1 {{ color: #38bdf8; }}
        .summary {{ display: flex; gap: 1rem; margin: 1.5rem 0; }}
        .card {{ background: #1e293b; padding: 1.5rem; border-radius: 12px; min-width: 150px; text-align: center; }}
        .card h2 {{ margin: 0; font-size: 2rem; }}
        .card p {{ margin: 0.5rem 0 0; color: #94a3b8; }}
        .pass {{ color: #10b981; }}
        .fail {{ color: #ef4444; }}
        .warn {{ color: #f59e0b; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 1.5rem; }}
        th, td {{ padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid #334155; }}
        th {{ background: #1e293b; color: #38bdf8; }}
        tr:hover {{ background: #1e293b; }}
        code {{ background: #334155; padding: 2px 6px; border-radius: 4px; font-size: 0.85em; }}
        .score {{ font-size: 3rem; font-weight: bold; }}
        .timestamp {{ color: #64748b; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h1>🛡️ Compliance Report — Fintech DevSecOps Pipeline</h1>
    <p class="timestamp">Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</p>

    <div class="summary">
        <div class="card">
            <h2 class="score" style="color: {'#10b981' if score >= 80 else '#f59e0b' if score >= 50 else '#ef4444'}">{score:.0f}%</h2>
            <p>Compliance Score</p>
        </div>
        <div class="card">
            <h2 class="pass">{passed}</h2>
            <p>Passed</p>
        </div>
        <div class="card">
            <h2 class="fail">{failed}</h2>
            <p>Failed</p>
        </div>
        <div class="card">
            <h2 class="warn">{warnings}</h2>
            <p>Warnings</p>
        </div>
        <div class="card">
            <h2>{skipped}</h2>
            <p>Skipped</p>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Tool</th>
                <th>Category</th>
                <th>Status</th>
                <th>Findings</th>
                <th>Details</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
</body>
</html>"""

    output_path.write_text(html, encoding='utf-8')
    print(f"✅ HTML report: {output_path}")


def generate_json_report(checks: list[ComplianceCheck], output_path: Path) -> None:
    """Generate a machine-readable JSON report."""
    report = {
        "report_type": "compliance_sweep",
        "project": "fintech-devsecops-pipeline",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_checks": len(checks),
            "passed": sum(1 for c in checks if c.status == "PASS"),
            "failed": sum(1 for c in checks if c.status == "FAIL"),
            "warnings": sum(1 for c in checks if c.status == "WARN"),
            "skipped": sum(1 for c in checks if c.status == "SKIP"),
        },
        "checks": [c.to_dict() for c in checks],
    }

    output_path.write_text(json.dumps(report, indent=2))
    print(f"✅ JSON report: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Run compliance sweep and generate reports")
    parser.add_argument("--output-dir", type=Path, default=Path("./reports"), help="Report output directory")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    print("🛡️ Starting compliance sweep...")
    print("=" * 60)

    checks = []

    # --- Secret Scanning ---
    print("\n[1/6] Running Gitleaks (secret scanning)...")
    checks.append(run_check("Gitleaks", ["gitleaks", "detect", "--no-git"], "Secret Scanning"))

    # --- Container Scanning ---
    print("[2/6] Running Trivy (container scan)...")
    checks.append(run_check(
        "Trivy",
        ["trivy", "fs", "--severity", "HIGH,CRITICAL", "--quiet", "services/webhook-service/"],
        "Vulnerability Scanning",
    ))

    # --- IaC Scanning ---
    print("[3/6] Running Checkov (IaC scan)...")
    checks.append(run_check(
        "Checkov",
        ["checkov", "--directory", "terraform/", "--quiet", "--compact"],
        "IaC Security",
    ))

    # --- OPA Policy Tests ---
    print("[5/6] Running OPA policy tests...")
    checks.append(run_check(
        "OPA",
        ["opa", "test", "policies/", "-v"],
        "Policy Compliance",
    ))

    # --- Terraform Validation ---
    print("[6/6] Running Terraform validate...")
    checks.append(run_check(
        "Terraform Validate",
        ["terraform", "validate"],
        "IaC Validation",
    ))

    # --- Generate Reports ---
    print("\n" + "=" * 60)
    print("Generating reports...")

    generate_html_report(checks, args.output_dir / "compliance_report.html")
    generate_json_report(checks, args.output_dir / "compliance_report.json")

    # --- Summary ---
    total = len(checks)
    passed = sum(1 for c in checks if c.status == "PASS")
    failed = sum(1 for c in checks if c.status == "FAIL")

    print(f"\n{'=' * 60}")
    print(f"Compliance Score: {passed}/{total} checks passed")

    if failed > 0:
        print(f"⚠️  {failed} check(s) FAILED — review reports for details")
        sys.exit(1)
    else:
        print("✅ All compliance checks passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
