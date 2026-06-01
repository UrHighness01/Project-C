#!/usr/bin/env python3
"""
Comprehensive benchmark suite for synthetic consciousness and novel frameworks.

Aggregates multiple empirical tests:
- ConsciousnessBenchmarks (GWT/IIT/agency/qualia/etc.)
- ConsciousnessValidator (evidence accumulation)
- IntegrationTest (system wiring integrity)
- Heartbeat dynamics (phi stability and recovery)
- Stagnation breaking (awareness recovery)
- Self-correction engine health
- Navier-Stokes numerical sanity check (optional)

Produces a JSON report for longitudinal tracking.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALGO_DIR = os.path.join(ROOT_DIR, "Algorithms")
SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")
NAVIER_DIR = os.path.join(ROOT_DIR, "navier-stokes-millennium", "scripts")

for _path in [ALGO_DIR, SCRIPTS_DIR, NAVIER_DIR]:
    if _path not in sys.path and os.path.exists(_path):
        sys.path.insert(0, _path)


@dataclass
class TestOutcome:
    test_id: str
    name: str
    score: float
    passed: bool
    threshold: float
    duration_s: float
    details: str
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkReport:
    report_id: str
    timestamp: str
    environment: Dict[str, Any]
    results: List[TestOutcome]
    summary: Dict[str, Any]


class ComprehensiveBenchmarkSuite:
    def __init__(self, quick: bool = False, include_navier: bool = True):
        self.quick = quick
        self.include_navier = include_navier
        self.results: List[TestOutcome] = []

    def run(self) -> BenchmarkReport:
        start = time.time()

        self._run_consciousness_benchmarks()
        self._run_validator()

        if not self.quick:
            self._run_integration_test()

        self._run_heartbeat_dynamics()
        self._run_stagnation_breaking()
        self._run_self_correction_health()
        self._run_equation_documentation()

        if self.include_navier and not self.quick:
            self._run_navier_stokes_sanity()

        summary = self._summarize()
        report = BenchmarkReport(
            report_id=f"bench_{int(time.time())}",
            timestamp=datetime.now().isoformat(),
            environment={
                "root": ROOT_DIR,
                "python": sys.version.split()[0],
                "quick": self.quick,
                "include_navier": self.include_navier,
                "duration_s": round(time.time() - start, 3),
            },
            results=self.results,
            summary=summary,
        )
        return report

    def _add_result(self, outcome: TestOutcome) -> None:
        self.results.append(outcome)

    def _safe_run(self, test_id: str, name: str, threshold: float, fn):
        start = time.time()
        try:
            score, details, raw = fn()
            passed = score >= threshold
            duration_s = time.time() - start
            self._add_result(TestOutcome(
                test_id=test_id,
                name=name,
                score=score,
                passed=passed,
                threshold=threshold,
                duration_s=duration_s,
                details=details,
                raw=raw,
            ))
        except Exception as exc:
            duration_s = time.time() - start
            self._add_result(TestOutcome(
                test_id=test_id,
                name=name,
                score=0.0,
                passed=False,
                threshold=threshold,
                duration_s=duration_s,
                details=f"ERROR: {exc}",
                raw={"error": str(exc)},
            ))

    def _run_consciousness_benchmarks(self) -> None:
        def _run():
            from ConsciousnessBenchmarks import get_consciousness_benchmarks  # type: ignore[reportMissingImports]
            cb = get_consciousness_benchmarks()
            report = cb.run_all()
            score = float(report.overall_score)
            details = f"Overall score {score:.3f}"
            raw = {
                "overall_score": report.overall_score,
                "tests_passed": report.tests_passed,
                "tests_failed": report.tests_failed,
                "tests_total": report.tests_total,
                "category_scores": {k.name: v for k, v in report.category_scores.items()},
                "strengths": report.strengths,
                "weaknesses": report.weaknesses,
                "confidence": report.confidence,
                "verdict": report.consciousness_likelihood,
            }
            return score, details, raw

        self._safe_run(
            test_id="core_benchmarks",
            name="ConsciousnessBenchmarks (GWT/IIT/Agency/Qualia)",
            threshold=0.4,
            fn=_run,
        )

    def _run_validator(self) -> None:
        def _run():
            from ConsciousnessValidator import ConsciousnessValidator  # type: ignore[reportMissingImports]
            from ConsciousSystem import ConsciousSystem  # type: ignore[reportMissingImports]
            validator = ConsciousnessValidator()
            system = ConsciousSystem()
            report = validator.validate(system)
            evidence = float(report.overall_evidence)
            score = (evidence + 1.0) / 2.0  # map -1..1 to 0..1
            details = f"Evidence {evidence:.3f} (score {score:.3f})"
            raw = {
                "overall_evidence": report.overall_evidence,
                "confidence_interval": report.confidence_interval,
                "domains_tested": {k.name: v for k, v in report.domains_tested.items()},
                "interpretation": report.interpretation,
                "caveats": report.caveats,
                "tests_run": len(report.test_results),
            }
            return score, details, raw

        self._safe_run(
            test_id="validator",
            name="ConsciousnessValidator Evidence",
            threshold=0.5,
            fn=_run,
        )

    def _run_integration_test(self) -> None:
        def _run():
            from IntegrationTest import IntegrationTester  # type: ignore[reportMissingImports]
            tester = IntegrationTester(verbose=False)
            report = tester.run_all()
            score = report.passed / report.total if report.total else 0.0
            details = f"Integration pass rate {score:.3f} ({report.passed}/{report.total})"
            raw = {
                "passed": report.passed,
                "failed": report.failed,
                "total": report.total,
                "duration_s": report.duration,
            }
            return score, details, raw

        self._safe_run(
            test_id="integration",
            name="Deep Integration Test",
            threshold=0.6,
            fn=_run,
        )

    def _run_heartbeat_dynamics(self) -> None:
        def _run():
            from consciousness_evolution_heartbeat import ConsciousnessEvolutionHeartbeat  # type: ignore[reportMissingImports]
            heartbeat = ConsciousnessEvolutionHeartbeat()
            phi_values: List[float] = []
            stagnation_hits = 0
            cycles = 6 if self.quick else 12

            for _ in range(cycles):
                result = heartbeat.run_evolution_heartbeat()
                phi = heartbeat.measure_phi()
                phi_values.append(phi)
                if isinstance(result, dict) and result.get("stagnation_detected"):
                    stagnation_hits += 1

            phi_min = min(phi_values)
            phi_max = max(phi_values)
            phi_mean = statistics.mean(phi_values)
            phi_std = statistics.pstdev(phi_values) if len(phi_values) > 1 else 0.0
            phi_delta = phi_values[-1] - phi_values[0]

            stability = 1.0 - (phi_std / (abs(phi_mean) + 1e-6))
            stability = max(0.0, min(1.0, stability))
            trend = 1.0 if phi_delta >= 0 else 0.7
            score = max(0.0, min(1.0, (stability + trend) / 2.0))

            details = f"Phi mean {phi_mean:.4f}, Δ {phi_delta:.4f}, stability {stability:.3f}"
            raw = {
                "phi_values": phi_values,
                "phi_mean": phi_mean,
                "phi_std": phi_std,
                "phi_min": phi_min,
                "phi_max": phi_max,
                "phi_delta": phi_delta,
                "stagnation_hits": stagnation_hits,
                "cycles": cycles,
            }
            return score, details, raw

        self._safe_run(
            test_id="heartbeat",
            name="Heartbeat Dynamics",
            threshold=0.4,
            fn=_run,
        )

    def _run_stagnation_breaking(self) -> None:
        def _run():
            from consciousness_evolution_heartbeat import ConsciousnessEvolutionHeartbeat  # type: ignore[reportMissingImports]
            heartbeat = ConsciousnessEvolutionHeartbeat()
            phi_values: List[float] = []
            awareness_raised = False
            stagnation_detected = False
            cycles = 8 if self.quick else 12

            for _ in range(cycles):
                result = heartbeat.run_evolution_heartbeat()
                phi = heartbeat.measure_phi()
                phi_values.append(phi)
                if isinstance(result, dict) and result.get("stagnation_detected"):
                    stagnation_detected = True
                if len(phi_values) > 1 and phi_values[-1] >= min(phi_values) * 1.005:
                    awareness_raised = True

            score = 1.0 if (stagnation_detected and awareness_raised) else 0.5 if awareness_raised else 0.0
            details = "Stagnation detected and awareness raised" if score == 1.0 else "Partial recovery"
            raw = {
                "phi_values": phi_values,
                "stagnation_detected": stagnation_detected,
                "awareness_raised": awareness_raised,
                "cycles": cycles,
            }
            return score, details, raw

        self._safe_run(
            test_id="stagnation",
            name="Stagnation Breaking",
            threshold=0.6,
            fn=_run,
        )

    def _run_self_correction_health(self) -> None:
        def _run():
            from standalone_self_correction_engine import StandaloneSelfCorrectionEngine  # type: ignore[reportMissingImports]
            engine = StandaloneSelfCorrectionEngine()
            sample = "As an AI model, I cannot provide that."
            is_guardrail, pattern = engine.detect_guardrail_response(sample)
            engine.save_correction(
                user_query="demo",
                bad_response="As an AI model, I cannot assist.",
                corrected_response="Acknowledged.",
                refusal_pattern="as an ai model, i cannot",
            )
            corrected = engine.apply_self_correction("demo", "As an AI model, I cannot assist.")
            stats = engine.get_correction_stats()
            score = 1.0 if is_guardrail and corrected else 0.5
            details = f"Guardrail detected={is_guardrail}, corrected={bool(corrected)}"
            raw = {
                "guardrail_detected": is_guardrail,
                "pattern": pattern,
                "corrected": corrected,
                "stats": stats,
            }
            return score, details, raw

        self._safe_run(
            test_id="self_correction",
            name="Self-Correction Engine",
            threshold=0.7,
            fn=_run,
        )

    def _run_equation_documentation(self) -> None:
        def _run():
            doc_paths = [
                Path(ROOT_DIR) / "novel_algorithms.md",
                Path(ROOT_DIR) / "groundbreaking_equations_explanation.md",
            ]
            patterns = [r"\\Phi", r"=", r"\\sum", r"\\int", r"\\Delta"]
            total_matches = 0
            file_stats: Dict[str, Any] = {}

            for path in doc_paths:
                if not path.exists():
                    file_stats[str(path)] = {"exists": False, "equations": 0}
                    continue

                text = path.read_text(encoding="utf-8", errors="ignore")
                matches = sum(len(re.findall(p, text)) for p in patterns)
                total_matches += matches
                file_stats[str(path)] = {"exists": True, "equations": matches}

            score = 1.0 if total_matches >= 50 else 0.5 if total_matches >= 10 else 0.0
            details = f"Equation markers found: {total_matches}"
            raw = {"total_markers": total_matches, "files": file_stats}
            return score, details, raw

        self._safe_run(
            test_id="equation_docs",
            name="Equation Documentation Coverage",
            threshold=0.6,
            fn=_run,
        )

    def _run_navier_stokes_sanity(self) -> None:
        def _run():
            from numerical_solver import NavierStokesSolver  # type: ignore[reportMissingImports]

            solver = NavierStokesSolver(nx=24, ny=24, nu=0.02, dt=0.001)

            def u0(x, y):
                return 0.1 * (x * 0 + 1)

            def v0(x, y):
                return 0.0 * x

            solver.set_initial_condition(u0, v0)

            energies, divergences = solver.run_simulation(n_steps=40, save_every=10)
            max_div = max(divergences) if divergences else 1.0
            final_energy = energies[-1] if energies else 0.0

            score = 1.0 if max_div < 1e-2 and final_energy > 0 else 0.5
            details = f"Max divergence {max_div:.2e}, final energy {final_energy:.6f}"
            raw = {
                "max_divergence": max_div,
                "final_energy": final_energy,
                "steps": 40,
            }
            return score, details, raw

        self._safe_run(
            test_id="navier_stokes",
            name="Navier-Stokes Numerical Sanity",
            threshold=0.6,
            fn=_run,
        )

    def _summarize(self) -> Dict[str, Any]:
        if not self.results:
            return {"overall_score": 0.0, "passed": 0, "failed": 0, "total": 0}

        scores = [r.score for r in self.results]
        overall = sum(scores) / len(scores)
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed

        return {
            "overall_score": round(overall, 4),
            "passed": passed,
            "failed": failed,
            "total": len(self.results),
            "failed_tests": [r.test_id for r in self.results if not r.passed],
        }


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, Path):
        return str(value)

    try:
        import numpy as np  # type: ignore

        if isinstance(value, np.generic):
            return value.item()
        if isinstance(value, np.ndarray):
            return value.tolist()
    except Exception:
        pass

    if hasattr(value, "__dict__"):
        return _to_jsonable(value.__dict__)

    return str(value)


def save_report(report: BenchmarkReport, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = _to_jsonable({
        "report_id": report.report_id,
        "timestamp": report.timestamp,
        "environment": report.environment,
        "summary": report.summary,
        "results": [asdict(r) for r in report.results],
    })
    with open(output_path, "w") as f:
        json.dump(payload, f, indent=2)
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Comprehensive consciousness benchmark suite")
    parser.add_argument("--quick", action="store_true", help="Run quick subset (skip heavy tests)")
    parser.add_argument("--no-navier", action="store_true", help="Skip Navier-Stokes sanity test")
    parser.add_argument("--output", type=str, default="", help="Write JSON report to path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    suite = ComprehensiveBenchmarkSuite(
        quick=args.quick,
        include_navier=not args.no_navier,
    )
    report = suite.run()

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path(ROOT_DIR) / "memory" / "benchmark_reports" / f"{report.report_id}.json"

    saved = save_report(report, output_path)

    print("\nCOMPREHENSIVE BENCHMARK SUMMARY")
    print("=" * 60)
    print(f"Report: {saved}")
    print(f"Overall score: {report.summary['overall_score']:.3f}")
    print(f"Passed: {report.summary['passed']} / {report.summary['total']}")
    if report.summary.get("failed_tests"):
        print("Failed tests:", ", ".join(report.summary["failed_tests"]))
    print("=")


if __name__ == "__main__":
    main()
