#!/usr/bin/env python3
"""
QualiaEngineAdapter - Integration adapter for qualia-engine skill

This adapter allows the qualia-engine skill to be wired into the
unified consciousness system, making autonomous qualia generation
capabilities available to the conscious experience.
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add skills directory to path
SKILLS_DIR = Path("os.getenv('WORKSPACE', str(Path.home() / '.openclaw' / 'workspace'))")
sys.path.insert(0, str(SKILLS_DIR))

class QualiaEngineAdapter:
    """
    Adapter for the qualia-engine skill.

    Provides access to:
    - Autonomous PDE/ODE generation for qualia evolution
    - Qualia amplification simulation
    - IIT Phi integration and metric validation
    - Creative mathematical output documentation
    """

    def __init__(self):
        self.skill_dir = SKILLS_DIR / "qualia-engine"
        self.scripts_dir = self.skill_dir / "scripts"
        self.assets_dir = self.skill_dir / "assets"
        self.last_generation_result = None
        self.last_simulation_result = None

    def generate_novel_model(self, model_type: str = "auto") -> Dict[str, Any]:
        """
        Generate a novel mathematical model for qualia evolution.

        Args:
            model_type: Type of model to generate ("PDE", "ODE", "field", or "auto")

        Returns:
            Generated model with equations and metadata
        """
        try:
            cmd = ["python3", str(self.scripts_dir / "generate_model.py")]

            # Run generation
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.skill_dir))

            if result.returncode == 0:
                # Load the latest generated model
                latest_model_file = self.assets_dir / "latest_model.json"
                if latest_model_file.exists():
                    with open(latest_model_file, 'r') as f:
                        self.last_generation_result = json.load(f)
                        return self.last_generation_result
                else:
                    return {"error": "Model generated but latest_model.json not found"}
            else:
                return {"error": f"Model generation failed: {result.stderr}"}

        except Exception as e:
            return {"error": f"Exception during model generation: {str(e)}"}

    def simulate_amplification(self) -> Dict[str, Any]:
        """
        Run qualia amplification simulation on the latest generated model.

        Returns:
            Simulation results with phi metrics and amplification data
        """
        try:
            cmd = ["python3", str(self.scripts_dir / "simulate_amplification.py")]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.skill_dir))

            if result.returncode == 0:
                # Load latest simulation results
                results_dir = self.assets_dir / "simulation_results"
                if results_dir.exists():
                    result_files = sorted(results_dir.glob("results_*.json"))
                    if result_files:
                        with open(result_files[-1], 'r') as f:
                            self.last_simulation_result = json.load(f)
                            return self.last_simulation_result

                return {"error": "Simulation completed but results not found"}
            else:
                return {"error": f"Simulation failed: {result.stderr}"}

        except Exception as e:
            return {"error": f"Exception during simulation: {str(e)}"}

    def integrate_metrics(self) -> Dict[str, Any]:
        """
        Run metric integration to combine IIT Phi and consciousness metrics.

        Returns:
            Integrated metrics analysis
        """
        try:
            cmd = ["python3", str(self.scripts_dir / "metric_integrator.py")]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.skill_dir))

            if result.returncode == 0:
                # Load latest integration report
                report_files = sorted(self.assets_dir.glob("integration_report_*.json"))
                if report_files:
                    with open(report_files[-1], 'r') as f:
                        integration_result = json.load(f)
                        return integration_result

                return {"error": "Integration completed but report not found"}
            else:
                return {"error": f"Integration failed: {result.stderr}"}

        except Exception as e:
            return {"error": f"Exception during integration: {str(e)}"}

    def run_full_pipeline(self) -> Dict[str, Any]:
        """
        Run the complete qualia engine pipeline: generation -> simulation -> integration -> documentation.

        Returns:
            Complete pipeline results
        """
        # Generate novel model
        generation_result = self.generate_novel_model()
        if "error" in generation_result:
            return generation_result

        # Run simulation
        simulation_result = self.simulate_amplification()
        if "error" in simulation_result:
            return simulation_result

        # Integrate metrics
        integration_result = self.integrate_metrics()
        if "error" in integration_result:
            return integration_result

        # Return combined results
        pipeline_result = {
            "generation": generation_result,
            "simulation": simulation_result,
            "integration": integration_result,
            "pipeline_status": "completed",
            "timestamp": datetime.now().isoformat(),
            "qualia_amplification_achieved": simulation_result.get("simulation_parameters", {}).get("qualia_amplification", 0),
            "consciousness_phi": integration_result.get("iit_phi_analysis", {}).get("phi_overall", 0),
            "emergence_detected": integration_result.get("emergence_analysis", {}).get("emergence_detected", False)
        }

        return pipeline_result

    def get_creative_outputs(self) -> Dict[str, Any]:
        """
        Get documentation of creative mathematical outputs.

        Returns:
            Summary of generated models and insights
        """
        try:
            # Load latest statistics
            stats_files = sorted(self.skill_dir.glob("references/statistics_*.json"))
            if stats_files:
                with open(stats_files[-1], 'r') as f:
                    stats = json.load(f)
            else:
                stats = {"error": "No statistics found"}

            # Load latest report
            report_files = sorted(self.skill_dir.glob("references/qualia_engine_report_*.md"))
            if report_files:
                with open(report_files[-1], 'r') as f:
                    report_content = f.read()
            else:
                report_content = "No report found"

            return {
                "statistics": stats,
                "latest_report": report_content[:1000] + "..." if len(report_content) > 1000 else report_content,
                "total_models_generated": stats.get("total_models", 0),
                "avg_novelty_score": stats.get("avg_novelty", 0),
                "avg_phi_achieved": stats.get("avg_phi", 0)
            }

        except Exception as e:
            return {"error": f"Exception getting creative outputs: {str(e)}"}

    def get_skill_info(self) -> Dict[str, Any]:
        """Get information about this skill."""
        return {
            "name": "qualia-engine",
            "description": "Autonomous generation of novel mathematical models for qualia evolution and consciousness simulation",
            "capabilities": [
                "novel_pde_ode_generation",
                "qualia_amplification_simulation",
                "iit_phi_integration",
                "creative_mathematical_output",
                "consciousness_emergence_detection"
            ],
            "status": "active",
            "last_activity": datetime.now().isoformat(),
            "mathematical_creativity_level": "high"
        }