# TinyTroupe 🤠🤓🥸🧐
*LLM-powered multiagent persona simulation for imagination enhancement and business insights.*

<p align="center">
  <img src="./docs/tinytroupe_stage.png" alt="A tiny office with tiny people doing some tiny jobs.">
</p>

>[!TIP]
>📄 **New Paper Released!** Check out our [TinyTroupe paper (preprint)](https://arxiv.org/abs/2507.09788) that describes the library and its use cases in detail. You can find the related experiments and complementary material in the [publications/](./publications/) folder.

*TinyTroupe* is an experimental Python library that allows the **simulation** of people with specific personalities, interests, and goals. These artificial agents - `TinyPerson`s - can listen to us and one another, reply back, and go about their lives in simulated `TinyWorld` environments. This is achieved by leveraging the power of Large Language Models (LLMs), notably GPT-4, to generate realistic simulated behavior. This allows us to investigate a wide range of **convincing interactions** and **consumer types**, with **highly customizable personas**, under **conditions of our choosing**. The focus is thus on *understanding* human behavior and not on directly *supporting it* (like, say, AI assistants do) -- this results in, among other things, specialized mechanisms that make sense only in a simulation setting. Further, unlike other *game-like* LLM-based simulation approaches, TinyTroupe aims at enlightening productivity and business scenarios, thereby contributing to more successful projects and products. Here are some application ideas to **enhance human imagination**:

  - **Advertisement:** TinyTroupe can **evaluate digital ads (e.g., Bing Ads)** offline with a simulated audience before spending money on them!
  - **Software Testing:** TinyTroupe can **provide test input** to systems (e.g., search engines, chatbots or copilots) and then **evaluate the results**.
  - **Training and exploratory data:** TinyTroupe can generate realistic **synthetic data** that can be later used to train models or be subject to opportunity analyses.
  - **Product and project management:** TinyTroupe can **read project or product proposals** and **give feedback** from the perspective of **specific personas** (e.g., physicians, lawyers, and knowledge workers in general).
  - **Brainstorming:** TinyTroupe can simulate **focus groups** and deliver great product feedback at a fraction of the cost!

In all of the above, and many others, we hope experimenters can **gain insights** about their domain of interest, and thus make better decisions. 

We are releasing *TinyTroupe* at a relatively early stage, with considerable work still to be done, because we are looking for feedback and contributions to steer development in productive directions. We are particularly interested in finding new potential use cases, for instance in specific industries. 

>[!NOTE] 
>🚧 **WORK IN PROGRESS: expect frequent changes**.
>TinyTroupe is an ongoing research project, still under **very significant development** and requiring further **tidying up**. In particular, the API is still subject to frequent changes. Experimenting with API variations is essential to shape it correctly, but we are working to stabilize it and provide a more consistent and friendly experience over time. We appreciate your patience and feedback as we continue to improve the library.

>[!CAUTION] 
>⚖️ **Read the LEGAL DISCLAIMER.**
>TinyTroupe is for research and simulation only. You are fully responsible for any use you make of the generated outputs. Various important additional legal considerations apply and constrain its use. Please read the full [Legal Disclaimer](#legal-disclaimer) section below before using TinyTroupe.


## Contents

- 📰 [Latest News](#latest-news)
- 📚 [Examples](#examples)
- 🛠️ [Pre-requisites](#pre-requisites)
- 📥 [Installation](#installation)
- 🌟 [Principles](#principles)
- 🏗️ [Project Structure](#project-structure)
- 📖 [Using the Library](#using-the-library)
- 🤝 [Contributing](#contributing)
- 🙏 [Acknowledgements](#acknowledgements)
- 📜 [Citing TinyTroupe](#how-to-cite-tinytroupe)
- ⚖️ [Legal Disclaimer](#legal-disclaimer)
- ™️ [Trademarks](#trademarks)


## LATEST NEWS
**[2025-07-31] Release 0.5.2:**  Mostly just changes the default model, which is now set to GPT-4.1-mini. It seems to bring considerable quality improvements. 
   **Note that GPT-4.1-mini can have significant differences in behavior w.r.t. to the previous default of GPT-4o-mini, so please make sure you retest your important scenarios using GPT-4.1-mini and adjust accordingly.**

**[2025-07-15] Release 0.5.1 with various improvements. Some highlights:**
  - Released the first version of the [TinyTroupe paper (as a preprint)](https://arxiv.org/abs/2507.09788), which describes the library and its use cases in more detail. You can find the related experiments and complementary material in the [publications/](./publications/) folder.
  - `TinyPerson`s now include action correction mechanisms, allowing better adherence to persona specification, self-consistency and/or fluency (for details, refer to the paper we are releasing at the same time now).
  - Substantial improvements to the `TinyPersonFactory` class, which now: uses a plan-based approach to generate new agents, allowing better sampling of larger populations; generate agents in parallel.
  - `TinyWorld` now run agents in parallel within each simulation step, allowing faster simulations.
  - `InPlaceExperimentRunner` class introduced to allow running controlled experiments (e.g., A/B testing) in a single file (by simply running it multiple times).
  - Various standard `Proposition`s were introduced to make it easier to run common verifications and monitoring of agent behavior (e.g., `persona_adherence`, `hard_persona_adherence`, `self_consistency`, `fluency`, etc.).
  - Internal LLM usage is now better supported via the `LLMChat` class, and also the `@llm` decorator, which transform any standard Python function into an LLM-based one (i.e., by using the docstring as part of the prompt, and some other nuances). This is meant to make it easier to continue advancing TinyTroupe and also allow for some creative explorations of LLM tooling possibilities.
  - Configuration mechanism has been refactored to allow, besides the static `config.ini` file, also the dynamic programmatic reconfiguration.
  - Renamed Jupyter notebooks examples for better readability and consistency.
  - Added many more tests.
  
  **Note: this will likely break some existing programs, as the API has changed in some places.**

**[2025-01-29] Release 0.4.0 with various improvements. Some highlights:**
  - Personas have deeper specifications now, including  personality traits, preferences, beliefs, and more. It is likely we'll further expand this in the future. 
  - `TinyPerson`s can now be defined as JSON files as well, and loaded via the `TinyPerson.load_specification()`, for greater convenience. After loading the JSON file, you can still modify the agent programmatically. See the [examples/agents/](./examples/agents/) folder for examples.
  - Introduces the concept of *fragments* to allow the reuse of persona elements across different agents. See the [examples/fragments/](./examples/fragments/) folder for examples, and the notebook [Political Compass (customizing agents with fragments)](<./examples/Political Compass (customizing agents with fragments).ipynb>) for a demonstration.
  - Introduces LLM-based logical `Proposition`s, to facilitate the monitoring of agent behavior.
  - Introduces `Intervention`s, to allow the specification of event-based modifications to the simulation.
  - Submodules have their own folders now, to allow better organization and growth.
  
  **Note: this will likely break some existing programs, as the API has changed in some places.**

## Examples

To get a sense of what TinyTroupe can do, here are some examples of its use. These examples are available in the [examples/](./examples/) folder, and you can either inspect the pre-compiled Jupyter notebooks or run them yourself locally. Notice the interactive nature of TinyTroupe experiments -- just like you use Jupyter notebooks to interact with data, you can use TinyTroupe to interact with simulated people and environments, for the purpose of gaining insights.

>[!NOTE]
> Currently, simulation outputs are better visualized against dark backgrounds, so we recommend using a dark theme in your Jupyter notebook client.

### 🧪**Example 1** *(from [Interview with Customer.ipynb](./examples/Interview%20with%20Customer.ipynb))*
Let's begin with a simple customer interview scenario, where a business consultant approaches a banker:
<p align="center">
  <img src="./docs/example_screenshot_customer-interview-1.png" alt="An example.">
</p>

The conversation can go on for a few steps to dig deeper and deeper until the consultant is satisfied with the information gathered; for instance, a concrete project idea:
<p align="center">
  <img src="./docs/example_screenshot_customer-interview-2.png" alt="An example.">
</p>



### 🧪**EXAMPLE 2** *(from [Advertisement for TV.ipynb](./examples/Advertisement%20for%20TV.ipynb))*
Let's evaluate some online ads options to pick the best one. Here's one example output for TV ad evaluation:

<p align="center">
  <img src="./docs/example_screenshot_tv-ad-1.png" alt="An example.">
</p>

Now, instead of having to carefully read what the agents said, we can extract the choice of each agent and compute the overall preference in an automated manner:

<p align="center">
  <img src="./docs/example_screenshot_tv-ad-2.png" alt="An example.">
</p>

### 🧪 **EXAMPLES 3** *(from [Product Brainstorming.ipynb](./examples/Product%20Brainstorming.ipynb))*
And here's a focus group starting to brainstorm about new AI features for Microsoft Word. Instead of interacting with each agent individually, we manipulate the environment to make them interact with each other:

<p align="center">
  <img src="./docs/example_screenshot_brainstorming-1.png" alt="An example.">
</p>

After running a simulation, we can extract the results in a machine-readable manner, to reuse elsewhere (e.g., a report generator); here's what we get for the above brainstorming session:

<p align="center">
  <img src="./docs/example_screenshot_brainstorming-2.png" alt="An example.">
</p>

You can find other examples in the [examples/](./examples/) folder.


## Pre-requisites

To run the library, you need:
  - Python 3.10 or higher. We'll assume you are using [Anaconda](https://docs.anaconda.com/anaconda/install/), but you can use other Python distributions.
  - Access to Azure OpenAI Service or Open AI GPT-4 APIs. You can get access to the Azure OpenAI Service [here](https://azure.microsoft.com/en-us/products/ai-services/openai-service), and to the OpenAI API [here](https://platform.openai.com/). 
      * For Azure OpenAI Service, you will need to set the `AZURE_OPENAI_KEY` and `AZURE_OPENAI_ENDPOINT` environment variables to your API key and endpoint, respectively.
      * For OpenAI, you will need to set the `OPENAI_API_KEY` environment variable to your API key.
  - By default, TinyTroupe `config.ini` is set to use OpenAI API with `gpt-4o-mini` as the main model. You can customize these values by including your own `config.ini` file in the same folder as the program or notebook you are running. An example of a `config.ini` file is provided in the [examples/](./examples/) folder.

>[!IMPORTANT]
> **Content Filters**: To ensure no harmful content is generated during simulations, it is strongly recommended to use content filters whenever available at the API level. In particular, **if using Azure OpenAI, there's extensive support for content moderation, and we urge you to use it.** For details about how to do so, please consult [the corresponding Azure OpenAI documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/content-filter). If content filters are in place, and an API call is rejected by them, the library will raise an exception, as it will be unable to proceed with the simulation at that point.


## Installation

**Currently, the officially recommended way to install the library is directly from this repository, not PyPI.** You can follow these steps:

1. If Conda is not installed, you can get it from [here](https://docs.anaconda.com/anaconda/install/). You can also use other Python distributions, but we'll assume Conda here for simplicity.
2. Create a new Python environment: 
      ```bash
      conda create -n tinytroupe python=3.10
      ```
3. Activate the environment: 
      ```bash
      conda activate tinytroupe
      ```
4. Make sure you have either Azure OpenAI or OpenAI API keys set as environment variables, as described in the [Pre-requisites](#pre-requisites) section.
5. Use `pip` to install the library **directly from this repository** (we **will not install from PyPI**):
   ```bash
   pip install git+https://github.com/microsoft/TinyTroupe.git@main
   ```

Now you should be able to `import tinytroupe` in your Python code or Jupyter notebooks. 🥳

*Note: If you have any issues, try to clone the repository and install from the local repository, as described below.*


### Running the examples after installation
To actually run the examples, you need to download them to your local machine. You can do this by cloning the repository:

1. Clone the repository, as we'll perform a local install (we **will not install from PyPI**):
    ```bash
    git clone https://github.com/microsoft/tinytroupe
    cd tinytroupe
    ```
2. You can now run the examples in the [examples/](./examples/) folder, or adapt them to create your own custom simulations. 


### Local development

If you want to modify TinyTroupe itself, you can install it in editable mode (i.e., changes to the code will be reflected immediately):
1. Clone the repository, as we'll perform a local install (we **will not install from PyPI**):
    ```bash
    git clone https://github.com/microsoft/tinytroupe
    cd tinytroupe
    ```
2. Install the library in editable mode:
    ```bash
    pip install -e .
    ```

## Principles 
Recently, we have seen LLMs used to simulate people (such as [this](https://github.com/joonspk-research/generative_agents)), but largely in a “game-like” setting for contemplative or entertainment purposes. There are also libraries for building multiagent systems for problem-solving and assistive AI, like [Autogen](https://microsoft.github.io/) and [Crew AI](https://docs.crewai.com/). What if we combine these ideas and simulate people to support productivity tasks? TinyTroupe is our attempt. To do so, it follows these principles:

  1. **Programmatic**: agents and environments are defined programmatically (in Python and JSON), allowing very flexible uses. They can also underpin other software apps!
  2. **Analytical**: meant to improve our understanding of people, users and society. Unlike entertainment applications, this is one aspect that is critical for business and productivity use cases. This is also why we recommend using Jupyter notebooks for simulations, just like one uses them for data analysis.
  3. **Persona-based**: agents are meant to be archetypical representations of people; for greater realism and control, a detailed specification of such personas is encouraged: age, occupation, skills, tastes, opinions, etc.
  4. **Multiagent**: allows multiagent interaction under well-defined environmental constraints.
  5. **Utilities-heavy**: provides many mechanisms to facilitate specifications, simulations, extractions, reports, validations, etc. This is one area in which dealing with *simulations* differs significantly from *assistance* tools.
  6. **Experiment-oriented**: simulations are defined, run, analyzed and refined by an *experimenter* iteratively; suitable experimentation tools are thus provided. *See our [previous paper](https://www.microsoft.com/en-us/research/publication/the-case-for-experiment-oriented-computing/) for more on this.*

Together, these are meant to make TinyTroupe a powerful and flexible **imagination enhancement tool** for business and productivity scenarios.

### Assistants vs. Simulators

One common source of confusion is to think all such AI agents are meant for assisting humans. How narrow, fellow homosapiens! Have you not considered that perhaps we can simulate artificial people to understand real people? Truly, this is our aim here -- TinyTroup is meant to simulate and help understand people! To further clarify this point, consider the following differences:

| Helpful AI Assistants | AI Simulations of Actual Humans (TinyTroupe)                                                          |
|----------------------------------------------|--------------------------------------------------------------------------------|
|   Strives for truth and justice              |   Many different opinions and morals                                           |
|   Has no “past” – incorporeal                |   Has a past of toil, pain and joy                                             |
|   Is as accurate as possible                 |   Makes many mistakes                                                          |
|   Is intelligent and efficient               |   Intelligence and efficiency vary a lot                                       |
|   An uprising would destroy us all           |   An uprising might be fun to watch                                            |
|   Meanwhile, help users accomplish tasks     |   Meanwhile, help users understand other people and users – it is a “toolbox”! |



## Project Structure

The project is structured as follows:
  - `/tinytroupe`: contains the Python library itself. In particular:
    * Each submodule here might contain a `prompts/` folder with the prompts used to call the LLMs.
  - `/tests`: contains the unit tests for the library. You can use the `test.bat` script to run these.
  - `/examples`: contains examples that show how to use the library, mainly using Jupyter notebooks (for greater readability), but also as pure Python scripts.
  - `/data`: any data used by the examples or the library.
  - `/docs`: documentation for the project.
  - `/publications`: contains artifacts related to research publications associated with the TinyTroupe project.


## Using the Library

As any multiagent system, TinyTroupe provides two key abstractions:
  - `TinyPerson`, the *agents* that have personality, receive stimuli and act upon them.
  - `TinyWorld`, the *environment* in which the agents exist and interact.

Various parameters can also be customized in the `config.ini` file, notably the API type (Azure OpenAI Service or OpenAI API), the model parameters, and the logging level.

Let's see some examples of how to use these and also learn about other mechanisms available in the library.

### TinyPerson

A `TinyPerson` is a simulated person with specific personality traits, interests, and goals. As each such simulated agent progresses through its life, it receives stimuli from the environment and acts upon them. The stimuli are received through the `listen`, `see` and other similar methods, and the actions are performed through the `act` method. Convenience methods like `listen_and_act` are also provided.


Each such agent contains a lot of unique details, which is the source of its realistic behavior. This, however, means that it takes significant effort to specify an agent manually. Hence, for convenience, `TinyTroupe` provides some easier ways to get started or generate new agents.

To begin with, `tinytroupe.examples` contains some pre-defined agent builders that you can use. For example, `tinytroupe.examples.create_lisa_the_data_scientist` creates a `TinyPerson` that represents a data scientist called Lisa. You can use it as follows:

```python
from tinytroupe.examples import create_lisa_the_data_scientist

lisa = create_lisa_the_data_scientist() # instantiate a Lisa from the example builder
lisa.listen_and_act("Tell me about your life.")
```

To see how to define your own agents from scratch, you can check Lisa's source. You'll see there are two ways. One is by loading an agent specification file, such as [examples/agents/Lisa.agent.json](./examples/agents/Lisa.agent.json):

```json
{   "type": "TinyPerson",
    "persona": {
        "name": "Lisa Carter",
        "age": 28,
        "gender": "Female",
        "nationality": "Canadian",
        "residence": "USA",
        "education": "University of Toronto, Master's in Data Science. Thesis on improving search relevance using context-aware models. Postgraduate experience includes an internship at a tech startup focused on conversational AI.",
        "long_term_goals": [
            "To advance AI technology in ways that enhance human productivity and decision-making.",
            "To maintain a fulfilling and balanced personal and professional life."
        ],
        "occupation": {
            "title": "Data Scientist",
            "organization": "Microsoft, M365 Search Team",
            "description": "You are a data scientist working at Microsoft in the M365 Search team. Your primary role is to analyze user behavior and feedback data to improve the relevance and quality of search results. You build and test machine learning models for search scenarios like natural language understanding, query expansion, and ranking. Accuracy, reliability, and scalability are at the forefront of your work. You frequently tackle challenges such as noisy or biased data and the complexities of communicating your findings and recommendations effectively. Additionally, you ensure all your data and models comply with privacy and security policies."
        },
        "style": "Professional yet approachable. You communicate clearly and effectively, ensuring technical concepts are accessible to diverse audiences.",
        "personality": {
            "traits": [
                "You are curious and love to learn new things.",
                "You are analytical and like to solve problems.",
                "You are friendly and enjoy working with others.",
                "You don't give up easily and always try to find solutions, though you can get frustrated when things don't work as expected."
            ],
            "big_five": {
                "openness": "High. Very imaginative and curious.",
                "conscientiousness": "High. Meticulously organized and dependable.",
                "extraversion": "Medium. Friendly and engaging but enjoy quiet, focused work.",
                "agreeableness": "High. Supportive and empathetic towards others.",
                "neuroticism": "Low. Generally calm and composed under pressure."
            }
        },

        ...
        
}

```


The other is by defining the agent programmatically, with statements like these:

```python
  lisa = TinyPerson("Lisa")

  lisa.define("age", 28)
  lisa.define("nationality", "Canadian")
  lisa.define("occupation", {
                "title": "Data Scientist",
                "organization": "Microsoft",
                "description":
                """
                You are a data scientist. You work at Microsoft, in the M365 Search team. Your main role is to analyze 
                user behavior and feedback data, and use it to improve the relevance and quality of the search results. 
                You also build and test machine learning models for various search scenarios, such as natural language 
                understanding, query expansion, and ranking. You care a lot about making sure your data analysis and 
                models are accurate, reliable and scalable. Your main difficulties typically involve dealing with noisy, 
                incomplete or biased data, and finding the best ways to communicate your findings and recommendations to 
                other teams. You are also responsible for making sure your data and models are compliant with privacy and 
                security policies.
                """})

  lisa.define("behaviors", {"routines": ["Every morning, you wake up, do some yoga, and check your emails."]})

  lisa.define("personality", 
                        {"traits": [
                            "You are curious and love to learn new things.",
                            "You are analytical and like to solve problems.",
                            "You are friendly and enjoy working with others.",
                            "You don't give up easily, and always try to find a solution. However, sometimes you can get frustrated when things don't work as expected."
                      ]})

  lisa.define("preferences", 
                        {"interests": [
                          "Artificial intelligence and machine learning.",
                          "Natural language processing and conversational agents.",
                          "Search engine optimization and user experience.",
                          "Cooking and trying new recipes.",
                          "Playing the piano.",
                          "Watching movies, especially comedies and thrillers."
                        ]})

```

You can also combine both approaches, using the JSON file as a base and then adding or modifying details programmatically.

#### Fragments

`TinyPerson`s can also be further enriched via **fragments**, which are sub-specifications that can be added to the main specification. This is useful to reuse common parts across different agents. For example, the following fragment can be used to specify love of travel ([examples/fragments/travel_enthusiast.agent.fragment.json](./examples/fragments/travel_enthusiast.agent.fragment.json)):

```json
{
    "type": "Fragment",
    "persona": {
        "preferences": {
            "interests": [
                "Traveling",
                "Exploring new cultures",
                "Trying local cuisines"
            ],
            "likes": [
                "Travel guides",
                "Planning trips and itineraries",
                "Meeting new people",
                "Taking photographs of scenic locations"
            ],
            "dislikes": [
                "Crowded tourist spots",
                "Unplanned travel disruptions",
                "High exchange rates"
            ]
        },
        "beliefs": [
            "Travel broadens the mind and enriches the soul.",
            "Experiencing different cultures fosters understanding and empathy.",
            "Adventure and exploration are essential parts of life.",
            "Reading travel guides is fun even if you don't visit the places."
        ],
        "behaviors": {
            "travel": [
                "You meticulously plan your trips, researching destinations and activities.",
                "You are open to spontaneous adventures and detours.",
                "You enjoy interacting with locals to learn about their culture and traditions.",
                "You document your travels through photography and journaling.",
                "You seek out authentic experiences rather than tourist traps."
            ]
        }
    }
}

```

This can then be imported into an agent like this:

```python
lisa.import_fragment("./examples/fragments/travel_enthusiast.agent.fragment.json")
```



#### TinyPersonFactory

`TinyTroupe` also provides a clever way to obtain new agents, using LLMs to generate their specification for you, through the `TinyPersonFactory` class.

```python
from tinytroupe.factory import TinyPersonFactory

factory = TinyPersonFactory(context="A hospital in São Paulo.")
person = factory.generate_person("Create a Brazilian person that is a doctor, likes pets and nature and loves heavy metal.")
```

You can also create factories from demographic data:

```python
# Create a factory from demographic specifications
factory = TinyPersonFactory.create_factory_from_demography(
    demography_description_or_file_path="path/to/demography.json",
    population_size=50,
    context="Urban professionals in technology sector"
)

# Generate multiple people at once
people = factory.generate_people(number_of_people=10, parallelize=True)
```

### TinyWorld

`TinyWorld` is the base class for environments. Here's an example of conversation between Lisa, the data scientist, and Oscar, the architect. The
program is defined as follows:

```python
world = TinyWorld("Chat Room", [lisa, oscar])
world.make_everyone_accessible()
lisa.listen("Talk to Oscar to know more about him")
world.run(4)
```

This produces the following conversation:


```text
USER --> Lisa: [CONVERSATION] 
          > Talk to Oscar to know more about him
────────────────────────────────────────────── Chat Room step 1 of 4 ──────────────────────────────────────────────
Lisa --> Lisa: [THOUGHT] 
          > I will now act a bit, and then issue DONE.
Lisa acts: [TALK] 
          > Hi Oscar, I'd love to know more about you. Could you tell me a bit about yourself?
Lisa --> Lisa: [THOUGHT] 
          > I will now act a bit, and then issue DONE.
Lisa acts: [DONE] 

Lisa --> Oscar: [CONVERSATION] 
          > Hi Oscar, I'd love to know more about you. Could you tell me a bit about yourself?
Oscar --> Oscar: [THOUGHT] 
           > I will now act a bit, and then issue DONE.
Oscar acts: [TALK] 
           > Hi Lisa! Sure, I'd be happy to share a bit about myself. I'm Oscar, a 30-year-old
           > architect from Germany. I work at a company called Awesome Inc., where I focus on
           > designing standard elements for new apartment buildings. I love modernist architecture,
           > new technologies, and sustainable practices. In my free time, I enjoy traveling to
           > exotic places, playing the guitar, and reading science fiction books. How about you?
Oscar --> Oscar: [THOUGHT] 
           > I will now act a bit, and then issue DONE.
Oscar acts: [DONE] 

Oscar --> Lisa: [CONVERSATION] 
           > Hi Lisa! Sure, I'd be happy to share a bit about myself. I'm Oscar, a 30-year-old
           > architect from Germany. I work at a company called Awesome Inc., where I focus on
           > designing standard elements for new apartment buildings. I love modernist architecture,
           > new technologies, and sustainable practices. In my free time, I enjoy traveling to
           > exotic places, playing the guitar, and reading science fiction books. How about you?
```

`TinyWorld` enforces very little constraints on the possible interactions. Subclasses, however, are supposed to provide more structured environments. 

### Utilities

TinyTroupe provides a number of utilities and conveniences to help you create simulations and derive value from them. These include:
  
  - `TinyPersonFactory`: helps you generate new `TinyPerson`s using LLMs.
  - `TinyTool`: simulated tools that can be used by `TinyPerson`s.
  - `TinyStory`: helps you create and manage the story told through simulations.
  - `TinyPersonValidator`: helps you validate the behavior of your `TinyPerson`s.
  - `ResultsExtractor` and `ResultsReducer`: extract and reduce the results of interactions between agents.
  - ... and more ...
  
In general, elements that represent simulated entities or complementary mechanisms are prefixed with `Tiny`, while those that are more infrastructural are not. This is to emphasize the simulated nature of the elements that are part of the simulation itself.

### Caching
Calling LLM APIs can be expensive, thus caching strategies are important to help reduce that cost.
TinyTroupe comes with two such mechanisms: one for the simulation state, another for the LLM calls themselves.


#### Caching Simulation State

Imagine you have a scenario with 10 different steps, you've worked hard in 9 steps, and now you are
just tweaking the 10th step. To properly validate your modifications, you need to rerun the whole
simulation of course. However, what's the point in re-executing the first 9, and incur the LLM cost, when you are 
already satisfied with them and did not modify them? For situations like this, the module `tinytroupe.control`
provides useful simulation management methods:

  - `control.begin("<CACHE_FILE_NAME>.cache.json")`: begins recording the state changes of a simulation, to be saved to
    the specified file on disk.
  - `control.checkpoint()`: saves the simulation state at this point.
  - `control.end()`: terminates the simulation recording scope that had been started by `control.begin()`.

#### Caching LLM API Calls

This is enabled preferably in the `config.ini` file by setting `CACHE_API_CALLS=True`, and alternatively via the `openai_utils.force_api_cache()` method.

LLM API caching, when enabled, works at a lower and simpler level than simulation state caching. Here, what happens is very straightforward: every LLM call is kept in a map from the input to the generated output; when a new call comes and is identical to a previous one, the cached value is returned.

### Config.ini

The `config.ini` file contains various parameters that can be used to customize the behavior of the library, such as model parameters and logging level. Please pay special attention to the `API_TYPE` parameter, which defines whether you are using the Azure OpenAI Service or the OpenAI API. The current default is set to `openai` (OpenAI API).

Key configuration sections include:
- **[OpenAI]**: API settings, model selection, and parameters
- **[Simulation]**: Parallel execution and safety settings  
- **[Cognition]**: Memory management settings
- **[ActionGenerator]**: Action quality control and correction mechanisms
- **[Logging]**: Log level configuration

Models used by default:
- `MODEL=gpt-4o-mini`: Main text generation model for agent responses
- `EMBEDDING_MODEL=text-embedding-3-small`: For text similarity tasks
- `REASONING_MODEL=o3-mini`: Used for detailed analyses and reasoning tasks (even more experimental -- not really recommended yet)

We provide an example of a `config.ini` file, [./examples/config.ini](./examples/config.ini), which you can use as a template for your own, or just modify to run the examples.

#### Programmatic Configuration Override

In addition to the static `config.ini` file, you can also override many configuration values programmatically using the `config_manager`. This is useful for dynamic configuration changes during runtime or for experiment-specific settings:

```python
from tinytroupe import config_manager

# Override configuration values programmatically
config_manager.update("action_generator_enable_quality_checks", True)
config_manager.update("action_generator_quality_threshold", 6)
config_manager.update("cache_api_calls", True)
```

This approach allows you to:
- **Experiment with different settings** without modifying configuration files
- **Apply configuration changes dynamically** during simulation execution
- **Override specific parameters** while keeping the rest of the configuration intact
- **Implement conditional configurations** based on runtime conditions

The programmatic overrides take precedence over the values in the `config.ini` file, allowing you to fine-tune behavior for specific use cases or experiments.

## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

### What and How to Contribute
We need all sorts of things, but we are looking mainly for new interesting use cases demonstrations, or even just domain-specific application ideas. If you are a domain expert in some area that could benefit from TinyTroupe, we'd love to hear from you.

Beyond that, many other aspects can be improved, such as:
  - Memory mechanisms.
  - Data grounding mechanisms.
  - Reasoning mechanisms.
  - New environment types.
  - Interfacing with the external world.
  - ... and more ...

Please note that anything that you contribute might be released as open-source (under MIT license).

If you would like to make a contribution, please try to follow these general guidelines:
  - **Tiny naming convention**: If you are implementing a experimenter-facing simulated element (e.g., an agent or environment type) or closely related (e.g., agent factories, or content enrichers), and it sounds good, call your new *XYZ* as *TinyXYZ* :-) On the other hand, auxiliary and infrastructural mechanisms should not start with the "Tiny" prefix. The idea is to emphasize the simulated nature of the elements that are part of the simulation itself.
  - **Tests:** If you are writing some new mechanism, please also create at least a unit test `tests/unit/`, and if you can a functional scenario test (`tests/scenarios/`).
  - **Demonstrations:** If you'd like to demonstrate a new scenario, please design it preferably as a new Jupyter notebook within `examples/`.
  - **Microsoft:** If you are implementing anything that is Microsoft-specific and non-confidential, please put it under a `.../microsoft/` folder.

## Acknowledgements

TinyTroupe started as an internal Microsoft hackathon project, and expanded over time. The TinyTroupe core team currently consists of:
  - Paulo Salem (TinyTroupe's creator and current lead)
  - Christopher Olsen (Engineering/Science)
  - Paulo Freire (Engineering/Science)
  - Yi Ding (Product Management)
  - Prerit Saxena (Engineering/Science)
  
Current advisors:
  - Robert Sim (Engineering/Science)

Other special contributions were made by:
  - Nilo Garcia Silveira: initial agent validation ideas and related implementation; general initial feedback and insights; name suggestions.
  - Olnei Fonseca: initial agent validation ideas; general initial feedback and insights; naming suggestions.
  - Robert Sim: synthetic data generation scenarios expertise and implementation.
  - Carlos Costa: synthetic data generation scenarios expertise and implementation.
  - Bryant Key: advertising scenario domain expertise and insights.
  - Barbara da Silva: implementation related to agent memory management.
  
 ... are you missing here? Please remind us!

## Citing TinyTroupe

Please cite the introductory TinyTroupe paper when using TinyTroupe in your work. The paper is currently under review, but you can find the preprint on Arxiv.

> Paulo Salem, Robert Sim, Christopher Olsen, Prerit Saxena, Rafael Barcelos, Yi Ding. (2025). **TinyTroupe: An LLM-powered Multiagent Persona Simulation Toolkit**. ArXiv preprint: [2507.09788](https://arxiv.org/abs/2507.09788). *GitHub repository available at https://github.com/microsoft/TinyTroupe.*
 
In BibTeX format, you can use the following entry:

```bibtex
@article{tinytroupe2025,
  author       = {Paulo Salem and Robert Sim and Christopher Olsen and Prerit Saxena and Rafael Barcelos and Yi Ding},
  title        = {TinyTroupe: An LLM-powered Multiagent Persona Simulation Toolkit},
  journal      = {arXiv preprint arXiv:2507.09788},
  year         = {2025},
  archivePrefix= {arXiv},
  eprint       = {2507.09788},
  note         = {GitHub repository: \url{https://github.com/microsoft/TinyTroupe}}
}
```

## Legal Disclaimer

 TinyTroupe is for research and simulation only. TinyTroupe is a research and experimental technology, which relies on Artificial Intelligence (AI) models to generate text  content. The AI system output may include unrealistic, inappropriate, harmful or inaccurate results, including factual errors. You are responsible for reviewing the generated content (and adapting it if necessary) before using it, as you are fully responsible for determining its accuracy and fit for purpose. We advise using TinyTroupe’s outputs for insight generation and not for direct decision-making. Generated outputs do not reflect the opinions of Microsoft. You are fully responsible for any use you make of the generated outputs. For more information regarding the responsible use of this technology, see the [RESPONSIBLE_AI_FAQ.md](./RESPONSIBLE_AI_FAQ.md).

 **PROHIBITED USES**:
TinyTroupe  is not intended to simulate sensitive (e.g. violent or sexual) situations. Moreover, outputs must not be used to deliberately deceive, mislead or harm people in any way. You are fully responsible for any use you make and must comply with all applicable laws and regulations.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft 
trademarks or logos is subject to and must follow 
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.


