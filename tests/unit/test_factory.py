import pytest
import os
import json
import tempfile

import sys
# Insert paths at the beginning of sys.path (position 0)
sys.path.insert(0, '..')
sys.path.insert(0, '../../')
sys.path.insert(0, '../../tinytroupe/')

from tinytroupe.examples import create_oscar_the_architect
from tinytroupe.control import Simulation
import tinytroupe.control as control
from tinytroupe.factory import TinyPersonFactory
from tinytroupe.agent import TinyPerson

from testing_utils import *

def test_generate_person(setup):
    """Test basic single person generation with simple context."""
    bank_spec =\
    """
    A large brazillian bank. It has a lot of branches and a large number of employees. It is facing a lot of competition from fintechs.
    """

    banker_spec =\
    """
    A vice-president of one of the largest brazillian banks. Has a degree in engineering and an MBA in finance.
    """
    
    banker_factory = TinyPersonFactory(context=bank_spec)
    banker = banker_factory.generate_person(banker_spec)
    minibio = banker.minibio()

    assert proposition_holds(f"The following is an acceptable short description for someone working in banking: '{minibio}'"), f"Proposition is false according to the LLM."


def test_generate_person_with_different_temperatures(setup):
    """Test person generation with different temperature settings."""
    context = "A technology startup focused on AI innovations."
    
    factory = TinyPersonFactory(context=context)
    
    # Test with low temperature (more deterministic)
    person_low_temp = factory.generate_person("A software engineer", temperature=0.1)
    
    # Test with high temperature (more creative)
    person_high_temp = factory.generate_person("A software engineer", temperature=1.9)
    
    assert person_low_temp is not None
    assert person_high_temp is not None
    assert person_low_temp.name != person_high_temp.name  # Should be different people


def test_generate_person_with_post_processing(setup):
    """Test person generation with post-processing function."""
    context = "A consulting firm."
    
    def add_consultant_trait(agent):
        """Post-processing function to add a specific trait."""
        agent.define("consultant_level", "senior")
        agent.define("certification", "PMP")
    
    factory = TinyPersonFactory(context=context)
    consultant = factory.generate_person("A management consultant", post_processing_func=add_consultant_trait)
    
    assert consultant.get("consultant_level") == "senior"
    assert consultant.get("certification") == "PMP"


def test_generate_people(setup):
    """Test basic multiple people generation."""
    general_context = "We are performing some market research, and in that examining the whole of the American population."
    sampling_space_description = "A uniform random representative sample of people from the American population."

    factory = TinyPersonFactory(sampling_space_description=sampling_space_description, total_population_size=50, context=general_context)
    people = factory.generate_people(10, agent_particularities="A random person from the American population.", verbose=True)

    assert len(people) == 10
    for person in people:
        assert person.get("nationality") == "American"
        assert person.get("age") > 0
        assert person.name is not None


def test_generate_people_2(setup):
    """Test generating people equal to population size."""
    general_context = "We are performing some market research, and in that examining the whole of the American population."
    sampling_space_description = "A uniform random representative sample of people from the American population."

    factory = TinyPersonFactory(sampling_space_description=sampling_space_description, total_population_size=20, context=general_context)
    people = factory.generate_people(20, agent_particularities="A random person from the American population.", verbose=True)

    assert len(people) == 20
    for person in people:
        assert person.get("nationality") == "American"
        assert person.get("age") > 0
        assert person.name is not None


def test_generate_people_with_different_particularities(setup):
    """Test generating people with different agent particularities."""
    context = "A diverse urban community."
    sampling_space_description = "A representative sample of urban professionals and residents."
    
    factory = TinyPersonFactory(sampling_space_description=sampling_space_description, total_population_size=30, context=context)
    
    # Generate professionals
    professionals = factory.generate_people(5, agent_particularities="Working professionals in various fields", verbose=True)
    
    # Generate students  
    students = factory.generate_people(3, agent_particularities="College students from diverse backgrounds", verbose=True)
    
    assert len(professionals) == 5
    assert len(students) == 3
    
    # Check that people have reasonable characteristics
    for person in professionals + students:
        assert person.name is not None
        assert len(person.minibio()) > 50  # Should have substantial description


def test_generate_people_with_post_processing(setup):
    """Test generating multiple people with post-processing function."""
    context = "A research institution."
    
    def add_research_credentials(agent):
        """Add research-related attributes to each agent."""
        agent.define("institution", "Research Institute")
        agent.define("security_clearance", "Level 2")
    
    factory = TinyPersonFactory(context=context)
    researchers = factory.generate_people(3, 
                                         agent_particularities="Academic researchers", 
                                         post_processing_func=add_research_credentials)
    
    assert len(researchers) == 3
    for researcher in researchers:
        assert researcher.get("institution") == "Research Institute"
        assert researcher.get("security_clearance") == "Level 2"


def test_create_factory_from_demography_file(setup):
    """Test creating factory from demographic JSON file."""
    # Create a temporary demographic file
    demography_data = {
        "country": "Brazil",
        "age_distribution": {
            "18-30": 0.3,
            "31-50": 0.4,
            "51+": 0.3
        },
        "gender_distribution": {
            "male": 0.48,
            "female": 0.52
        },
        "education_levels": {
            "high_school": 0.4,
            "university": 0.4,
            "postgraduate": 0.2
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(demography_data, f)
        temp_file_path = f.name
    
    try:
        factory = TinyPersonFactory.create_factory_from_demography(temp_file_path, population_size=15)
        people = factory.generate_people(5, verbose=True)
        
        assert len(people) == 5
        for person in people:
            assert person.name is not None
            # Should have reasonable characteristics based on Brazilian demographics
            
    finally:
        os.unlink(temp_file_path)


def test_create_factory_from_demography_dict(setup):
    """Test creating factory from demographic dictionary."""
    demography_data = {
        "country": "Canada", 
        "age_distribution": {
            "20-35": 0.4,
            "36-55": 0.4,
            "56+": 0.2
        },
        "profession_distribution": {
            "technology": 0.3,
            "healthcare": 0.2,
            "education": 0.2,
            "other": 0.3
        }
    }
    
    factory = TinyPersonFactory.create_factory_from_demography(demography_data, population_size=12, context="Canadian professionals")
    people = factory.generate_people(4, verbose=True)
    
    assert len(people) == 4
    for person in people:
        assert person.name is not None


def test_multiple_factories_sequentially(setup):
    """Test creating and using multiple factories one after another."""
    # First factory for investment firm
    investment_context = "InvesTastic is a financial services firm that specializes in providing highly customized investment advice."
    
    investment_factory = TinyPersonFactory(context=investment_context)
    analysts = investment_factory.generate_people(2, agent_particularities="Financial analysts specialized in different sectors.")
    
    # Second factory for travel industry
    travel_context = "A travel company focused on luxury vacation packages."
    
    travel_factory = TinyPersonFactory(context=travel_context)  
    agents = travel_factory.generate_people(2, agent_particularities="Travel agents and customer service representatives.")
    
    # Third factory for market research
    research_context = "Market research company examining consumer behavior."
    
    research_factory = TinyPersonFactory(context=research_context)
    participants = research_factory.generate_people(3, agent_particularities="Diverse consumers from different demographics.")
    
    # Verify all factories worked independently
    assert len(analysts) == 2
    assert len(agents) == 2  
    assert len(participants) == 3
    
    # Check that people from different factories have different characteristics
    all_people = analysts + agents + participants
    names = [person.name for person in all_people]
    assert len(set(names)) == len(names)  # All names should be unique


def test_multiple_factories_same_context_different_particularities(setup):
    """Test multiple factories with same context but different agent particularities."""
    context = "A large university with diverse academic departments."
    
    # Faculty factory
    faculty_factory = TinyPersonFactory(context=context)
    faculty = faculty_factory.generate_people(2, agent_particularities="University professors from different academic disciplines.")
    
    # Student factory  
    student_factory = TinyPersonFactory(context=context)
    students = student_factory.generate_people(3, agent_particularities="Graduate and undergraduate students.")
    
    # Staff factory
    staff_factory = TinyPersonFactory(context=context) 
    staff = staff_factory.generate_people(2, agent_particularities="Administrative and support staff.")
    
    assert len(faculty) == 2
    assert len(students) == 3
    assert len(staff) == 2
    
    # Verify different roles/characteristics
    all_people = faculty + students + staff
    for person in all_people:
        assert person.name is not None
        bio = person.minibio().lower()
        # Should contain university-related terms
        assert any(term in bio for term in ['university', 'academic', 'student', 'professor', 'staff', 'education'])


def test_factory_with_sampling_plan_initialization(setup):
    """Test factory that uses sampling plan initialization."""
    sampling_space_description = """
    A diverse group of American professionals including:
    - Various age groups from 25 to 65
    - Different educational backgrounds
    - Multiple industry sectors
    - Different income levels
    """
    context = "Professional market research study."
    
    factory = TinyPersonFactory(
        sampling_space_description=sampling_space_description,
        total_population_size=20,
        context=context
    )
    
    # Generate subset of population
    people = factory.generate_people(5, agent_particularities="Working professionals", verbose=True)
    
    assert len(people) == 5
    for person in people:
        assert person.name is not None
        assert person.get("age") is not None
        
    # Should be able to generate more from same factory
    more_people = factory.generate_people(3, agent_particularities="Senior executives", verbose=True)
    assert len(more_people) == 3


def test_factory_population_size_constraints(setup):
    """Test population size constraints and error handling."""
    factory = TinyPersonFactory(
        sampling_space_description="Small sample of 5 people",
        total_population_size=5,
        context="Limited population test"
    )
    
    # Should work fine within limits
    people = factory.generate_people(3)
    assert len(people) == 3
    
    # Should be able to generate remaining people
    remaining = factory.generate_people(2)
    assert len(remaining) == 2
    
    # Now trying to generate more should return an empty list (i.e., fail silently)
    res = factory.generate_people(1)
    assert len(res) == 0


def test_factory_name_uniqueness_across_factories(setup):
    """Test that names remain unique across multiple factory instances."""
    context1 = "Technology startup in Silicon Valley."
    context2 = "Financial services firm in New York."
    context3 = "Healthcare organization in Boston."
    
    factory1 = TinyPersonFactory(context=context1)
    factory2 = TinyPersonFactory(context=context2)
    factory3 = TinyPersonFactory(context=context3)
    
    people1 = factory1.generate_people(3, agent_particularities="Software engineers and designers.")
    people2 = factory2.generate_people(3, agent_particularities="Financial analysts and advisors.")
    people3 = factory3.generate_people(3, agent_particularities="Doctors and nurses.")
    
    all_people = people1 + people2 + people3
    names = [person.name for person in all_people]
    
    # All names should be unique across factories
    assert len(set(names)) == len(names), f"Duplicate names found: {names}"


def test_factory_error_handling(setup):
    """Test error handling in factory operations."""
    # Test invalid demography input
    with pytest.raises(ValueError, match="must be either a string or a dictionary"):
        TinyPersonFactory.create_factory_from_demography(123, population_size=10)
    
    # Test missing population size in demography factory
    with pytest.raises(ValueError, match="population_size must be specified"):
        TinyPersonFactory.create_factory_from_demography({}, population_size=None)
    
    # Test requesting more people than population size
    factory = TinyPersonFactory(
        sampling_space_description="Very small sample",
        total_population_size=3,
        context="Error test"
    )
    
    with pytest.raises(ValueError, match="Cannot generate more people than the population size"):
        factory.generate_people(5)


def test_factory_complex_market_research_scenario(setup):
    """Test complex scenario similar to travel market research notebook."""
    # Create multiple factories for different market segments
    singles_factory = TinyPersonFactory(
        sampling_space_description="Single adults aged 25-45 from various backgrounds",
        total_population_size=20,
        context="Travel market research for singles segment"
    )
    
    families_factory = TinyPersonFactory(
        sampling_space_description="Married couples with children from diverse backgrounds", 
        total_population_size=20,
        context="Travel market research for families segment"
    )
    
    couples_factory = TinyPersonFactory(
        sampling_space_description="Married or dating couples without children",
        total_population_size=20, 
        context="Travel market research for couples segment"
    )
    
    # Generate people from each segment
    singles = singles_factory.generate_people(5, agent_particularities="Single adults interested in travel")
    families = families_factory.generate_people(5, agent_particularities="Parents planning family vacations") 
    couples = couples_factory.generate_people(5, agent_particularities="Couples seeking romantic getaways")
    
    # Verify each segment
    assert len(singles) == 5
    assert len(families) == 5 
    assert len(couples) == 5
    
    # Check that different segments have appropriate characteristics
    for person in singles + families + couples:
        assert person.name is not None
        bio = person.minibio()
        assert len(bio) > 30  # Should have substantial biography
    
    # Names should be unique across all segments
    all_names = [p.name for p in singles + families + couples]
    assert len(set(all_names)) == len(all_names)


def test_large_scale_generation_multiple_industries(setup):
    """Test generating large numbers of people (100 per factory) across multiple industry factories."""
    # Create factories for different industries
    tech_factory = TinyPersonFactory(
        sampling_space_description="Technology professionals including software engineers, data scientists, product managers, and UX designers from diverse backgrounds",
        total_population_size=110,  # Slightly more than target to allow for some variation
        context="Large tech company workforce analysis"
    )
    
    healthcare_factory = TinyPersonFactory(
        sampling_space_description="Healthcare professionals including doctors, nurses, administrators, and support staff from various specialties",
        total_population_size=110,
        context="Hospital and healthcare system staffing research"
    )
    
    finance_factory = TinyPersonFactory(
        sampling_space_description="Financial services professionals including analysts, advisors, managers, and support roles from banking and investment",
        total_population_size=110,
        context="Financial services industry workforce study"
    )
    
    education_factory = TinyPersonFactory(
        sampling_space_description="Education professionals including teachers, administrators, researchers, and support staff from K-12 and higher education",
        total_population_size=110,
        context="Education sector demographic analysis"
    )
    
    # Generate approximately 100 people from each factory
    tech_people = tech_factory.generate_people(100, agent_particularities="Technology professionals with diverse skills and experience levels")
    healthcare_people = healthcare_factory.generate_people(100, agent_particularities="Healthcare workers from various medical specialties")
    finance_people = finance_factory.generate_people(100, agent_particularities="Financial professionals with different roles and expertise")
    education_people = education_factory.generate_people(100, agent_particularities="Education professionals from various levels and subjects")
    
    # Verify counts are in expected range (100 ± 10)
    assert 90 <= len(tech_people) <= 110, f"Tech people count {len(tech_people)} outside expected range"
    assert 90 <= len(healthcare_people) <= 110, f"Healthcare people count {len(healthcare_people)} outside expected range"
    assert 90 <= len(finance_people) <= 110, f"Finance people count {len(finance_people)} outside expected range"
    assert 90 <= len(education_people) <= 110, f"Education people count {len(education_people)} outside expected range"
    
    # Verify all people are valid
    all_people = tech_people + healthcare_people + finance_people + education_people
    for person in all_people:
        assert person is not None, "Generated person should not be None"
        assert person.name is not None, "Person should have a name"
        assert len(person.name.strip()) > 0, "Person name should not be empty"
    
    # Verify names are globally unique across all factories
    all_names = [person.name for person in all_people]
    unique_names = set(all_names)
    assert len(unique_names) == len(all_names), f"Found {len(all_names) - len(unique_names)} duplicate names across factories"
    
    # Verify total count
    total_generated = len(all_people)
    assert 360 <= total_generated <= 440, f"Total people generated {total_generated} outside expected range of 360-440"


def test_large_scale_generation_geographic_regions(setup):
    """Test generating large numbers of people across different geographic regions."""
    # Create factories for different geographic regions
    usa_factory = TinyPersonFactory(
        sampling_space_description="Diverse American population from all 50 states, various ages, ethnicities, professions, and socioeconomic backgrounds",
        total_population_size=105,
        context="US national demographic survey"
    )
    
    europe_factory = TinyPersonFactory(
        sampling_space_description="European population from major EU countries including UK, Germany, France, Italy, Spain with diverse cultural and professional backgrounds",
        total_population_size=105,
        context="European market research study"
    )
    
    asia_factory = TinyPersonFactory( 
        sampling_space_description="Asian population from major countries including China, India, Japan, South Korea, Southeast Asia with diverse backgrounds",
        total_population_size=105,
        context="Asian Pacific consumer behavior study"
    )
    
    # Generate people from each region
    usa_people = usa_factory.generate_people(100, agent_particularities="Americans who enjoy travelling by train.")
    europe_people = europe_factory.generate_people(100, agent_particularities="Europeans who enjoy travelling by train.")
    asia_people = asia_factory.generate_people(100, agent_particularities="Asians who enjoy travelling by train.")

    # Verify counts are in expected range
    assert 90 <= len(usa_people) <= 110, f"USA people count {len(usa_people)} outside expected range"
    assert 90 <= len(europe_people) <= 110, f"Europe people count {len(europe_people)} outside expected range"
    assert 90 <= len(asia_people) <= 110, f"Asia people count {len(asia_people)} outside expected range"
    
    # Verify quality of generated people
    all_people = usa_people + europe_people + asia_people
    
    # Check that people have substantial biographical information
    for person in all_people:
        assert person.name is not None
        bio = person.minibio()
        assert len(bio) > 50, f"Person {person.name} has insufficient biography length: {len(bio)}"
    
    # Verify geographic diversity indicators
    usa_bios = [p.minibio().lower() for p in usa_people]
    europe_bios = [p.minibio().lower() for p in europe_people]
    asia_bios = [p.minibio().lower() for p in asia_people]
    
    # Check for region-specific terms (basic validation)
    usa_terms = ['american', 'usa', 'united states', 'us']
    europe_terms = ['european', 'europe', 'british', 'german', 'french', 'italian', 'spanish', 'uk']
    asia_terms = ['asian', 'asia', 'chinese', 'indian', 'japanese', 'korean']
    
    usa_matches = sum(1 for bio in usa_bios if any(term in bio for term in usa_terms))
    europe_matches = sum(1 for bio in europe_bios if any(term in bio for term in europe_terms))
    asia_matches = sum(1 for bio in asia_bios if any(term in bio for term in asia_terms))
    
    # At least some people should have region-specific indicators
    assert usa_matches >= len(usa_people) * 0.3, f"Too few USA people with regional indicators: {usa_matches}/{len(usa_people)}"
    assert europe_matches >= len(europe_people) * 0.3, f"Too few Europe people with regional indicators: {europe_matches}/{len(europe_people)}"
    assert asia_matches >= len(asia_people) * 0.3, f"Too few Asia people with regional indicators: {asia_matches}/{len(asia_people)}"
    
    # Verify global name uniqueness
    all_names = [person.name for person in all_people]
    assert len(set(all_names)) == len(all_names), "Names should be unique across all geographic regions"


def test_large_scale_generation_performance_and_consistency(setup):
    """Test performance and consistency of large-scale generation across multiple runs."""
    # Create a factory with a well-defined sampling space
    factory = TinyPersonFactory(
        sampling_space_description="Professional working adults aged 25-65 from diverse industries, educational backgrounds, and income levels in urban areas",
        total_population_size=120,
        context="Large-scale urban professional demographic study"
    )
    
    # Generate large batch
    people = factory.generate_people(100, agent_particularities="Urban professionals with diverse career backgrounds")
    
    # Verify count is in expected range
    assert 90 <= len(people) <= 110, f"Generated {len(people)} people, expected 90-110"
    
    # Verify all people are valid and have required attributes
    ages = []
    names = []
    bios = []
    
    for person in people:
        assert person is not None
        assert person.name is not None
        assert len(person.name.strip()) > 0
        
        # Check age attribute exists and is reasonable
        age = person.get("age")
        if age is not None:
            assert 18 <= age <= 80, f"Person {person.name} has unreasonable age: {age}"
            ages.append(age)
        
        names.append(person.name)
        bio = person.minibio()
        assert len(bio) > 30, f"Person {person.name} has insufficient biography: {len(bio)}"
        bios.append(bio)
    
    # Verify diversity in names (no duplicates)
    assert len(set(names)) == len(names), "All names should be unique"
    
    # Verify age distribution if ages are available
    if ages:
        assert len(set(ages)) > 20, f"Age diversity too low: {len(set(ages))} unique ages"
        assert min(ages) >= 18, f"Minimum age too low: {min(ages)}"
        assert max(ages) <= 80, f"Maximum age too high: {max(ages)}"
    
    # Verify biographical diversity
    unique_bios = set(bios)
    assert len(unique_bios) == len(bios), "All biographies should be unique"
    
    # Test that we can generate more from the same factory
    additional_people = factory.generate_people(15, agent_particularities="Additional urban professionals")
    assert 10 <= len(additional_people) <= 20, f"Additional batch size {len(additional_people)} outside expected range"
    
    # Verify total doesn't exceed population size
    total_generated = len(people) + len(additional_people)
    assert total_generated <= 120, f"Total generated {total_generated} exceeds population size of 120"
    
    # Verify no name conflicts with previous batch
    all_names = names + [p.name for p in additional_people]
    assert len(set(all_names)) == len(all_names), "Names should remain unique across batches"

