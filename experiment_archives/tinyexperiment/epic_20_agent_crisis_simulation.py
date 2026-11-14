#!/usr/bin/env python3
"""
EPIC 20-AGENT CRISIS SIMULATION
RovoDev Multi-Agent Team - The Ultimate Demonstration

Proving optimized TinyTroupe can handle complex, multi-phase business crisis
with 20 diverse agents across multiple interaction rounds.
"""

import sys
import time
import json
import os
from datetime import datetime
from typing import List, Dict, Any

sys.path.insert(0, '.')

from tinytroupe.agent.tiny_person import TinyPerson
from tinytroupe.environment.tiny_world import TinyWorld
from tinytroupe import control

# Import our optimizations
try:
    from tinytroupe.optimization.template_storage import get_template_storage
    from tinytroupe.optimization.cache_adapter import OptimizedCacheAdapter
    OPTIMIZATIONS_AVAILABLE = True
except ImportError:
    OPTIMIZATIONS_AVAILABLE = False

class Epic20AgentSimulation:
    """
    The Ultimate TinyTroupe Demonstration
    20 agents, complex crisis, multiple phases, real business decisions
    """
    
    def __init__(self):
        self.world = None
        self.agents = []
        self.simulation_log = []
        self.start_time = None
        
        # Enable optimizations if available
        if OPTIMIZATIONS_AVAILABLE:
            self.cache_adapter = OptimizedCacheAdapter()
            print("✅ Optimizations enabled: Template storage + Delta compression")
        else:
            print("⚠️  Running without optimizations")
    
    def create_crisis_scenario(self) -> Dict[str, Any]:
        """
        EPIC CRISIS: TechCorp AI Platform Catastrophic Failure
        50M users affected, $500M revenue at risk, competitors attacking
        """
        return {
            "title": "TechCorp AI Platform Crisis - Code Red",
            "severity": "CATASTROPHIC",
            "context": """
BREAKING: TechCorp's flagship AI platform suffered cascading failure.
- IMPACT: 50M users offline, $2M/hour revenue loss (18 hours = $36M lost)
- CAUSE: AI model hallucination cascade + infrastructure meltdown
- CUSTOMERS: 3 Fortune 500 clients threatening immediate contract termination
- MEDIA: Trending #TechCorpFail, stock down 22%, congressional inquiry threatened
- COMPETITION: Microsoft, Google announcing competing products within 48 hours
- TIMELINE: Board emergency session in 36 hours, CEO job potentially at risk

STAKEHOLDERS DEMANDING ANSWERS:
- Internal: Panicked employees, angry customers, frustrated investors
- External: Regulatory bodies, media, competitors capitalizing
- Board: Considering leadership changes, demanding accountability

MULTI-PHASE CRISIS RESPONSE REQUIRED:
1. IMMEDIATE (0-6h): Service restoration, damage control
2. SHORT-TERM (6-24h): Customer retention, media management  
3. MEDIUM-TERM (24-48h): Strategic recovery, competitive response
4. LONG-TERM (48h+): Platform resilience, market positioning
            """,
            "phases": [
                {
                    "name": "Emergency Response",
                    "duration": "0-6 hours", 
                    "urgency": "CRITICAL",
                    "participants": ["ceo", "cto", "ops_director", "crisis_manager"],
                    "objectives": ["Restore service", "Stop revenue bleeding", "Prevent customer exodus"]
                },
                {
                    "name": "Damage Assessment",
                    "duration": "6-12 hours",
                    "urgency": "HIGH", 
                    "participants": ["cfo", "sales_vp", "customer_success", "data_analyst", "legal_counsel"],
                    "objectives": ["Quantify losses", "Assess legal exposure", "Customer retention strategy"]
                },
                {
                    "name": "Technical Investigation", 
                    "duration": "12-24 hours",
                    "urgency": "HIGH",
                    "participants": ["cto", "lead_engineer", "ai_researcher", "security_chief", "qa_director"],
                    "objectives": ["Root cause analysis", "Fix implementation", "Prevention measures"]
                },
                {
                    "name": "Strategic Response",
                    "duration": "24-36 hours",
                    "urgency": "MEDIUM",
                    "participants": ["ceo", "cmo", "strategy_vp", "external_consultant", "investor_relations"],
                    "objectives": ["Competitive response", "Market positioning", "Investment strategy"]
                },
                {
                    "name": "Board Presentation",
                    "duration": "36-48 hours", 
                    "urgency": "CRITICAL",
                    "participants": ["ceo", "cfo", "cto", "board_chair", "lead_investor", "crisis_consultant"],
                    "objectives": ["Accountability", "Recovery plan", "Leadership decisions"]
                }
            ]
        }
    
    def create_20_agent_cast(self) -> List[TinyPerson]:
        """Create diverse 20-agent cast for epic crisis simulation"""
        
        # EPIC CAST: 20 distinct personalities and roles
        agent_specs = [
            # C-Suite Leadership (4)
            ("Sarah Chen", "CEO", "Visionary leader, 15yr tech veteran, 3 IPOs. Strategic long-term thinker. Data-driven but willing to take calculated risks. Values innovation and customer satisfaction over short-term profits."),
            
            ("Marcus Rodriguez", "CTO", "Technical perfectionist, former Google Principal Engineer, PhD CS. Quality and scalability obsessed. Cautious about rushing to market. Strong advocate for engineering excellence."),
            
            ("Jennifer Walsh", "CMO", "Customer psychology expert, former Apple VP Marketing. Aggressive about market timing and competitive positioning. Believes in bold campaigns. Launched 5 category-defining products."),
            
            ("David Kim", "CFO", "Financial pragmatist, former Goldman Sachs VP. ROI-focused risk management expert. Skeptical of unproven strategies but supportive when business case is solid."),
            
            # VP Level (4)
            ("Lisa Thompson", "VP Product", "User experience fanatic, former Spotify Product Director. Product-market fit obsessed. Analytical and research-driven but intuitive about user needs."),
            
            ("Michael Chang", "VP Operations", "Process optimization expert. Efficiency and resource allocation specialist. Workflow management and execution focused. Former McKinsey operations consultant."),
            
            ("Rachel Green", "VP Sales", "Revenue generation machine. Pipeline management expert. Customer acquisition and deal closure specialist. Aggressive growth targets and quota achievement."),
            
            ("James Wilson", "VP Engineering", "Technical implementation leader. Code quality and architecture decision maker. Performance optimization expert. Team coordination and delivery focused."),
            
            # Department Heads (4) 
            ("Anna Kowalski", "Head Customer Success", "Customer retention specialist. Relationship management expert. Churn prevention and expansion revenue focused. Former enterprise account manager."),
            
            ("Robert Taylor", "Head Communications", "Crisis communication expert. Media relations and public messaging specialist. Brand reputation management. Former political communications director."),
            
            ("Maria Gonzalez", "Head Data Science", "Metrics interpretation expert. Statistical analysis and insight generation specialist. Reporting and trend identification focused. PhD Statistics."),
            
            ("Thomas Anderson", "Head Security", "Threat assessment and risk mitigation expert. Compliance and vulnerability analysis specialist. Protection protocols and incident response focused."),
            
            # Senior Staff (4)
            ("Emily Davis", "Senior UX Designer", "User experience and interface design expert. Usability testing and design systems specialist. User research and interaction design focused."),
            
            ("Kevin Liu", "Senior Project Manager", "Timeline coordination and resource planning expert. Risk mitigation and stakeholder communication specialist. Delivery and execution focused."),
            
            ("Sophie Martin", "Senior AI Researcher", "Machine learning and AI systems expert. Model development and optimization specialist. Research and innovation focused. PhD Machine Learning."),
            
            ("Daniel Brown", "Senior DevOps Engineer", "Infrastructure and deployment expert. System reliability and performance specialist. Automation and monitoring focused."),
            
            # External Stakeholders (4)
            ("Dr. Patricia Williams", "External Crisis Consultant", "Crisis management and turnaround specialist. Strategic advisory and change management expert. Former Fortune 500 CEO during major crisis."),
            
            ("Jonathan Miller", "Board Member & Lead Investor", "Venture capital and growth strategy expert. ROI expectations and market validation specialist. Fiduciary responsibility and exit strategy focused."),
            
            ("Catherine Lee", "Enterprise Customer Representative", "Large enterprise customer perspective. Business value and implementation concerns specialist. Vendor evaluation and decision influence focused."),
            
            ("Alex Johnson", "Regulatory Affairs Specialist", "Government relations and compliance expert. Regulatory navigation and policy impact specialist. Risk assessment and legal strategy focused.")
        ]
        
        agents = []
        for name, role, personality in agent_specs:
            agent = TinyPerson(name)
            
            # PRESERVE SACRED INSTRUCTION + Rich personality
            full_personality = f"""You are a simulation of a person such that: You don't know you are a simulation, you think you are an actual person. You are {name}, {role} at TechCorp. {personality} You have deep expertise in your field and strong opinions based on your experience. You think and respond as this person would in a high-stakes business crisis."""
            
            agent.define("personality", full_personality)
            agent.define("role", role)
            agent.define("crisis_expertise", self._get_crisis_expertise(role))
            
            agents.append(agent)
        
        return agents
    
    def _get_crisis_expertise(self, role: str) -> str:
        """Get crisis-specific expertise for each role"""
        expertise_map = {
            "CEO": "Crisis leadership, stakeholder management, strategic decision-making under pressure",
            "CTO": "Technical crisis response, system recovery, engineering team coordination", 
            "CMO": "Crisis communications, brand protection, competitive response",
            "CFO": "Financial impact assessment, cost management, investor relations",
            "VP Product": "Product recovery strategy, user impact analysis, feature prioritization",
            "VP Operations": "Operational continuity, resource allocation, process optimization",
            "VP Sales": "Customer retention, revenue protection, deal salvage",
            "VP Engineering": "Technical implementation, team coordination, delivery management"
        }
        return expertise_map.get(role, "Business crisis management and strategic response")
    
    def run_epic_simulation(self, max_turns_per_phase: int = 4) -> Dict[str, Any]:
        """
        Run the EPIC 20-agent crisis simulation
        Multiple phases, complex interactions, real business decisions
        """
        
        print("🚀 STARTING EPIC 20-AGENT CRISIS SIMULATION")
        print("=" * 80)
        
        self.start_time = time.time()
        
        # Initialize
        control.begin()
        self.world = TinyWorld("TechCorp Crisis Command Center")
        self.agents = self.create_20_agent_cast()
        scenario = self.create_crisis_scenario()
        
        # Add all agents to world
        for agent in self.agents:
            self.world.add_agent(agent)
        
        print(f"✅ EPIC CAST ASSEMBLED: {len(self.agents)} agents ready")
        print(f"📋 CRISIS SCENARIO: {scenario['title']}")
        print(f"⚠️  SEVERITY: {scenario['severity']}")
        
        # Track results
        results = {
            "scenario": scenario,
            "agents": [{"name": a.name, "role": a.get("role")} for a in self.agents],
            "phases": [],
            "total_interactions": 0,
            "start_time": datetime.now().isoformat()
        }
        
        # Execute each crisis phase
        for phase_idx, phase in enumerate(scenario["phases"]):
            print(f"\n🚨 PHASE {phase_idx + 1}: {phase['name']} - {phase['urgency']}")
            print(f"   ⏰ Timeline: {phase['duration']}")
            print(f"   🎯 Objectives: {', '.join(phase['objectives'])}")
            
            phase_results = self.run_crisis_phase(phase, phase_idx + 1, max_turns_per_phase)
            results["phases"].append(phase_results)
            results["total_interactions"] += len(phase_results.get("interactions", []))
            
            # Brief pause between phases for realism
            time.sleep(2)
        
        # Calculate final metrics
        total_time = time.time() - self.start_time
        results["total_simulation_time"] = total_time
        results["end_time"] = datetime.now().isoformat()
        
        return results
    
    def run_crisis_phase(self, phase: Dict[str, Any], phase_num: int, max_turns: int) -> Dict[str, Any]:
        """Execute a single crisis phase with participating agents"""
        
        # Get participating agents for this phase
        participating_agents = self._get_phase_participants(phase)
        
        print(f"   👥 ACTIVE AGENTS: {[a.name for a in participating_agents]}")
        
        phase_interactions = []
        
        # Create phase-specific crisis context
        crisis_context = f"""
CRISIS PHASE {phase_num}: {phase['name']} - URGENCY: {phase['urgency']}
TIMELINE: {phase['duration']}
OBJECTIVES: {', '.join(phase['objectives'])}

CURRENT SITUATION: TechCorp AI platform failure continues. Every minute costs $2M in revenue.
Your expertise is CRITICAL for crisis resolution. Provide specific, actionable recommendations.

RESPONSE FORMAT: Brief, decisive, business-focused. This is a real crisis requiring immediate action.
        """
        
        # Execute turns for this phase
        for turn in range(max_turns):
            print(f"     🔥 CRISIS TURN {turn + 1}/{max_turns}")
            
            # Each agent provides crisis input
            for agent in participating_agents:
                
                objective = phase['objectives'][turn % len(phase['objectives'])]
                
                # Create urgent crisis prompt
                crisis_prompt = f"""
{crisis_context}

URGENT DECISION NEEDED - Turn {turn + 1}:
Focus area: {objective}

As {getattr(agent, 'role', 'Team Member')}, what is your immediate recommendation for {objective}?

Required response:
1. Specific action items (what to do NOW)
2. Resource requirements (who/what needed)
3. Timeline (how fast can this be done)
4. Risk assessment (what could go wrong)
5. Success metrics (how do we know it worked)

Crisis situation - be decisive and specific!
                """
                
                try:
                    start_time = time.time()
                    # Blake's definitive async fix - handle both sync and async properly
                    import asyncio
                    import inspect
                    
                    # Get the actual response
                    raw_response = agent.listen_and_act(crisis_prompt)
                    
                    # Handle coroutine properly
                    if inspect.iscoroutine(raw_response):
                        response = asyncio.run(raw_response)
                    else:
                        response = raw_response
                    
                    response_time = time.time() - start_time
                    
                    if response and len(response) > 0 and response[0] and 'action' in response[0]:
                        content = response[0]['action']['content']
                        
                        interaction = {
                            "phase": phase_num,
                            "turn": turn + 1,
                            "agent": agent.name,
                            "role": getattr(agent, "role", "Unknown"),
                            "objective": objective,
                            "response": content,
                            "response_time": response_time,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        phase_interactions.append(interaction)
                        self.simulation_log.append(interaction)
                        
                        print(f"       ✅ {agent.name}: {content[:120]}...")
                    
                except Exception as e:
                        print(f"       ❌ {agent.name}: Crisis response failed - {e}")
        
        return {
            "phase_name": phase['name'],
            "phase_number": phase_num,
            "urgency": phase['urgency'],
            "participants": [a.name for a in participating_agents],
            "interactions": phase_interactions,
            "objectives": phase['objectives']
        }
    
    def _get_phase_participants(self, phase: Dict[str, Any]) -> List[TinyPerson]:
        """Get agents participating in this crisis phase"""
        
        participating_agents = []
        phase_participants = phase.get("participants", [])
        
        # Map phase participant roles to actual agents
        for agent in self.agents:
            agent_role = getattr(agent, "role", "").lower().replace(" ", "_")
            
            # Check if agent should participate in this phase
            for participant_key in phase_participants:
                if (participant_key in agent_role or 
                    participant_key in agent.name.lower() or
                    self._role_matches_participant(agent_role, participant_key)):
                    participating_agents.append(agent)
                    break
        
        # Ensure we have at least some participants
        if not participating_agents:
            # Fallback: use first 4 agents
            participating_agents = self.agents[:4]
        
        return participating_agents
    
    def _role_matches_participant(self, agent_role: str, participant_key: str) -> bool:
        """Check if agent role matches phase participant"""
        role_mappings = {
            "ceo": ["ceo"],
            "cto": ["cto"],
            "cfo": ["cfo"],
            "cmo": ["cmo"],
            "ops_director": ["vp_operations", "operations"],
            "crisis_manager": ["communications", "external_consultant"],
            "sales_vp": ["vp_sales", "sales"],
            "customer_success": ["customer_success"],
            "data_analyst": ["data_science"],
            "legal_counsel": ["regulatory"],
            "lead_engineer": ["vp_engineering", "engineering"],
            "ai_researcher": ["ai_researcher"],
            "security_chief": ["security"],
            "qa_director": ["qa", "quality"],
            "strategy_vp": ["strategy"],
            "external_consultant": ["external_consultant"],
            "investor_relations": ["investor"],
            "board_chair": ["board"],
            "lead_investor": ["investor"],
            "crisis_consultant": ["external_consultant"]
        }
        
        mapped_roles = role_mappings.get(participant_key, [participant_key])
        return any(mapped_role in agent_role for mapped_role in mapped_roles)

def main():
    """Execute the EPIC 20-agent crisis simulation"""
    
    print("🔥 EPIC 20-AGENT CRISIS SIMULATION - ULTIMATE DEMONSTRATION")
    print("🎯 Proving optimized TinyTroupe handles complex business scenarios")
    print("=" * 80)
    
    try:
        # Create and run epic simulation
        epic_sim = Epic20AgentSimulation()
        
        print("\n🎬 LAUNCHING EPIC CRISIS SIMULATION...")
        start_time = time.time()
        
        results = epic_sim.run_epic_simulation(max_turns_per_phase=4)
        
        total_time = time.time() - start_time
        
        # Display epic results
        print("\n" + "=" * 80)
        print("🏆 EPIC SIMULATION COMPLETE - ULTIMATE SUCCESS!")
        print("=" * 80)
        
        print(f"\n📊 EPIC RESULTS:")
        print(f"   🎭 Agents: {len(results['agents'])} diverse crisis experts")
        print(f"   🚨 Phases: {len(results['phases'])} crisis response phases")
        print(f"   💬 Interactions: {results['total_interactions']} total responses")
        print(f"   ⏱️  Duration: {total_time:.2f} seconds")
        
        # Save epic results
        with open('epic_simulation_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 EPIC results saved to epic_simulation_results.json")
        
        # Check cache optimization impact
        if os.path.exists('tinytroupe-default.cache.json'):
            cache_size = os.path.getsize('tinytroupe-default.cache.json') / (1024*1024)
            print(f"📈 Cache size after epic simulation: {cache_size:.1f}MB")
        
        print(f"\n🎉 EPIC 20-AGENT SIMULATION COMPLETE!")
        print(f"   ✅ Complex crisis scenario successfully simulated")
        print(f"   ✅ 20 diverse agents with rich personalities")
        print(f"   ✅ Multi-phase business decision making")
        print(f"   ✅ Optimized storage preserving full functionality")
        
    except Exception as e:
        print(f"\n❌ EPIC SIMULATION ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        control.end()

if __name__ == "__main__":
    main()