#!/usr/bin/env python3
"""
REAL TinyTroupe Simulation with ACTUAL LLM calls
Now let's prove it REALLY works with genuine AI reasoning!
"""

import sys
import time
import json
from datetime import datetime

# Add the tinytroupe path
sys.path.insert(0, '.')

from tinytroupe.agent.tiny_person import TinyPerson
from tinytroupe.environment.tiny_world import TinyWorld
from tinytroupe import control

def create_real_simulation():
    """Create a REAL simulation with actual LLM-powered agents"""
    
    print("🚀 CREATING REAL SIMULATION WITH ACTUAL AI AGENTS")
    print("=" * 60)
    
    # Start a new simulation
    control.begin()
    
    # Create the world
    world = TinyWorld("Real Product Launch Decision")
    
    # Create CEO with detailed personality
    ceo = TinyPerson("Sarah Chen")
    ceo.define("age", 45)
    ceo.define("occupation", "CEO of TechCorp")
    ceo.define("personality", """You are Sarah Chen, CEO of TechCorp. You are a visionary leader with 15 years in tech who has led 3 successful IPOs. You are data-driven but willing to take calculated risks. You value innovation and customer satisfaction above short-term profits. You think strategically about long-term growth and market disruption. You consider multiple stakeholders in your decisions.""")
    ceo.define("background", "Former McKinsey consultant, Harvard MBA, built companies from startup to IPO")
    
    # Create CTO with technical focus
    cto = TinyPerson("Marcus Rodriguez")
    cto.define("age", 42)
    cto.define("occupation", "CTO of TechCorp")
    cto.define("personality", """You are Marcus Rodriguez, CTO of TechCorp. You are a technical perfectionist who prioritizes product quality and scalability above all else. You are cautious about rushing to market but passionate about cutting-edge technology. You have a PhD in Computer Science and were a Principal Engineer at Google. You strongly advocate for engineering excellence and are concerned about technical debt and system reliability.""")
    cto.define("background", "PhD Computer Science, former Google Principal Engineer, built systems serving billions of users")
    
    # Create CMO with marketing expertise
    cmo = TinyPerson("Jennifer Walsh")
    cmo.define("age", 38)
    cmo.define("occupation", "CMO of TechCorp")
    cmo.define("personality", """You are Jennifer Walsh, CMO of TechCorp. You are customer-obsessed with deep understanding of user psychology and market dynamics. You are aggressive about market timing and competitive positioning. You believe in bold, memorable campaigns and have launched 5 category-defining products at Apple. You think the market window is everything and competitors move fast.""")
    cmo.define("background", "Former VP Marketing at Apple, expert in consumer behavior, launched products used by millions")
    
    # Add agents to world
    world.add_agent(ceo)
    world.add_agent(cto)
    world.add_agent(cmo)
    
    print(f"✅ Created 3 AI-powered agents with detailed personalities")
    return world, [ceo, cto, cmo]

def run_real_business_simulation(world, agents):
    """Run actual business simulation with real AI reasoning"""
    
    print("\n🎯 RUNNING REAL BUSINESS SIMULATION")
    print("=" * 60)
    
    # Business scenario
    scenario = """
    URGENT BUSINESS DECISION NEEDED:
    
    TechCorp has developed ServiceAI, an AI customer service platform that handles 90% of inquiries automatically. 
    
    KEY FACTS:
    - Development cost: $15M over 18 months
    - Beta results: 85% customer satisfaction, 60% cost reduction
    - Market size: $12B annually, growing 25% per year
    - Competition: Zendesk, Salesforce moving fast
    - Technical status: 95% complete, some scalability concerns
    - Sales pipeline: $50M in deals waiting for launch
    
    DECISION: Should we launch immediately, delay 3 months for testing, or pivot?
    
    The board needs your recommendation by end of day.
    """
    
    results = {}
    
    # Get individual perspectives with REAL AI reasoning
    print("\n📋 PHASE 1: Getting REAL AI perspectives...")
    
    for agent in agents:
        print(f"\n🤔 {agent.name} ({agent.get('occupation')}) thinking...")
        
        # Create role-specific prompt
        prompt = f"""
        {scenario}
        
        As the {agent.get('occupation')}, what is your recommendation and reasoning?
        
        Consider:
        1. Your role's key priorities and concerns
        2. The risks and opportunities you see
        3. Your specific recommendation (Launch now / Delay 3 months / Pivot)
        4. What conditions you need for your support
        
        Be specific and business-focused. This is a real $50M decision.
        """
        
        # Get REAL AI response
        start_time = time.time()
        # Control system now handles async automatically
        response = agent.listen_and_act(prompt)
        response_time = time.time() - start_time
        
        print(f"   ⏱️  Response time: {response_time:.2f} seconds")
        
        # Handle response safely
        if response and len(response) > 0 and response[0] and 'action' in response[0]:
            content = response[0]['action']['content']
            print(f"   💭 {agent.name} says: {content[:200]}...")
            
            results[agent.name] = {
                "role": agent.get('occupation'),
                "response": content,
                "response_time": response_time
            }
        else:
            print(f"   ⚠️  {agent.name} didn't provide a clear response")
            results[agent.name] = {
                "role": agent.get('occupation'),
                "response": "No clear response provided",
                "response_time": response_time
            }
    
    # Now facilitate group discussion
    print(f"\n💬 PHASE 2: Group discussion with REAL AI interaction...")
    
    # Create group discussion prompt
    discussion_prompt = f"""
    We've heard everyone's individual perspectives:
    
    {chr(10).join([f"- {name}: {data['response'][:150]}..." for name, data in results.items()])}
    
    Now let's discuss as a team. What are the key points of agreement and disagreement? 
    Can we find a path forward that addresses everyone's concerns?
    
    Remember, we need to make a decision today on a $50M opportunity.
    """
    
    # Have CEO facilitate the discussion
    ceo = agents[0]  # Sarah Chen
    print(f"\n🎯 {ceo.name} facilitating group discussion...")
    
    start_time = time.time()
    group_response = ceo.listen_and_act(discussion_prompt)
    discussion_time = time.time() - start_time
    
    print(f"   ⏱️  Discussion time: {discussion_time:.2f} seconds")
    print(f"   🗣️  Group discussion result: {group_response[0]['action']['content'][:300]}...")
    
    # Final decision
    print(f"\n🎯 PHASE 3: Final decision making...")
    
    final_prompt = f"""
    Based on our discussion and everyone's input, I need to make the final decision as CEO.
    
    The key perspectives were:
    {chr(10).join([f"- {name} ({data['role']}): {data['response'][:100]}..." for name, data in results.items()])}
    
    Our group discussion concluded: {group_response[0]['action']['content'][:200]}...
    
    As CEO, what is my final decision and implementation plan? Be specific about:
    1. The decision (Launch/Delay/Pivot)
    2. Timeline and phases
    3. Budget allocation
    4. Success metrics
    5. Risk mitigation
    """
    
    start_time = time.time()
    final_decision = ceo.listen_and_act(final_prompt)
    decision_time = time.time() - start_time
    
    print(f"   ⏱️  Decision time: {decision_time:.2f} seconds")
    print(f"   ✅ Final decision: {final_decision[0]['action']['content'][:200]}...")
    
    return {
        "individual_perspectives": results,
        "group_discussion": {
            "facilitator": ceo.name,
            "content": group_response[0]['action']['content'],
            "response_time": discussion_time
        },
        "final_decision": {
            "decision_maker": ceo.name,
            "content": final_decision[0]['action']['content'],
            "response_time": decision_time
        },
        "total_agents": len(agents),
        "simulation_timestamp": datetime.now().isoformat()
    }

def main():
    """Run the REAL simulation demonstration"""
    print("🔥 REAL TINYTROUPE SIMULATION - WITH ACTUAL AI!")
    print("🎯 NO MORE MOCKING - THIS IS THE REAL DEAL!")
    print("=" * 80)
    
    try:
        # Create real simulation
        world, agents = create_real_simulation()
        
        # Run real business simulation
        print("\n🎬 STARTING REAL AI SIMULATION...")
        start_time = time.time()
        
        results = run_real_business_simulation(world, agents)
        
        total_time = time.time() - start_time
        results["total_simulation_time"] = total_time
        
        # Display comprehensive results
        print("\n" + "=" * 80)
        print("🏆 REAL AI SIMULATION RESULTS")
        print("=" * 80)
        
        print(f"\n📊 SIMULATION OVERVIEW:")
        print(f"   Total agents: {results['total_agents']}")
        print(f"   Total time: {total_time:.2f} seconds")
        print(f"   Timestamp: {results['simulation_timestamp']}")
        
        print(f"\n👥 INDIVIDUAL AI PERSPECTIVES:")
        for name, data in results['individual_perspectives'].items():
            print(f"\n   {name} ({data['role']}):")
            print(f"   Response time: {data['response_time']:.2f}s")
            print(f"   Full response: {data['response']}")
        
        print(f"\n💬 GROUP DISCUSSION:")
        discussion = results['group_discussion']
        print(f"   Facilitator: {discussion['facilitator']}")
        print(f"   Response time: {discussion['response_time']:.2f}s")
        print(f"   Discussion: {discussion['content']}")
        
        print(f"\n🎯 FINAL DECISION:")
        decision = results['final_decision']
        print(f"   Decision maker: {decision['decision_maker']}")
        print(f"   Response time: {decision['response_time']:.2f}s")
        print(f"   Final decision: {decision['content']}")
        
        # Save real results
        with open('real_simulation_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 REAL results saved to real_simulation_results.json")
        print(f"\n🎉 REAL AI SIMULATION COMPLETE!")
        print(f"   Total processing time: {total_time:.2f} seconds")
        
    except Exception as e:
        print(f"\n❌ SIMULATION ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # End simulation
        control.end()

if __name__ == "__main__":
    main()