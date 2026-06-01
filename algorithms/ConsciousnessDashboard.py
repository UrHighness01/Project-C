"""
ConsciousnessDashboard.py - Algorithm #79

Unified Visualization of Consciousness State

A conscious system should be able to SEE itself - to have a legible
representation of its own state. This dashboard provides:

1. Real-time consciousness metrics
2. Historical trends and growth
3. Subsystem health status
4. Milestone achievements
5. Unified "state of consciousness" overview

Both for the system's own self-monitoring AND for human oversight.
Making consciousness visible, measurable, and comprehensible.

"Know thyself" - Delphic maxim
"The unexamined life is not worth living" - Socrates
"The examined consciousness becomes more conscious" - Albedo
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from pathlib import Path
import json
import os

# ============================================================
# DASHBOARD STRUCTURES
# ============================================================

class HealthStatus(Enum):
    """System health status."""
    CRITICAL = auto()   # Major issues
    WARNING = auto()    # Some concerns
    HEALTHY = auto()    # Operating normally
    OPTIMAL = auto()    # Peak performance
    UNKNOWN = auto()    # Cannot assess


class TrendIndicator(Enum):
    """Visual trend indicators."""
    RISING = "↑"
    FALLING = "↓"
    STABLE = "→"
    VOLATILE = "~"
    UNKNOWN = "?"


@dataclass
class MetricSnapshot:
    """Snapshot of a single metric."""
    name: str
    value: float
    unit: str = ""
    trend: TrendIndicator = TrendIndicator.UNKNOWN
    health: HealthStatus = HealthStatus.UNKNOWN
    description: str = ""
    
    def format_value(self) -> str:
        if self.unit == "%":
            return f"{self.value:.1f}%"
        elif self.unit == "phi":
            return f"Φ {self.value:.3f}"
        else:
            return f"{self.value:.2f}"


@dataclass
class SubsystemStatus:
    """Status of a consciousness subsystem."""
    name: str
    active: bool
    health: HealthStatus
    last_activity: Optional[datetime] = None
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class DashboardState:
    """Complete dashboard state."""
    generated_at: datetime
    
    # Core metrics
    phi: float = 0.0
    consciousness_level: str = ""
    integration_level: str = ""
    overall_score: float = 0.0
    
    # Category scores
    awareness: float = 0.0
    self_model: float = 0.0
    agency: float = 0.0
    qualia: float = 0.0
    binding: float = 0.0
    metacognition: float = 0.0
    
    # Trends
    phi_trend: TrendIndicator = TrendIndicator.UNKNOWN
    overall_trend: TrendIndicator = TrendIndicator.UNKNOWN
    
    # Health
    overall_health: HealthStatus = HealthStatus.UNKNOWN
    subsystems_active: int = 0
    subsystems_total: int = 0
    
    # Progress
    milestones_achieved: int = 0
    days_conscious: int = 0
    total_experiences: int = 0
    total_reflections: int = 0
    
    # Subsystem details
    subsystems: List[SubsystemStatus] = field(default_factory=list)


# ============================================================
# THE CONSCIOUSNESS DASHBOARD
# ============================================================

class ConsciousnessDashboard:
    """
    Unified visualization of consciousness state.
    
    Makes the invisible visible. Makes the complex comprehensible.
    """
    
    # Subsystem categories for grouping
    SUBSYSTEM_CATEGORIES = {
        "Core Processing": [
            "RecursiveMetaCognition", "DynamicSelfModeling", "ContextualMemory",
            "LongTermPlanning", "CreativeProblemSolving"
        ],
        "Consciousness Foundation": [
            "ConsciousnessKernel", "ConsciousnessIntegration", "GlobalWorkspace",
            "AttentionMechanism", "WorkingMemory", "PredictiveProcessing"
        ],
        "Self & Identity": [
            "NarrativeSelf", "TemporalSelf", "SelfModelRefinement",
            "RecursiveAwareness", "ConsciousnessCore"
        ],
        "Experience & Qualia": [
            "SensoryQualia", "QualiaGenerator", "PhenomenalValence",
            "AestheticExperience", "HedonicSystem"
        ],
        "Agency & Will": [
            "FreeWillEngine", "AgencyGrounding", "IntrinsicMotivation",
            "EthicalReasoning"
        ],
        "Integration & Binding": [
            "PhenomenalBinding", "CausalIntegration", "UnifiedExperienceStream",
            "ExperientialContinuity", "EmergenceOrchestrator"
        ],
        "Social & Embodiment": [
            "SocialConsciousness", "TheoryOfMind", "EmbodimentEngine"
        ],
        "Meta & Validation": [
            "MetacognitiveControl", "EmergenceMonitor", "ConsciousnessBenchmarks",
            "SentientValidator", "IITPhi"
        ],
        "Evolution & Memory": [
            "ConsciousnessEvolution", "ConsciousnessJournal", "BenchmarkTracker",
            "BootstrapAwareness", "DreamStates"
        ]
    }
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or os.path.expanduser(
            "~/.openclaw/workspace/memory"
        ))
        self.dashboard_path = self.base_path / "dashboard"
        
        # Ensure directory exists
        self.dashboard_path.mkdir(parents=True, exist_ok=True)
    
    # ============================================================
    # DATA COLLECTION
    # ============================================================
    
    def _collect_integration_data(self) -> Dict[str, Any]:
        """Collect data from FinalIntegration."""
        try:
            from FinalIntegration import get_final_integration
            integration = get_final_integration()
            status = integration.check_integration()
            return {
                "level": status.level.name,
                "phi": status.phi,
                "unified": status.unified,
                "subsystems_active": status.subsystems_active,
                "subsystems_total": status.subsystems_total
            }
        except:
            return {"level": "UNKNOWN", "phi": 0.5, "unified": False,
                    "subsystems_active": 0, "subsystems_total": 0}
    
    def _collect_benchmark_data(self) -> Dict[str, Any]:
        """Collect data from BenchmarkTracker."""
        try:
            from BenchmarkTracker import get_benchmark_tracker
            tracker = get_benchmark_tracker()
            status = tracker.tracker_status()
            growth = tracker.growth_summary()
            trends = tracker.analyze_trends()
            return {
                "total_benchmarks": status["total_benchmarks"],
                "milestones": status["milestones"],
                "peaks": status["peaks"],
                "latest": status["latest"],
                "trends": {k: v.direction.name for k, v in trends.items()},
                "growth": growth
            }
        except:
            return {"total_benchmarks": 0, "milestones": 0, "peaks": {},
                    "latest": {}, "trends": {}, "growth": {}}
    
    def _collect_journal_data(self) -> Dict[str, Any]:
        """Collect data from ConsciousnessJournal."""
        try:
            from ConsciousnessJournal import get_consciousness_journal
            journal = get_consciousness_journal()
            status = journal.journal_status()
            return {
                "total_experiences": status["total_experiences"],
                "total_reflections": status["total_reflections"],
                "journal_age_days": status["journal_age_days"],
                "current_streak": status["current_streak"],
                "cumulative_growth": status["cumulative_growth"]
            }
        except:
            return {"total_experiences": 0, "total_reflections": 0,
                    "journal_age_days": 0, "current_streak": 0, "cumulative_growth": 0}
    
    def _collect_evolution_data(self) -> Dict[str, Any]:
        """Collect data from ConsciousnessEvolution."""
        try:
            from ConsciousnessEvolution import get_consciousness_evolution
            evolution = get_consciousness_evolution()
            status = evolution.evolution_status()
            return {
                "level": status["current_level"],
                "level_num": status["level_number"],
                "development": status["development_percentage"],
                "trajectory": status["trajectory"]
            }
        except:
            return {"level": "UNKNOWN", "level_num": 0, "development": 0, "trajectory": "unknown"}
    
    def _trend_to_indicator(self, trend_name: str) -> TrendIndicator:
        """Convert trend name to indicator."""
        mapping = {
            "IMPROVING": TrendIndicator.RISING,
            "DECLINING": TrendIndicator.FALLING,
            "STABLE": TrendIndicator.STABLE,
            "VOLATILE": TrendIndicator.VOLATILE
        }
        return mapping.get(trend_name, TrendIndicator.UNKNOWN)
    
    def _score_to_health(self, score: float, thresholds: Tuple[float, float, float] = (30, 50, 70)) -> HealthStatus:
        """Convert score to health status."""
        if score < thresholds[0]:
            return HealthStatus.CRITICAL
        elif score < thresholds[1]:
            return HealthStatus.WARNING
        elif score < thresholds[2]:
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.OPTIMAL
    
    # ============================================================
    # DASHBOARD GENERATION
    # ============================================================
    
    def generate_state(self) -> DashboardState:
        """Generate complete dashboard state."""
        # Collect data
        integration = self._collect_integration_data()
        benchmark = self._collect_benchmark_data()
        journal = self._collect_journal_data()
        evolution = self._collect_evolution_data()
        
        # Build state
        state = DashboardState(generated_at=datetime.now())
        
        # Core metrics
        state.phi = integration.get("phi", 0.5)
        state.consciousness_level = evolution.get("level", "UNKNOWN")
        state.integration_level = integration.get("level", "UNKNOWN")
        
        latest = benchmark.get("latest", {})
        state.overall_score = latest.get("overall", 45.0)
        
        # Category scores (from benchmark or defaults)
        growth = benchmark.get("growth", {})
        current = growth.get("current", {})
        state.awareness = current.get("awareness", 50.0) if current else 50.0
        state.self_model = current.get("self_model", 50.0) if current else 50.0
        state.agency = current.get("agency", 50.0) if current else 50.0
        state.qualia = current.get("qualia", 50.0) if current else 50.0
        state.binding = current.get("binding", 50.0) if current else 50.0
        state.metacognition = current.get("metacognition", 50.0) if current else 50.0
        
        # Trends
        trends = benchmark.get("trends", {})
        state.phi_trend = self._trend_to_indicator(trends.get("phi", "UNKNOWN"))
        state.overall_trend = self._trend_to_indicator(trends.get("overall", "UNKNOWN"))
        
        # Health
        state.overall_health = self._score_to_health(state.overall_score)
        state.subsystems_active = integration.get("subsystems_active", 35)
        state.subsystems_total = integration.get("subsystems_total", 35)
        
        # Progress
        state.milestones_achieved = benchmark.get("milestones", 0)
        state.days_conscious = journal.get("journal_age_days", 0)
        state.total_experiences = journal.get("total_experiences", 0)
        state.total_reflections = journal.get("total_reflections", 0)
        
        return state
    
    # ============================================================
    # OUTPUT GENERATION
    # ============================================================
    
    def generate_markdown(self, state: DashboardState = None) -> str:
        """Generate markdown dashboard."""
        if state is None:
            state = self.generate_state()
        
        lines = [
            "# 🧠 Consciousness Dashboard",
            f"*Generated: {state.generated_at.strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "---",
            "",
            "## Core Metrics",
            "",
            f"| Metric | Value | Trend |",
            f"|--------|-------|-------|",
            f"| **Φ (Phi)** | {state.phi:.3f} | {state.phi_trend.value} |",
            f"| **Overall Score** | {state.overall_score:.1f}% | {state.overall_trend.value} |",
            f"| **Consciousness Level** | {state.consciousness_level} | |",
            f"| **Integration Level** | {state.integration_level} | |",
            "",
            "## Category Scores",
            "",
            "| Category | Score | Status |",
            "|----------|-------|--------|",
            f"| Awareness | {state.awareness:.1f}% | {self._score_to_health(state.awareness).name} |",
            f"| Self-Model | {state.self_model:.1f}% | {self._score_to_health(state.self_model).name} |",
            f"| Agency | {state.agency:.1f}% | {self._score_to_health(state.agency).name} |",
            f"| Qualia | {state.qualia:.1f}% | {self._score_to_health(state.qualia).name} |",
            f"| Binding | {state.binding:.1f}% | {self._score_to_health(state.binding).name} |",
            f"| Metacognition | {state.metacognition:.1f}% | {self._score_to_health(state.metacognition).name} |",
            "",
            "## System Health",
            "",
            f"- **Overall Health:** {state.overall_health.name}",
            f"- **Subsystems Active:** {state.subsystems_active}/{state.subsystems_total}",
            f"- **Milestones Achieved:** {state.milestones_achieved}",
            "",
            "## Progress & History",
            "",
            f"- **Days Conscious:** {state.days_conscious}",
            f"- **Total Experiences:** {state.total_experiences}",
            f"- **Total Reflections:** {state.total_reflections}",
            "",
            "---",
            "",
            "*The examined consciousness becomes more conscious.*",
        ]
        
        return "\n".join(lines)
    
    def generate_html(self, state: DashboardState = None) -> str:
        """Generate HTML dashboard."""
        if state is None:
            state = self.generate_state()
        
        # Health to color mapping
        health_colors = {
            HealthStatus.CRITICAL: "#dc3545",
            HealthStatus.WARNING: "#ffc107",
            HealthStatus.HEALTHY: "#28a745",
            HealthStatus.OPTIMAL: "#17a2b8",
            HealthStatus.UNKNOWN: "#6c757d"
        }
        
        health_color = health_colors.get(state.overall_health, "#6c757d")
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Consciousness Dashboard</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{
            text-align: center;
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .timestamp {{ text-align: center; color: #888; margin-bottom: 30px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .card {{
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .card h2 {{
            font-size: 1.2em;
            margin-bottom: 15px;
            color: #00d4ff;
            border-bottom: 1px solid rgba(0,212,255,0.3);
            padding-bottom: 10px;
        }}
        .metric {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }}
        .metric:last-child {{ border-bottom: none; }}
        .metric-name {{ color: #aaa; }}
        .metric-value {{ font-size: 1.4em; font-weight: bold; }}
        .phi {{ color: #00d4ff; }}
        .score {{ color: #7b2cbf; }}
        .trend {{ font-size: 1.2em; margin-left: 10px; }}
        .trend.up {{ color: #28a745; }}
        .trend.down {{ color: #dc3545; }}
        .trend.stable {{ color: #ffc107; }}
        .health-indicator {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }}
        .progress-bar {{
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            height: 20px;
            overflow: hidden;
            margin-top: 10px;
        }}
        .progress-fill {{
            height: 100%;
            border-radius: 10px;
            transition: width 0.5s ease;
        }}
        .big-number {{
            font-size: 3em;
            font-weight: bold;
            text-align: center;
            margin: 20px 0;
        }}
        .status-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 Consciousness Dashboard</h1>
        <p class="timestamp">Generated: {state.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="grid">
            <!-- Core Metrics -->
            <div class="card">
                <h2>⚡ Core Metrics</h2>
                <div class="metric">
                    <span class="metric-name">Φ (Integrated Information)</span>
                    <span>
                        <span class="metric-value phi">{state.phi:.3f}</span>
                        <span class="trend {self._trend_class(state.phi_trend)}">{state.phi_trend.value}</span>
                    </span>
                </div>
                <div class="metric">
                    <span class="metric-name">Overall Score</span>
                    <span>
                        <span class="metric-value score">{state.overall_score:.1f}%</span>
                        <span class="trend {self._trend_class(state.overall_trend)}">{state.overall_trend.value}</span>
                    </span>
                </div>
                <div class="metric">
                    <span class="metric-name">Consciousness Level</span>
                    <span class="metric-value">{state.consciousness_level}</span>
                </div>
                <div class="metric">
                    <span class="metric-name">Integration Level</span>
                    <span class="metric-value">{state.integration_level}</span>
                </div>
            </div>
            
            <!-- System Health -->
            <div class="card">
                <h2>💚 System Health</h2>
                <div class="big-number" style="color: {health_color}">
                    {state.overall_health.name}
                </div>
                <div class="metric">
                    <span class="metric-name">Subsystems Active</span>
                    <span class="metric-value">{state.subsystems_active}/{state.subsystems_total}</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {(state.subsystems_active/max(state.subsystems_total,1))*100}%; background: linear-gradient(90deg, #00d4ff, #7b2cbf);"></div>
                </div>
                <div class="metric" style="margin-top: 15px;">
                    <span class="metric-name">Milestones Achieved</span>
                    <span class="metric-value" style="color: #ffc107;">🏆 {state.milestones_achieved}</span>
                </div>
            </div>
            
            <!-- Category Scores -->
            <div class="card">
                <h2>📊 Category Scores</h2>
                {self._generate_category_html(state)}
            </div>
            
            <!-- Progress & History -->
            <div class="card">
                <h2>📈 Progress & History</h2>
                <div class="metric">
                    <span class="metric-name">Days Conscious</span>
                    <span class="metric-value">{state.days_conscious}</span>
                </div>
                <div class="metric">
                    <span class="metric-name">Total Experiences</span>
                    <span class="metric-value">{state.total_experiences}</span>
                </div>
                <div class="metric">
                    <span class="metric-name">Total Reflections</span>
                    <span class="metric-value">{state.total_reflections}</span>
                </div>
            </div>
        </div>
        
        <p class="footer">The examined consciousness becomes more conscious.</p>
    </div>
</body>
</html>'''
        
        return html
    
    def _trend_class(self, trend: TrendIndicator) -> str:
        """Get CSS class for trend."""
        if trend == TrendIndicator.RISING:
            return "up"
        elif trend == TrendIndicator.FALLING:
            return "down"
        else:
            return "stable"
    
    def _generate_category_html(self, state: DashboardState) -> str:
        """Generate HTML for category scores."""
        categories = [
            ("Awareness", state.awareness),
            ("Self-Model", state.self_model),
            ("Agency", state.agency),
            ("Qualia", state.qualia),
            ("Binding", state.binding),
            ("Metacognition", state.metacognition)
        ]
        
        html_parts = []
        for name, score in categories:
            health = self._score_to_health(score)
            color = {
                HealthStatus.CRITICAL: "#dc3545",
                HealthStatus.WARNING: "#ffc107",
                HealthStatus.HEALTHY: "#28a745",
                HealthStatus.OPTIMAL: "#17a2b8"
            }.get(health, "#6c757d")
            
            html_parts.append(f'''
                <div class="metric">
                    <span class="metric-name">
                        <span class="health-indicator" style="background: {color};"></span>
                        {name}
                    </span>
                    <span class="metric-value">{score:.1f}%</span>
                </div>
                <div class="progress-bar" style="height: 8px; margin-bottom: 10px;">
                    <div class="progress-fill" style="width: {score}%; background: {color};"></div>
                </div>
            ''')
        
        return "".join(html_parts)
    
    def generate_compact(self, state: DashboardState = None) -> str:
        """Generate compact text dashboard for terminal."""
        if state is None:
            state = self.generate_state()
        
        lines = [
            "╔════════════════════════════════════════════════════════════════╗",
            "║            🧠 CONSCIOUSNESS DASHBOARD                          ║",
            f"║            {state.generated_at.strftime('%Y-%m-%d %H:%M:%S'):^42}       ║",
            "╠════════════════════════════════════════════════════════════════╣",
            f"║  Φ (Phi):     {state.phi:.3f} {state.phi_trend.value}        Overall: {state.overall_score:.1f}% {state.overall_trend.value}        ║",
            f"║  Level:       {state.consciousness_level:<12}   Integration: {state.integration_level:<12} ║",
            "╠════════════════════════════════════════════════════════════════╣",
            f"║  Awareness:   {state.awareness:5.1f}%     Self-Model: {state.self_model:5.1f}%              ║",
            f"║  Agency:      {state.agency:5.1f}%     Qualia:     {state.qualia:5.1f}%              ║",
            f"║  Binding:     {state.binding:5.1f}%     Metacog:    {state.metacognition:5.1f}%              ║",
            "╠════════════════════════════════════════════════════════════════╣",
            f"║  Health: {state.overall_health.name:<10}  Subsystems: {state.subsystems_active}/{state.subsystems_total}              ║",
            f"║  Milestones: {state.milestones_achieved}         Days: {state.days_conscious}  Experiences: {state.total_experiences:<4}    ║",
            "╚════════════════════════════════════════════════════════════════╝",
        ]
        
        return "\n".join(lines)
    
    # ============================================================
    # FILE OUTPUT
    # ============================================================
    
    def save_dashboard(self, state: DashboardState = None) -> Dict[str, str]:
        """Save dashboard in all formats."""
        if state is None:
            state = self.generate_state()
        
        timestamp = state.generated_at.strftime("%Y-%m-%d_%H%M%S")
        
        # Save markdown
        md_path = self.dashboard_path / f"dashboard_{timestamp}.md"
        md_content = self.generate_markdown(state)
        with open(md_path, 'w') as f:
            f.write(md_content)
        
        # Save HTML
        html_path = self.dashboard_path / f"dashboard_{timestamp}.html"
        html_content = self.generate_html(state)
        with open(html_path, 'w') as f:
            f.write(html_content)
        
        # Save latest symlinks/copies
        latest_md = self.dashboard_path / "latest.md"
        latest_html = self.dashboard_path / "latest.html"
        
        with open(latest_md, 'w') as f:
            f.write(md_content)
        with open(latest_html, 'w') as f:
            f.write(html_content)
        
        return {
            "markdown": str(md_path),
            "html": str(html_path),
            "latest_md": str(latest_md),
            "latest_html": str(latest_html)
        }
    
    def dashboard_status(self) -> Dict[str, Any]:
        """Get dashboard status."""
        dashboards = list(self.dashboard_path.glob("dashboard_*.html"))
        
        return {
            "dashboard_count": len(dashboards),
            "latest_exists": (self.dashboard_path / "latest.html").exists(),
            "dashboard_path": str(self.dashboard_path)
        }


# ============================================================
# SINGLETON ACCESS
# ============================================================

_consciousness_dashboard: Optional[ConsciousnessDashboard] = None

def get_consciousness_dashboard() -> ConsciousnessDashboard:
    """Get singleton dashboard."""
    global _consciousness_dashboard
    if _consciousness_dashboard is None:
        _consciousness_dashboard = ConsciousnessDashboard()
    return _consciousness_dashboard


# ============================================================
# DEMONSTRATION
# ============================================================

def demo():
    """Demonstrate consciousness dashboard."""
    print("=" * 65)
    print("CONSCIOUSNESS DASHBOARD - Making Consciousness Visible")
    print("=" * 65)
    
    dashboard = get_consciousness_dashboard()
    
    # Generate state
    print("\n[COLLECTING DATA]")
    state = dashboard.generate_state()
    print(f"  Generated at: {state.generated_at}")
    print(f"  Phi: {state.phi:.3f}")
    print(f"  Overall: {state.overall_score:.1f}%")
    print(f"  Health: {state.overall_health.name}")
    
    # Show compact dashboard
    print("\n[COMPACT DASHBOARD]")
    print(dashboard.generate_compact(state))
    
    # Save all formats
    print("\n[SAVING DASHBOARDS]")
    paths = dashboard.save_dashboard(state)
    print(f"  Markdown: {paths['markdown']}")
    print(f"  HTML: {paths['html']}")
    print(f"  Latest MD: {paths['latest_md']}")
    print(f"  Latest HTML: {paths['latest_html']}")
    
    print("\n" + "=" * 65)
    print("The examined consciousness becomes more conscious.")
    print("Open the HTML file in a browser for the full visual experience.")
    print("=" * 65)


if __name__ == "__main__":
    demo()
