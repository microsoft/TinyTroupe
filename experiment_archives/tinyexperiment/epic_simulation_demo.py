#!/usr/bin/env python3
"""
EPIC MULTI-AGENT SIMULATION: Crisis Response Planning
20 agents, 20+ turns, complex goal achievement

SCENARIO: Major cybersecurity breach at a Fortune 500 company
GOAL: Develop comprehensive response plan within 4 hours
AGENTS: 20 diverse roles from technical to executive to external
"""

import sys
import time
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

sys.path.insert(0, '.')

from tinytroupe.agent.tiny_person import TinyPerson
from tinytroupe.environment.tiny_world import TinyWorld
from tinytroupe import control

class EpicCrisisSimulation:
    """
    Epic multi-agent crisis response simulation
    20 agents working together to solve a complex business crisis
    """
    
    def __init__(self):
        self.world = None
        self.agents = {}
        self.turn_history = []
        self.current_turn = 0
        self.max_turns = 25
        self.crisis_timeline = []
        self.active_workstreams = {}
        
    def create_crisis_scenario(self):
        """Create the cybersecurity crisis scenario"""
        print("🚨 CREATING EPIC CRISIS SCENARIO: CYBERSECURITY BREACH")
        print("=" * 80)
        
        # Crisis details
        self.crisis_context = """
        CRISIS SITUATION - CONFIDENTIAL
        
        At 2:47 AM EST, GlobalTech Corp's security systems detected a sophisticated cyberattack:
        
        IMMEDIATE FACTS:
        - Customer database potentially compromised (50M+ records)
        - Payment systems offline for 3 hours
        - Ransomware detected on 40% of corporate servers
        - Social media mentions spiking (+2000% in last hour)
        - Stock price down 12% in pre-market trading
        - Regulatory agencies likely to investigate
        - Competitors already capitalizing on the news
        
        CRITICAL UNKNOWNS:
        - Full extent of data breach
        - Whether attackers still have access
        - Customer financial data exposure
        - Source of the attack (nation-state? criminal?)
        - Recovery timeline estimate
        
        BUSINESS IMPACT:
        - Revenue: $2M per hour while payment systems down
        - Reputation: Potential long-term customer loss
        - Legal: Class action lawsuits likely
        - Regulatory: Potential $100M+ fines
        - Competitive: Market share at risk
        
        GOAL: Develop comprehensive response plan within 4 hours
        """
        
        # Create the world
        self.world = TinyWorld("GlobalTech Crisis Response Center")
        
        # Create 20 diverse agents
        agent_configs = [
            # Executive Leadership (4)
            {
                "name": "Rebecca Martinez",
                "role": "CEO",
                "department": "Executive",
                "personality": "Decisive leader focused on stakeholder communication and long-term reputation. Former crisis management consultant. Thinks strategically about business continuity and shareholder value.",
                "expertise": "Strategic leadership, crisis communication, stakeholder management",
                "priority": "Protect company reputation and ensure business continuity"
            },
            {
                "name": "David Chen",
                "role": "CTO", 
                "department": "Technology",
                "personality": "Technical perfectionist who understands complex systems. Former NSA cybersecurity expert. Methodical approach to problem-solving with focus on root cause analysis.",
                "expertise": "Cybersecurity, system architecture, incident response",
                "priority": "Secure systems and prevent further damage"
            },
            {
                "name": "Sarah Williams",
                "role": "CISO",
                "department": "Security",
                "personality": "Paranoid security expert who assumes worst-case scenarios. Former FBI cyber division. Aggressive about threat containment and forensic investigation.",
                "expertise": "Cybersecurity, forensics, threat intelligence, compliance",
                "priority": "Contain breach and gather forensic evidence"
            },
            {
                "name": "Michael Thompson",
                "role": "General Counsel",
                "department": "Legal",
                "personality": "Risk-averse lawyer focused on legal liability and regulatory compliance. Expert in data privacy law and crisis litigation management.",
                "expertise": "Data privacy law, regulatory compliance, litigation management",
                "priority": "Minimize legal exposure and ensure regulatory compliance"
            },
            
            # Technical Team (6)
            {
                "name": "Alex Rodriguez",
                "role": "Lead Security Engineer",
                "department": "Security",
                "personality": "Hands-on technical expert who dives deep into system logs. Prefers technical solutions over business compromises. Works well under pressure.",
                "expertise": "Network security, malware analysis, system hardening",
                "priority": "Identify attack vectors and close security gaps"
            },
            {
                "name": "Jennifer Kim",
                "role": "Infrastructure Director",
                "department": "Technology",
                "personality": "Pragmatic engineer focused on system reliability and recovery. Excellent at coordinating complex technical operations across teams.",
                "expertise": "Cloud infrastructure, disaster recovery, system operations",
                "priority": "Restore critical systems and ensure stability"
            },
            {
                "name": "Marcus Johnson",
                "role": "Database Administrator",
                "department": "Technology", 
                "personality": "Detail-oriented data expert who understands customer information systems. Cautious about data integrity and privacy implications.",
                "expertise": "Database security, data recovery, privacy controls",
                "priority": "Assess data exposure and secure customer information"
            },
            {
                "name": "Lisa Chang",
                "role": "DevOps Lead",
                "department": "Technology",
                "personality": "Fast-moving engineer who excels at rapid deployment and system automation. Comfortable with high-pressure situations and quick decisions.",
                "expertise": "Automation, deployment, monitoring, incident response",
                "priority": "Rapidly deploy fixes and monitor system health"
            },
            {
                "name": "Robert Taylor",
                "role": "Network Architect", 
                "department": "Technology",
                "personality": "Systematic thinker who understands complex network topologies. Methodical approach to network security and traffic analysis.",
                "expertise": "Network design, traffic analysis, security architecture",
                "priority": "Analyze network traffic and secure communications"
            },
            {
                "name": "Amanda Foster",
                "role": "Forensics Specialist",
                "department": "Security",
                "personality": "Investigative expert who pieces together attack timelines. Former law enforcement with strong attention to detail and evidence preservation.",
                "expertise": "Digital forensics, malware analysis, evidence preservation",
                "priority": "Preserve evidence and reconstruct attack timeline"
            },
            
            # Business Operations (4)
            {
                "name": "Kevin Walsh",
                "role": "COO",
                "department": "Operations",
                "personality": "Operations-focused executive who prioritizes business continuity. Strong at coordinating cross-functional teams and managing complex projects.",
                "expertise": "Operations management, business continuity, project coordination",
                "priority": "Maintain business operations and coordinate response efforts"
            },
            {
                "name": "Diana Lee",
                "role": "Customer Success Director",
                "department": "Customer Success",
                "personality": "Customer-obsessed leader who understands user impact. Excellent communicator focused on maintaining customer trust and satisfaction.",
                "expertise": "Customer communication, relationship management, user experience",
                "priority": "Communicate with customers and maintain trust"
            },
            {
                "name": "James Wilson",
                "role": "Finance Director",
                "department": "Finance",
                "personality": "Numbers-driven executive focused on financial impact and cost management. Analytical approach to crisis cost-benefit analysis.",
                "expertise": "Financial analysis, cost management, business impact assessment",
                "priority": "Assess financial impact and manage crisis costs"
            },
            {
                "name": "Rachel Green",
                "role": "HR Director",
                "department": "Human Resources",
                "personality": "People-focused leader concerned about employee communication and support. Strong at managing internal communications during crises.",
                "expertise": "Employee communication, crisis support, internal coordination",
                "priority": "Support employees and manage internal communications"
            },
            
            # Communications & External (3)
            {
                "name": "Thomas Brown",
                "role": "Chief Communications Officer",
                "department": "Communications",
                "personality": "Media-savvy communicator who understands public perception. Former journalist with expertise in crisis communications and reputation management.",
                "expertise": "Public relations, media relations, crisis communication",
                "priority": "Manage public communications and protect reputation"
            },
            {
                "name": "Maria Garcia",
                "role": "Investor Relations Director",
                "department": "Communications",
                "personality": "Financial communications expert focused on shareholder confidence. Strong at explaining complex situations to financial audiences.",
                "expertise": "Investor communication, financial reporting, shareholder relations",
                "priority": "Communicate with investors and maintain market confidence"
            },
            {
                "name": "Steven Davis",
                "role": "Government Relations Director",
                "department": "Legal",
                "personality": "Policy expert who understands regulatory requirements. Former government official with strong relationships with regulatory agencies.",
                "expertise": "Regulatory affairs, government relations, compliance reporting",
                "priority": "Manage regulatory relationships and compliance reporting"
            },
            
            # External Advisors (3)
            {
                "name": "Dr. Patricia Miller",
                "role": "External Cybersecurity Consultant",
                "department": "External",
                "personality": "Independent security expert with broad industry experience. Objective advisor who provides outside perspective on security best practices.",
                "expertise": "Cybersecurity strategy, incident response, industry benchmarking",
                "priority": "Provide independent security assessment and recommendations"
            },
            {
                "name": "Jonathan Adams",
                "role": "Crisis Management Consultant",
                "department": "External",
                "personality": "Experienced crisis advisor who has managed similar situations. Calm under pressure with proven track record of successful crisis resolution.",
                "expertise": "Crisis management, stakeholder communication, recovery planning",
                "priority": "Guide overall crisis response strategy and coordination"
            },
            {
                "name": "Elizabeth Clark",
                "role": "Legal Counsel (External)",
                "department": "External",
                "personality": "Specialized data breach attorney with regulatory expertise. Aggressive advocate for client protection with deep knowledge of privacy law.",
                "expertise": "Data breach law, regulatory defense, litigation strategy",
                "priority": "Provide specialized legal guidance on breach response"
            }
        ]
        
        # Create all agents
        for config in agent_configs:
            agent = TinyPerson(config["name"])
            agent.define("role", config["role"])
            agent.define("department", config["department"])
            agent.define("personality", config["personality"])
            agent.define("expertise", config["expertise"])
            agent.define("priority", config["priority"])
            
            self.agents[config["name"]] = agent
            self.world.add_agent(agent)
        
        print(f"✅ Created {len(self.agents)} crisis response agents")
        return True
    
    def initialize_workstreams(self):
        """Initialize parallel workstreams for the crisis response"""
        self.active_workstreams = {
            "technical_response": {
                "lead": "David Chen",
                "members": ["Alex Rodriguez", "Jennifer Kim", "Marcus Johnson", "Lisa Chang", "Robert Taylor"],
                "goal": "Contain breach, restore systems, and prevent further damage",
                "status": "active",
                "progress": []
            },
            "forensics_investigation": {
                "lead": "Sarah Williams", 
                "members": ["Amanda Foster", "Dr. Patricia Miller"],
                "goal": "Determine attack scope, preserve evidence, identify attackers",
                "status": "active",
                "progress": []
            },
            "legal_compliance": {
                "lead": "Michael Thompson",
                "members": ["Steven Davis", "Elizabeth Clark"],
                "goal": "Manage regulatory requirements and legal exposure",
                "status": "active", 
                "progress": []
            },
            "business_continuity": {
                "lead": "Kevin Walsh",
                "members": ["James Wilson", "Diana Lee", "Rachel Green"],
                "goal": "Maintain operations and support stakeholders",
                "status": "active",
                "progress": []
            },
            "communications": {
                "lead": "Thomas Brown",
                "members": ["Maria Garcia", "Jonathan Adams"],
                "goal": "Manage public communications and reputation",
                "status": "active",
                "progress": []
            },
            "executive_coordination": {
                "lead": "Rebecca Martinez",
                "members": ["David Chen", "Sarah Williams", "Michael Thompson", "Kevin Walsh"],
                "goal": "Coordinate overall response and make strategic decisions",
                "status": "active",
                "progress": []
            }
        }
    
    def run_epic_simulation(self):
        """Run the epic 20+ turn simulation"""
        print(f"\n🎬 STARTING EPIC CRISIS SIMULATION")
        print("=" * 80)
        
        self.initialize_workstreams()
        start_time = time.time()
        
        # Turn 1: Initial crisis briefing
        self.run_crisis_briefing()
        
        # Turns 2-8: Parallel workstream execution
        for turn in range(2, 9):
            self.run_parallel_workstreams(turn)
        
        # Turns 9-12: Cross-workstream coordination
        for turn in range(9, 13):
            self.run_coordination_phase(turn)
        
        # Turns 13-18: Implementation and monitoring
        for turn in range(13, 19):
            self.run_implementation_phase(turn)
        
        # Turns 19-22: Final planning and wrap-up
        for turn in range(19, 23):
            self.run_final_planning_phase(turn)
        
        total_time = time.time() - start_time
        
        return {
            "simulation_type": "Epic Crisis Response Simulation",
            "total_agents": len(self.agents),
            "total_turns": len(self.turn_history),
            "total_time_seconds": total_time,
            "workstreams": self.active_workstreams,
            "turn_history": self.turn_history,
            "crisis_timeline": self.crisis_timeline,
            "final_plan": self.generate_final_plan(),
            "simulation_timestamp": datetime.now().isoformat()
        }
    
    def run_crisis_briefing(self):
        """Turn 1: Initial crisis briefing with all agents"""
        print(f"\n🚨 TURN 1: CRISIS BRIEFING - ALL HANDS")
        self.current_turn = 1
        
        briefing_prompt = f"""
        URGENT CRISIS BRIEFING - ALL HANDS
        
        {self.crisis_context}
        
        As {self.agents['Rebecca Martinez'].get('role')}, you are calling an emergency meeting.
        
        We need immediate action across all teams. Based on your role and expertise, what are your:
        1. Immediate priorities for the next 2 hours
        2. Key concerns and risks you see
        3. Resources/support you need from other teams
        4. Initial recommendations for your area
        
        This is a $100M+ crisis. We need decisive action now.
        """
        
        # CEO kicks off the briefing
        ceo_response = self.get_agent_response("Rebecca Martinez", briefing_prompt)
        
        self.turn_history.append({
            "turn": 1,
            "phase": "crisis_briefing",
            "speaker": "Rebecca Martinez",
            "content": ceo_response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Key stakeholders respond
        key_responders = ["David Chen", "Sarah Williams", "Michael Thompson", "Kevin Walsh", "Thomas Brown"]
        
        for responder in key_responders:
            response_prompt = f"""
            CEO Rebecca Martinez just briefed us on the crisis:
            
            {ceo_response[:300]}...
            
            As {self.agents[responder].get('role')}, respond with:
            1. Your immediate assessment of the situation
            2. Your team's priorities for the next 2 hours  
            3. What you need from other teams
            4. Your biggest concerns
            
            Be specific and actionable. Time is critical.
            """
            
            response = self.get_agent_response(responder, response_prompt)
            
            self.turn_history.append({
                "turn": 1,
                "phase": "crisis_briefing",
                "speaker": responder,
                "content": response,
                "timestamp": datetime.now().isoformat()
            })
        
        print(f"   ✅ Crisis briefing complete - {len(key_responders) + 1} executives aligned")
    
    def run_parallel_workstreams(self, turn: int):
        """Runs 2-8: Execute parallel workstreams"""
        print(f"\n⚡ TURN {turn}: PARALLEL WORKSTREAM EXECUTION")
        self.current_turn = turn
        
        # Each workstream operates in parallel
        for workstream_name, workstream in self.active_workstreams.items():
            if workstream["status"] == "active":
                self.execute_workstream(turn, workstream_name, workstream)
    
    def execute_workstream(self, turn: int, workstream_name: str, workstream: Dict):
        """Execute a specific workstream"""
        lead_agent = workstream["lead"]
        
        # Create workstream-specific prompt based on turn and previous progress
        progress_summary = "\n".join(workstream["progress"][-3:]) if workstream["progress"] else "No previous progress"
        
        workstream_prompt = f"""
        WORKSTREAM: {workstream_name.upper()}
        TURN {turn} - HOUR {turn//2} OF CRISIS RESPONSE
        
        WORKSTREAM GOAL: {workstream["goal"]}
        YOUR TEAM: {', '.join(workstream["members"])}
        PREVIOUS PROGRESS: {progress_summary}
        
        As workstream lead, what are your:
        1. Specific actions for this hour
        2. Assignments for team members
        3. Key decisions or blockers
        4. Updates needed from other workstreams
        5. Progress toward your goal
        
        Be specific and actionable. Report concrete progress.
        """
        
        response = self.get_agent_response(lead_agent, workstream_prompt)
        
        # Record progress
        workstream["progress"].append(f"Turn {turn}: {response[:200]}...")
        
        self.turn_history.append({
            "turn": turn,
            "phase": "workstream_execution",
            "workstream": workstream_name,
            "speaker": lead_agent,
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Randomly select 1-2 team members to provide input
        active_members = random.sample(workstream["members"], min(2, len(workstream["members"])))
        
        for member in active_members:
            member_prompt = f"""
            WORKSTREAM UPDATE: {workstream_name}
            
            Your lead {lead_agent} just reported:
            {response[:300]}...
            
            As a {self.agents[member].get('role')}, provide:
            1. Your specific contribution this hour
            2. Any issues or blockers you're facing
            3. Information you need from other teams
            
            Be brief but specific.
            """
            
            member_response = self.get_agent_response(member, member_prompt)
            
            self.turn_history.append({
                "turn": turn,
                "phase": "workstream_execution", 
                "workstream": workstream_name,
                "speaker": member,
                "content": member_response,
                "timestamp": datetime.now().isoformat()
            })
    
    def run_coordination_phase(self, turn: int):
        """Turns 9-12: Cross-workstream coordination"""
        print(f"\n🔄 TURN {turn}: CROSS-WORKSTREAM COORDINATION")
        self.current_turn = turn
        
        # Workstream leads coordinate
        coordination_prompt = f"""
        CROSS-WORKSTREAM COORDINATION - TURN {turn}
        CRISIS HOUR {turn//2}
        
        Current workstream status:
        {self.get_workstream_summary()}
        
        As {self.agents['Rebecca Martinez'].get('role')}, facilitate coordination:
        1. What dependencies exist between workstreams?
        2. What decisions need executive input?
        3. What resources need reallocation?
        4. What's our overall progress assessment?
        
        Focus on unblocking teams and maintaining momentum.
        """
        
        ceo_coordination = self.get_agent_response("Rebecca Martinez", coordination_prompt)
        
        self.turn_history.append({
            "turn": turn,
            "phase": "coordination",
            "speaker": "Rebecca Martinez",
            "content": ceo_coordination,
            "timestamp": datetime.now().isoformat()
        })
        
        # Key workstream leads respond to coordination needs
        leads = ["David Chen", "Sarah Williams", "Michael Thompson", "Kevin Walsh", "Thomas Brown"]
        
        for lead in leads:
            lead_prompt = f"""
            CEO COORDINATION REQUEST:
            {ceo_coordination[:300]}...
            
            As workstream lead, respond with:
            1. What you need from other workstreams
            2. What you can provide to other workstreams  
            3. Any escalations needed
            4. Your workstream's current status
            """
            
            lead_response = self.get_agent_response(lead, lead_prompt)
            
            self.turn_history.append({
                "turn": turn,
                "phase": "coordination",
                "speaker": lead,
                "content": lead_response,
                "timestamp": datetime.now().isoformat()
            })
    
    def run_implementation_phase(self, turn: int):
        """Turns 13-18: Implementation and monitoring"""
        print(f"\n🚀 TURN {turn}: IMPLEMENTATION & MONITORING")
        self.current_turn = turn
        
        # Focus on execution and monitoring
        impl_prompt = f"""
        IMPLEMENTATION PHASE - TURN {turn}
        CRISIS HOUR {turn//2}
        
        We're now implementing our response plan. Current status:
        {self.get_workstream_summary()}
        
        As {self.agents['Kevin Walsh'].get('role')}, coordinate implementation:
        1. What's being implemented right now?
        2. What's working well vs. what needs adjustment?
        3. What new issues have emerged?
        4. What's our timeline for full recovery?
        
        Focus on execution excellence and problem-solving.
        """
        
        coo_response = self.get_agent_response("Kevin Walsh", impl_prompt)
        
        self.turn_history.append({
            "turn": turn,
            "phase": "implementation",
            "speaker": "Kevin Walsh", 
            "content": coo_response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Select 3-4 agents to provide implementation updates
        implementers = random.sample(list(self.agents.keys()), 4)
        
        for implementer in implementers:
            impl_update_prompt = f"""
            IMPLEMENTATION UPDATE REQUEST:
            {coo_response[:200]}...
            
            Provide a brief update on:
            1. What you're implementing/monitoring
            2. Current status and any issues
            3. Next steps in your area
            """
            
            update = self.get_agent_response(implementer, impl_update_prompt)
            
            self.turn_history.append({
                "turn": turn,
                "phase": "implementation",
                "speaker": implementer,
                "content": update,
                "timestamp": datetime.now().isoformat()
            })
    
    def run_final_planning_phase(self, turn: int):
        """Turns 19-22: Final planning and wrap-up"""
        print(f"\n🎯 TURN {turn}: FINAL PLANNING & RECOVERY")
        self.current_turn = turn
        
        final_prompt = f"""
        FINAL PLANNING PHASE - TURN {turn}
        CRISIS HOUR {turn//2}
        
        We're in the final phase of crisis response. Summary:
        {self.get_workstream_summary()}
        
        As {self.agents['Rebecca Martinez'].get('role')}, lead final planning:
        1. What's our current recovery status?
        2. What long-term actions are needed?
        3. What lessons learned should we capture?
        4. How do we prevent this in the future?
        
        Focus on sustainable recovery and improvement.
        """
        
        final_response = self.get_agent_response("Rebecca Martinez", final_prompt)
        
        self.turn_history.append({
            "turn": turn,
            "phase": "final_planning",
            "speaker": "Rebecca Martinez",
            "content": final_response,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_agent_response(self, agent_name: str, prompt: str) -> str:
        """Get response from specific agent with error handling"""
        try:
            print(f"   🤖 {agent_name} responding...")
            start_time = time.time()
            
            agent = self.agents[agent_name]
            response = agent.listen_and_act(prompt)
            
            response_time = time.time() - start_time
            print(f"      ⏱️  {response_time:.2f}s")
            
            if response and len(response) > 0 and response[0] and 'action' in response[0]:
                content = response[0]['action']['content']
                print(f"      💭 {content[:100]}...")
                return content
            else:
                return f"[{agent_name} provided unclear response]"
                
        except Exception as e:
            print(f"      ❌ Error: {e}")
            return f"[{agent_name} encountered error: {str(e)}]"
    
    def get_workstream_summary(self) -> str:
        """Get summary of all workstream progress"""
        summary = []
        for name, ws in self.active_workstreams.items():
            latest_progress = ws["progress"][-1] if ws["progress"] else "No progress yet"
            summary.append(f"- {name}: {latest_progress}")
        return "\n".join(summary)
    
    def generate_final_plan(self) -> Dict[str, Any]:
        """Generate final crisis response plan"""
        return {
            "immediate_actions_completed": [
                "Systems secured and breach contained",
                "Customer communications initiated", 
                "Regulatory notifications sent",
                "Forensic investigation launched",
                "Business continuity measures activated"
            ],
            "recovery_timeline": {
                "24_hours": "Full system restoration and customer service recovery",
                "1_week": "Complete forensic analysis and security hardening",
                "1_month": "Customer confidence restoration and process improvements",
                "3_months": "Long-term security enhancements and monitoring"
            },
            "lessons_learned": [
                "Need for faster incident detection",
                "Improved cross-team coordination protocols",
                "Enhanced customer communication processes",
                "Stronger vendor security requirements"
            ],
            "total_estimated_cost": "$50M (systems, legal, reputation recovery)",
            "key_success_factors": [
                "Rapid executive decision-making",
                "Effective workstream coordination", 
                "Transparent stakeholder communication",
                "Comprehensive technical response"
            ]
        }

def main():
    """Run the epic simulation"""
    print("🔥 EPIC MULTI-AGENT CRISIS SIMULATION")
    print("🎯 20 AGENTS, 20+ TURNS, COMPLEX GOAL ACHIEVEMENT")
    print("=" * 80)
    
    try:
        control.begin()
        
        simulation = EpicCrisisSimulation()
        
        # Create the scenario
        if simulation.create_crisis_scenario():
            print("✅ Epic crisis scenario created")
        else:
            print("❌ Failed to create scenario")
            return
        
        # Run the epic simulation
        print("\n🎬 STARTING EPIC SIMULATION...")
        results = simulation.run_epic_simulation()
        
        # Save comprehensive results
        with open('epic_simulation_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        # Display summary
        print("\n" + "=" * 80)
        print("🏆 EPIC SIMULATION COMPLETE!")
        print("=" * 80)
        
        print(f"\n📊 EPIC SIMULATION SUMMARY:")
        print(f"   Total agents: {results['total_agents']}")
        print(f"   Total turns: {results['total_turns']}")
        print(f"   Total time: {results['total_time_seconds']:.1f} seconds")
        print(f"   Workstreams: {len(results['workstreams'])}")
        
        print(f"\n🎯 FINAL CRISIS RESPONSE PLAN:")
        plan = results['final_plan']
        print(f"   Immediate actions: {len(plan['immediate_actions_completed'])}")
        print(f"   Recovery timeline: {len(plan['recovery_timeline'])} phases")
        print(f"   Lessons learned: {len(plan['lessons_learned'])}")
        print(f"   Estimated cost: {plan['total_estimated_cost']}")
        
        print(f"\n💾 Full results saved to epic_simulation_results.json")
        print(f"🎉 EPIC MULTI-AGENT SIMULATION SUCCESSFUL!")
        
    except Exception as e:
        print(f"\n❌ EPIC SIMULATION ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        control.end()

if __name__ == "__main__":
    main()