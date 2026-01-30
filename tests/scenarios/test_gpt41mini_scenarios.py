"""
GPT-4.1-mini Compatibility Tests

This module tests TinyTroupe functionality using the gpt-4.1-mini model to ensure
compatibility with alternative models beyond the primary supported model.

These tests are designed to be:
- Concise but dense: covering multiple utilities per scenario
- Small-scale: 3 agents max per scenario
- Comprehensive: covering manual creation, file loading, factories, extractors, 
  enrichers, document creation, and export

Use the pytest marker @pytest.mark.gpt41mini to run these tests specifically:
    pytest -m "gpt41mini" --use_cache
"""

import os
import pytest
import logging
import textwrap

logger = logging.getLogger("tinytroupe")

import sys
sys.path.insert(0, '..')
sys.path.insert(0, '../../')
sys.path.insert(0, '../../tinytroupe/')

from tinytroupe import config_manager
from tinytroupe.agent import TinyPerson, TinyToolUse
from tinytroupe.environment import TinyWorld
from tinytroupe.factory import TinyPersonFactory
from tinytroupe.extraction import ResultsExtractor, ArtifactExporter
from tinytroupe.enrichment import TinyEnricher
from tinytroupe.tools import TinyWordProcessor
import tinytroupe.control as control

from tinytroupe.examples import (
    create_lisa_the_data_scientist,
    create_oscar_the_architect,
    create_marcos_the_physician,
)

from testing_utils import *


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def gpt41mini_config(setup):
    """
    Configure gpt-4.1-mini model for tests.
    
    This fixture:
    1. Saves the original model configuration
    2. Sets gpt-4.1-mini with explicit model parameters
    3. Restores original config after test
    
    Note: gpt-4.1-mini has a max token limit of 32768, unlike gpt-5-mini's 128000.
    """
    # Save original configuration
    original_model = config_manager.get("model")
    original_temp = config_manager.get("temperature")
    original_max_tokens = config_manager.get("max_completion_tokens")
    original_top_p = config_manager.get("top_p")
    original_freq_penalty = config_manager.get("frequency_penalty")
    
    # Set gpt-4.1-mini configuration with explicit parameters
    # Note: gpt-4.1-mini supports max 32768 completion tokens
    config_manager.update("model", "gpt-4.1-mini")
    config_manager.update("temperature", 0.7)
    config_manager.update("max_completion_tokens", 32768)
    config_manager.update("top_p", 0.95)
    config_manager.update("frequency_penalty", 0.0)
    
    # Print model configuration for visual verification
    print("\n" + "="*70)
    print("GPT-4.1-MINI TEST CONFIGURATION")
    print("="*70)
    print(f"  Model:                 {config_manager.get('model')}")
    print(f"  Temperature:           {config_manager.get('temperature')}")
    print(f"  Top P:                 {config_manager.get('top_p')}")
    print(f"  Frequency Penalty:     {config_manager.get('frequency_penalty')}")
    print(f"  Max Completion Tokens: {config_manager.get('max_completion_tokens')}")
    print(f"  API Type:              {config_manager.get('api_type')}")
    print(f"  Timeout:               {config_manager.get('timeout')}")
    print("="*70 + "\n")
    
    logger.info(f"Switched to gpt-4.1-mini (original: {original_model}, max_tokens: {original_max_tokens} -> 32768)")
    
    yield
    
    # Restore original config
    config_manager.update("model", original_model)
    config_manager.update("max_completion_tokens", original_max_tokens)
    config_manager.update("top_p", original_top_p)
    config_manager.update("frequency_penalty", original_freq_penalty)
    if original_temp is not None:
        config_manager.update("temperature", original_temp)
    else:
        # Reset to default if temperature was None
        config_manager.reset()
    
    logger.info(f"Restored model to {original_model}")


# ============================================================================
# TEST CLASS
# ============================================================================

@pytest.mark.gpt41mini
class TestGPT41MiniScenarios:
    """
    Test scenarios using gpt-4.1-mini model.
    
    Each test is designed to be dense, covering multiple TinyTroupe utilities
    in a single credible simulation scenario.
    """

    def test_manual_agents_with_extraction_and_export(self, gpt41mini_config):
        """
        Scenario: Product Feedback Session
        
        Covers:
        - Manual agent creation (using example functions)
        - TinyWorld simulation
        - ResultsExtractor for agent and world extraction
        - ArtifactExporter for JSON/text export
        """
        control.reset()
        
        # Create agents manually using example functions
        lisa = create_lisa_the_data_scientist()
        oscar = create_oscar_the_architect()
        marcos = create_marcos_the_physician()
        
        # Create world
        world = TinyWorld("Product Feedback Session", [lisa, oscar, marcos])
        world.make_everyone_accessible()
        
        # Run simulation
        world.broadcast(
            """
            We're evaluating a new AI-powered health monitoring app that combines 
            architectural design principles with data analytics. Each of you, please 
            share your professional perspective on this product concept.
            """
        )
        world.run(2)
        
        # Test ResultsExtractor - from agent
        extractor = ResultsExtractor()
        agent_results = extractor.extract_results_from_agent(
            lisa,
            extraction_objective="Extract key insights about data and analytics aspects",
            situation="Product feedback session",
            fields=["data_insights", "recommendations"],
            fields_hints={
                "data_insights": "Key observations about data handling",
                "recommendations": "Suggested improvements"
            }
        )
        
        assert agent_results is not None, "Agent extraction should return results"
        assert isinstance(agent_results, dict), "Results should be a dictionary"
        
        # Test ResultsExtractor - from world
        world_results = extractor.extract_results_from_world(
            world,
            extraction_objective="Summarize the group's collective feedback",
            situation="Multi-disciplinary product review"
        )
        
        assert world_results is not None, "World extraction should return results"
        
        # Test ArtifactExporter
        exporter = ArtifactExporter(base_output_folder=get_relative_to_test_path(f"{EXPORT_BASE_FOLDER}/gpt41mini/"))
        
        # Export as JSON - must include 'content' key for ArtifactExporter
        exporter.export(
            artifact_name="feedback_session_results",
            artifact_data={
                "content": str(agent_results),  # content key required by ArtifactExporter
                "agent_results": agent_results, 
                "world_results": world_results
            },
            content_type="Results",  # Use descriptive content type (creates Results subfolder)
            target_format="json"
        )
        
        # Export as text  
        exporter.export(
            artifact_name="feedback_summary",
            artifact_data=str(world_results),
            content_type="Text",
            target_format="txt"
        )
        
        # Verify files were created (note: files go in subfolder based on content_type)
        json_path = get_relative_to_test_path(f"{EXPORT_BASE_FOLDER}/gpt41mini/Results/feedback_session_results.json")
        assert os.path.exists(json_path), "JSON export file should exist"
        
        # Semantic verification
        assert proposition_holds(
            f"The following contains product feedback or professional insights: '{world_results}'"
        ), "World results should contain relevant feedback"

    def test_loaded_agents_with_enrichment_and_docx(self, gpt41mini_config):
        """
        Scenario: Technical Documentation Workshop
        
        Covers:
        - Loading agents from specification files
        - TinyEnricher for content enrichment
        - ArtifactExporter for DOCX export
        - Agent state serialization
        """
        control.reset()
        
        # Load agents from files
        oscar = TinyPerson.load_specification(
            get_relative_to_test_path("../examples/agents/Oscar.agent.json"),
            new_agent_name="Oscar_Loaded"
        )
        lisa = TinyPerson.load_specification(
            get_relative_to_test_path("../examples/agents/Lisa.agent.json"),
            new_agent_name="Lisa_Loaded"
        )
        
        assert oscar is not None, "Oscar should be loaded from file"
        assert lisa is not None, "Lisa should be loaded from file"
        
        # Create world with loaded agents
        world = TinyWorld("Documentation Workshop", [oscar, lisa])
        world.make_everyone_accessible()
        
        # Generate content through simulation
        world.broadcast(
            """
            You are writing a brief technical guide about integrating AI into existing 
            workflows. Each person should contribute their expertise. Keep it concise 
            but insightful.
            """
        )
        world.run(1)
        
        # Have Oscar summarize
        oscar.listen_and_act("Please provide a brief outline of the key integration points.")
        
        # Extract from Oscar
        extractor = ResultsExtractor()
        outline = extractor.extract_results_from_agent(
            oscar,
            extraction_objective="Extract the technical integration outline",
            fields=["key_points", "implementation_steps"]
        )
        
        # Test TinyEnricher
        draft_content = textwrap.dedent(f"""
        # AI Integration Guide
        
        ## Overview
        Key integration points for AI in workflows.
        
        ## Summary
        {outline}
        """).strip()
        
        enriched_content = TinyEnricher().enrich_content(
            requirements="Expand this outline into a more detailed section with examples. Add at least 2x more content.",
            content=draft_content,
            content_type="Technical Documentation",
            context_info="A guide for professionals on AI integration",
            verbose=False
        )
        
        assert enriched_content is not None, "Enriched content should not be None"
        assert len(enriched_content) > len(draft_content), "Enriched content should be longer"
        
        # Test DOCX export - content_format='md' required for DOCX conversion
        exporter = ArtifactExporter(base_output_folder=get_relative_to_test_path(f"{EXPORT_BASE_FOLDER}/gpt41mini/"))
        exporter.export(
            artifact_name="ai_integration_guide",
            artifact_data=enriched_content,
            content_type="Document",
            content_format="md",
            target_format="docx"
        )
        
        docx_path = get_relative_to_test_path(f"{EXPORT_BASE_FOLDER}/gpt41mini/Document/ai_integration_guide.docx")
        assert os.path.exists(docx_path), f"DOCX file should exist at {docx_path}"
        
        # Test agent state serialization
        state = oscar.encode_complete_state()
        assert state is not None, "Agent state should be serializable"
        assert "name" in state, "State should contain agent name"

    def test_factory_single_and_population_generation(self, gpt41mini_config):
        """
        Scenario: Market Research Focus Group Creation
        
        Covers:
        - TinyPersonFactory single agent generation
        - TinyPersonFactory population generation (3 agents)
        - Post-processing hooks
        - Basic agent interaction
        - ResultsExtractor for synthesizing research findings
        """
        control.reset()
        
        # Test single agent generation
        factory = TinyPersonFactory(
            "Market research participants interested in consumer technology products."
        )
        
        single_agent = factory.generate_person(
            "A tech-savvy millennial who frequently adopts new gadgets.",
            temperature=0.8
        )
        
        assert single_agent is not None, "Single agent should be generated"
        assert single_agent.get("age") is not None, "Agent should have age defined"
        
        # Test population generation with post-processing
        def add_research_context(agent):
            """Post-processing hook to add research context."""
            agent.define("research_role", "focus_group_participant")
            return agent
        
        population = factory.generate_people(
            number_of_people=3,
            agent_particularities="Diverse professionals with different tech adoption patterns",
            post_processing_func=add_research_context,
            temperature=0.7
        )
        
        assert len(population) == 3, "Should generate exactly 3 agents"
        
        # Verify post-processing was applied
        for agent in population:
            assert agent.get("research_role") == "focus_group_participant", \
                "Post-processing should add research_role"
        
        # Create focus group with generated population
        world = TinyWorld("Tech Product Focus Group", [single_agent] + population)
        world.make_everyone_accessible()
        
        # Run market research simulation
        world.broadcast(
            """
            We're researching reactions to a new smart home device priced at $199.
            Would you consider purchasing it? Share your honest thoughts and concerns.
            """
        )
        world.run(2)
        
        # Extract market research findings
        extractor = ResultsExtractor()
        findings = extractor.extract_results_from_world(
            world,
            extraction_objective="Synthesize market research findings: purchase intent, concerns, and suggestions",
            situation="Consumer focus group for smart home product",
            fields=["purchase_intent_summary", "main_concerns", "suggestions"],
            fields_hints={
                "purchase_intent_summary": "Overall sentiment toward purchasing",
                "main_concerns": "Key objections or worries raised",
                "suggestions": "Product improvements mentioned"
            }
        )
        
        assert findings is not None, "Should extract market research findings"
        assert isinstance(findings, dict), "Findings should be structured"
        
        # Semantic verification
        assert proposition_holds(
            f"The following contains consumer feedback about a product: '{findings}'"
        ), "Findings should contain consumer feedback"

    def test_tool_usage_with_document_creation(self, gpt41mini_config):
        """
        Scenario: Collaborative Report Writing
        
        Covers:
        - TinyToolUse with TinyWordProcessor
        - Document creation through agent tool usage
        - Multi-agent collaboration on document
        - Export verification
        """
        control.reset()
        
        # Setup exporter and enricher for the word processor
        exporter = ArtifactExporter(base_output_folder=get_relative_to_test_path(f"{EXPORT_BASE_FOLDER}/gpt41mini/"))
        enricher = TinyEnricher()
        word_processor = TinyWordProcessor(exporter=exporter, enricher=enricher)
        
        # Create tool-using faculty
        tooluse = TinyToolUse(tools=[word_processor])
        
        # Create agents with tool capability
        lisa = create_lisa_the_data_scientist()
        lisa.add_mental_faculties([tooluse])
        
        oscar = create_oscar_the_architect()  
        oscar.add_mental_faculties([tooluse])
        
        # Create collaborative world
        world = TinyWorld("Report Writing Team", [lisa, oscar])
        world.make_everyone_accessible()
        
        # Prompt document creation
        world.broadcast(
            """
            You need to collaboratively create a brief report about "AI in Professional Workflows".
            Use the word processor tool to write your section. Lisa should cover data aspects,
            Oscar should cover design aspects. Keep each section to 2-3 paragraphs.
            """
        )
        
        # Run with tool usage
        world.run(3)
        
        # Verify agents responded
        for agent in [lisa, oscar]:
            actions = agent.pop_actions_and_get_contents_for("WRITE", False)
            if actions:
                logger.info(f"{agent.name} created document content")
        
        # Extract collaboration results
        extractor = ResultsExtractor()
        report_summary = extractor.extract_results_from_world(
            world,
            extraction_objective="Summarize the collaborative report content created",
            situation="Professional report writing session"
        )
        
        assert report_summary is not None, "Should extract report summary"

    def test_demography_factory_with_full_pipeline(self, gpt41mini_config):
        """
        Scenario: Demographic Survey Simulation
        
        Covers:
        - TinyPersonFactory.create_factory_from_demography (dict-based)
        - Complete pipeline: generation -> simulation -> extraction -> export
        - State encode/decode for agents and world
        """
        control.reset()
        
        # Create factory from demography specification (dict-based, not file)
        demography_spec = {
            "population_description": "American consumers from diverse backgrounds",
            "demographic_dimensions": {
                "age_group": ["young_adult (18-30)", "middle_aged (31-50)", "senior (51+)"],
                "income_level": ["low_income", "middle_income", "high_income"],
                "tech_affinity": ["early_adopter", "mainstream", "late_adopter"]
            }
        }
        
        factory = TinyPersonFactory.create_factory_from_demography(
            demography_description_or_file_path=demography_spec,
            population_size=3,
            context="Consumer survey participants for market research"
        )
        
        # Generate small population
        participants = factory.generate_people(
            number_of_people=3,
            agent_particularities="Willing to share opinions on consumer products"
        )
        
        assert len(participants) == 3, "Should generate 3 participants"
        
        # Create survey world
        world = TinyWorld("Consumer Survey", participants)
        world.make_everyone_accessible()
        
        # Run survey simulation
        survey_question = """
        On a scale of 1-10, how likely are you to purchase an AI-powered personal assistant?
        Please explain your rating based on your personal situation and preferences.
        """
        
        world.broadcast(survey_question)
        world.run(2)
        
        # Extract structured survey results
        extractor = ResultsExtractor()
        survey_results = extractor.extract_results_from_world(
            world,
            extraction_objective="Extract survey responses with ratings and justifications",
            situation="Consumer survey about AI products",
            fields=["responses", "overall_sentiment", "key_themes"],
            fields_hints={
                "responses": "Individual participant responses with ratings",
                "overall_sentiment": "Aggregate sentiment (positive/neutral/negative)",
                "key_themes": "Common themes across responses"
            }
        )
        
        assert survey_results is not None, "Should extract survey results"
        
        # Test world state encoding
        world_state = world.encode_complete_state()
        assert world_state is not None, "World state should be encodable"
        assert "agents" in world_state, "World state should contain agents"
        
        # Test world state decoding (decode_complete_state is an instance method)
        restored_world = TinyWorld("Restored Survey", [])  # Create empty world first
        restored_world.decode_complete_state(world_state)  # Then restore state
        assert restored_world is not None, "World should be restorable"
        assert len(restored_world.agents) == 3, "Restored world should have 3 agents"
        
        # Export final results - must include 'content' key for ArtifactExporter
        exporter = ArtifactExporter(base_output_folder=get_relative_to_test_path(f"{EXPORT_BASE_FOLDER}/gpt41mini/"))
        exporter.export(
            artifact_name="survey_results_demography",
            artifact_data={
                "content": str(survey_results),  # content key required
                "results": survey_results, 
                "participant_count": 3
            },
            content_type="Survey",  # Use descriptive content type
            target_format="json"
        )
        
        # Verify semantic quality
        assert proposition_holds(
            f"The following contains survey responses about AI products: '{survey_results}'"
        ), "Results should contain survey responses"

    def test_mixed_agents_comprehensive_workflow(self, gpt41mini_config):
        """
        Scenario: Innovation Workshop (Comprehensive)
        
        This test combines ALL major utilities in one dense scenario:
        - Manual agent creation
        - Loaded agent from file  
        - Factory-generated agent
        - TinyWorld simulation
        - ResultsExtractor (agent + world)
        - TinyEnricher
        - ArtifactExporter (JSON + DOCX)
        - State serialization
        """
        control.reset()
        
        # 1. Manual agent creation
        manual_agent = create_marcos_the_physician()
        
        # 2. Load agent from file
        loaded_agent = TinyPerson.load_specification(
            get_relative_to_test_path("../examples/agents/Oscar.agent.json"),
            new_agent_name="Oscar_Workshop"
        )
        
        # 3. Factory-generated agent
        factory = TinyPersonFactory("Innovation workshop participants with diverse expertise.")
        generated_agent = factory.generate_person(
            "A healthcare technology specialist interested in digital innovation."
        )
        
        # Combine all agent types
        agents = [manual_agent, loaded_agent, generated_agent]
        assert len(agents) == 3, "Should have 3 agents from different sources"
        
        # Create comprehensive workshop world
        world = TinyWorld("Innovation Workshop", agents)
        world.make_everyone_accessible()
        
        # Run multi-phase simulation
        world.broadcast(
            """
            Welcome to the Healthcare Innovation Workshop. We're brainstorming ideas 
            for improving patient experience using AI and design thinking.
            Phase 1: Share your perspective on current challenges.
            """
        )
        world.run(1)
        
        world.broadcast(
            """
            Phase 2: Propose one concrete solution based on your expertise.
            Be specific about implementation.
            """
        )
        world.run(1)
        
        # Extract from individual agent (Marcos - manual)
        extractor = ResultsExtractor()
        physician_insights = extractor.extract_results_from_agent(
            manual_agent,
            extraction_objective="Extract healthcare professional insights on patient experience",
            fields=["challenges_identified", "proposed_solution"]
        )
        
        # Extract from world (all agents)
        workshop_synthesis = extractor.extract_results_from_world(
            world,
            extraction_objective="Synthesize all innovation ideas from the workshop",
            situation="Multi-disciplinary healthcare innovation workshop",
            fields=["innovation_ideas", "implementation_priorities", "consensus_points"]
        )
        
        # Enrich the workshop findings into a report
        draft_report = f"""
        # Healthcare Innovation Workshop Report
        
        ## Physician Perspective
        {physician_insights}
        
        ## Workshop Synthesis  
        {workshop_synthesis}
        """
        
        enriched_report = TinyEnricher().enrich_content(
            requirements="Expand into a professional workshop report with executive summary and action items. Make it at least 2x longer.",
            content=draft_report,
            content_type="Workshop Report",
            context_info="Healthcare innovation brainstorming session",
            verbose=False
        )
        
        assert enriched_report is not None, "Enriched report should be generated"
        assert len(enriched_report) > len(draft_report), "Report should be expanded"
        
        # Export comprehensive results
        exporter = ArtifactExporter(base_output_folder=get_relative_to_test_path(f"{EXPORT_BASE_FOLDER}/gpt41mini/"))
        
        # JSON export with structured data - must include 'content' key
        exporter.export(
            artifact_name="workshop_comprehensive_data",
            artifact_data={
                "content": str(workshop_synthesis),  # content key required
                "physician_insights": physician_insights,
                "workshop_synthesis": workshop_synthesis,
                "agents": [a.name for a in agents],
                "agent_sources": ["manual", "file", "factory"]
            },
            content_type="Workshop",  # Use descriptive content type
            target_format="json"
        )
        
        # DOCX export with enriched report - content_format='md' required
        exporter.export(
            artifact_name="workshop_final_report",
            artifact_data=enriched_report,
            content_type="Document",
            content_format="md",
            target_format="docx"
        )
        
        # Verify exports (note: files go in subfolder based on content_type)
        json_path = get_relative_to_test_path(f"{EXPORT_BASE_FOLDER}/gpt41mini/Workshop/workshop_comprehensive_data.json")
        docx_path = get_relative_to_test_path(f"{EXPORT_BASE_FOLDER}/gpt41mini/Document/workshop_final_report.docx")
        
        assert os.path.exists(json_path), "JSON export should exist"
        assert os.path.exists(docx_path), f"DOCX export should exist at {docx_path}"
        
        # Test state serialization for all agents
        for agent in agents:
            state = agent.encode_complete_state()
            assert state is not None, f"{agent.name} state should be serializable"
        
        # Test world state
        world_state = world.encode_complete_state()
        assert world_state is not None, "World state should be serializable"
        
        # Final semantic verification
        assert proposition_holds(
            f"The following is a healthcare innovation workshop report: '{enriched_report[:500]}'"
        ), "Report should be about healthcare innovation"
