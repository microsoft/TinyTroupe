import json
import os
import sys

import tinytroupe
# Print current LLM configuration for debugging
from tinytroupe import litellm_utils
from tinytroupe.agent import TinyPerson
from tinytroupe.environment import TinyWorld
from tinytroupe.examples import (create_lisa_the_data_scientist,
                                 create_oscar_the_architect)
from tinytroupe.extraction import ResultsExtractor
from tinytroupe.factory import TinyPersonFactory

# No need to modify sys.path since we're already in the TinyTroupeLiteLLM directory


# TinyTroupeLiteLLM uses LiteLLM which handles multiple providers
# Environment variables for specific providers (like Google Cloud) should be set as needed
# Current configuration in config.ini uses: PROVIDER=vertex_ai, MODEL=vertex_ai/gemini-2.0-flash




print(f"Current LLM Provider: {litellm_utils.default['provider']}")
print(f"Current LLM Model: {litellm_utils.default['model']}")
print("=" * 50)


# User search query: "55 inches tv"

# Ad targeting tech enthusiasts
tv_ad_1 = """
The Ultimate Gaming Experience - LG 4K Ultra HD TV
https://www.lg.com/tv/oled
AdExperience Next-Level Gaming with LG's 4K OLED TV. Unmatched Picture Quality and Ultra-Fast Response Time. Perfect for Gamers and Tech Enthusiasts.

Infinite Contrast · Self-Lighting OLED · Dolby Vision™ IQ · ThinQ AI w/ Magic Remote

Exclusive Gaming Features
LG G2 97" OLED evo TV
Free Gaming Stand w/ Purchase
World's No.1 OLED TV
"""

# Ad targeting families
tv_ad_2 = """
The Perfect Family TV - Samsung 4K & 8K TVs
https://www.samsung.com
AdBring Your Family Together with Samsung's 4K & 8K TVs. Stunning Picture Quality and Family-Friendly Features. Ideal for Movie Nights and Family Gatherings.

Discover Samsung Event · Real Depth Enhancer · Anti-Reflection · 48 mo 0% APR Financing

The 2023 OLED TV Is Here
Samsung Neo QLED 4K TVs
Samsung Financing
Ranked #1 By The ACSI®

Perfect for Family Movie Nights
"""

# Ad targeting budget-conscious shoppers
tv_ad_3 = """
Affordable 55 Inch TV - Wayfair Deals
Shop Now
https://www.wayfair.com/furniture/free-shipping
AdGet the Best Deals on 55 Inch TVs at Wayfair. High-Quality TVs at Budget-Friendly Prices. Free Shipping on All Orders Over $35.

Affordable Prices · Great Deals · Free Shipping
"""

eval_request_msg = f"""
Can you evaluate these Bing ads for me? Which one convices you more to buy their particular offering? 
Select **ONLY** one. Please explain your reasoning, based on your financial situation, background and personality.

# AD 1
```
{tv_ad_1}
```

# AD 2
```
{tv_ad_2}
```

# AD 3
```
{tv_ad_3}
```
"""

print(eval_request_msg)

situation = "Your TV broke and you need a new one. You search for a new TV on Bing."

TinyPerson.all_agents

lisa = create_lisa_the_data_scientist()

lisa.change_context(situation)
lisa.listen_and_act(eval_request_msg)

extractor = ResultsExtractor()

extraction_objective = "Find the ad the agent chose. Extract the Ad number and title."

res = extractor.extract_results_from_agent(
    lisa,
    extraction_objective=extraction_objective,
    situation=situation,
    fields=["ad_number", "ad_title"],
    verbose=True,
)

import pprint

pprint.pprint(res)
