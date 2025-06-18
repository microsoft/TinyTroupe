import pytest
import logging
logger = logging.getLogger("tinytroupe")

import sys
# Insert paths at the beginning of sys.path (position 0)
sys.path.insert(0, '..')
sys.path.insert(0, '../../')
sys.path.insert(0, '../../tinytroupe/')

import tinytroupe
from tinytroupe.agent import TinyPerson
from tinytroupe.environment import TinyWorld, TinySocialNetwork
from tinytroupe.factory import TinyPersonFactory
from tinytroupe.extraction import ResultsExtractor

from tinytroupe.examples import create_lisa_the_data_scientist, create_oscar_the_architect, create_marcos_the_physician

import tinytroupe.control as control
from tinytroupe.control import Simulation

from testing_utils import *


def test_ad_evaluation_scenario(setup):
    # user search query: "europe travel package"

    travel_ad_1 =\
    """
    Tailor-Made Tours Of Europe - Nat'l Geographic Award Winner
    https://www.kensingtontours.com/private-tours/europe
    AdPrivate Guides; Custom Trip Itineraries; 24/7 In-Country Support. Request A Custom Quote. Europe's Best Customized For You - Historic Cities, Scenic Natural Wonders & More.

    Unbeatable Value · Easy Multi-Country · Expert Safari Planners · Top Lodges

    Bulgari & Romania
    Explore Europe Off The Beaten Track
    Exceptional Journey In The Balkans
    Munich, Salzburg, Vienna
    Discover Extraordinary Landscapes
    Explore Castles & Royal Palaces
    Budapest, Vienna, Prague
    Tread Cobblestone Laneways
    Bask In The Elegant Architecture
    30,000+ Delighted Clients
    Customers Love Kensington Tours
    With A Trust Score Of 9.8 Out Of 10
    Expert Planners
    Our Experts Know The Must-Sees,
    Hidden Gems & Everything In Between
    Free Custom Quotes
    Your Itinerary Is Tailored For You
    By Skilled Destination Experts
    See more at kensingtontours.com
    """

    travel_ad_2 =\
    """
    Europe all-inclusive Packages - Europe Vacation Packages
    https://www.exoticca.com/europe/tours

    AdDiscover our inspiring Europe tour packages from the US: Capitals, Beaches and much more. Enjoy our most exclusive experiences in Europe with English guides and Premium hotels

    100% Online Security · +50000 Happy Customers · Flights + Hotels + Tours

    Types: Lodge, Resort & Spa, Guest House, Luxury Hotel, Tented Lodge
    """

    travel_ad_3 =\
    """
    Travel Packages - Great Vacation Deals
    https://www.travelocity.com/travel/packages
    AdHuge Savings When You Book Flight and Hotel Together. Book Now and Save! Save When You Book Your Flight & Hotel Together At Travelocity.

    Get 24-Hour Support · 3 Million Guest Reviews · 240,000+ Hotels Worldwide

    Types: Cheap Hotels, Luxury Hotels, Romantic Hotels, Pet Friendly Hotels
    Cars
    Things to Do
    Discover
    All-Inclusive Resorts
    Book Together & Save
    Find A Hotel
    Nat Geo Expeditions® - Trips to Europe
    https://www.nationalgeographic.com/expeditions/europe
    AdTravel Beyond Your Wildest Dreams. See the World Close-Up with Nat Geo Experts. Join Us for An Unforgettable Expedition! Discover the Nat Geo Difference.

    People & Culture · Wildlife Encounters · Photography Trips · Hiking Trips

    Find The Trip For You
    Request a Free Catalog
    Special Offers
    Discover the Difference
    """

    travel_ad_4 =\
    """
    Europe Luxury Private Tours
    https://www.kensingtontours.com
    Kensington Tours - Private Guides, Custom Itineraries, Hand Picked Hotels & 24/7 Support
    """


    eval_request_msg = \
    f"""
    Can you please evaluate these Bing ads for me? Which one convices you more to buy their particular offering? Select **ONLY** one. Please explain your reasoning, based on your background and personality.

    # AD 1
    ```
    {travel_ad_1}
    ```

    # AD 2
    ```
    {travel_ad_2}
    ```

    # AD 3
    ```
    {travel_ad_3}
    ```

    # AD 4
    ```
    {travel_ad_4}
    ```

    """

    print(eval_request_msg)

    situation = "You decided you want to visit Europe and you are planning your next vacations. You start by searching for good deals as well as good ideas."

    extraction_objective="Find the ad the agent chose. Extract the Ad number (just put a number here, no text, e.g., 2), title and justification for the choice."

    people = [create_oscar_the_architect(), create_lisa_the_data_scientist()]

    for person in people:
        person.change_context(situation)
        person.listen_and_act(eval_request_msg)
        
    extractor = ResultsExtractor()
    choices = []

    for person in people:
        res = extractor.extract_results_from_agent(person,
                                        extraction_objective=extraction_objective,
                                        situation=situation,
                                        fields=["ad_id", "ad_title", "justification"])
        
        print(f"Agent {person.name} choice: {res}")

        assert res is not None, "There should be a result."
        assert "ad_id" in res, "There should be an ad_id field."
        assert str(res["ad_id"]) in ["1", "2", "3", "4"], "The ad_id should be one of the four options."
        assert "ad_title" in res, "There should be an ad_title field."
        assert "justification" in res, "There should be a justification field."

        choices.append(res)

    assert len(choices) == 2, "There should be two choices made."

    print("Agents choices:", choices)

def test_ad_creation_scenario(setup, focus_group_world):

    situation = \
    """ 
    This is a focus group dedicated to finding the best way to advertise an appartment for rent.
    Everyone in the group is a friend to the person who is renting the appartment, called Paulo.
    The objective is to find the best way to advertise the appartment, so that Paulo can find a good tenant.
    """

    apartment_description = \
    """	
    The appartment has the following characteristics:
    - It is in an old building, but was completely renovated and remodeled by an excellent architect. 
        There are almost no walls, so it is very spacious, mostly composed of integrated spaces. 
    - It was also recently repainted, so it looks brand new.
    - 1 bedroom. Originally, it had two, but one was converted into a home office.
    - 1 integrated kitchen and living room. The kitchen is very elegant, with a central eating wood table,
        with 60s-style chairs. The appliances are in gray and steel, and the cabinets are in white, the wood
        is light colored.
    - Has wood-like floors in all rooms, except the kitchen and bathroom, which are tiled.  
    - 2 bathrooms. Both with good taste porcelain and other decorative elements.
    - 1 laundry room. The washing machine is new and also doubles as a dryer.
    - Is already furnished with a bed, a sofa, a table, a desk, a chair, a washing machine, a refrigerator, 
        a stove, and a microwave.
    - It has a spacious shelf for books and other objects.
    - It is close to: a very convenient supermarket, a bakery, a gym, a bus stop, and a subway station. 
        It is also close to a great argentinian restaurant, and a pizzeria.
    - It is located at a main avenue, but the appartment is in the back of the building, so it is very quiet.
    - It is near of the best Medicine School in the country, so it is a good place for a medical student.  
    """

    task = \
    """
    Discuss the best way to advertise the appartment, so that Paulo can find a good tenant.
    """

    focus_group = focus_group_world

    focus_group.broadcast(situation)
    focus_group.broadcast(apartment_description)
    focus_group.broadcast(task)

    focus_group.run(2)

    extractor = ResultsExtractor()
    res = extractor.extract_results_from_world(focus_group, verbose=True)

    assert proposition_holds(f"The following contains ideas for an apartment advertisement: '{res}'"), f"Proposition is false according to the LLM."

def test_consumer_profiling_scenario(setup):

    remove_file_if_exists("test_consumer_profiling_scenario.cache.json")
    control.begin("test_consumer_profiling_scenario.cache.json")

    general_context = \
    """
    We are performing market research, and in that examining the whole of the American population. We care for the opinion of everyone, from the simplest professions to those of the highest ranks. 
    We are interested in the opinion of everyone, from the youngest to the oldest; from the most conservative, to the most liberal; from the educated, to the ignorant;
    from the healthy to the sick; from rich to poor. You get the idea. We are surveying the market for bottled gazpacho, so we are interested in the opinion of everyone, 
    from the most enthusiastic to the most skeptical.
    """

    consumer_factory = TinyPersonFactory(general_context)

    from time import sleep


    consumers = []
    def interview_consumer_batch(n):
        for i in range(n):
            print(f"################################### Interviewing consumer {i+1} of {n} ###################################")
            sleep(2)
            consumer = consumer_factory.generate_person("A random person with highly detailed preferences.")
            print(consumer.minibio())
            #consumer.listen_and_act("Can you please present yourself, and tell us a bit about your background and preferences?")
            consumer.listen_and_act("We are performing some market research and need to know you more. Can you please present yourself and also list your top-10 interests?")
            #consumer.listen_and_act("Can you plese explain more about why you care for these things?")
            consumer.listen_and_act(\
                """
                Would you buy bottled gazpacho if you went to the supermarket today? Why yes, or why not? Please be honest, we are not here to judge you, but just to learn from you.
                We know these choices depend on many factors, but please make your best guess, consider your current situation in life, location, job and interests,
                and tell us whether you would buy bottled gazpacho or not. To make it easier, start your response with "Yes, " or "No, ".
                """)
            
            consumers.append(consumer)

            control.checkpoint()
    
    interview_consumer_batch(15)

    # check if the file was created
    assert os.path.exists("test_consumer_profiling_scenario.cache.json"), "The checkpoint file should have been created."

    control.end()