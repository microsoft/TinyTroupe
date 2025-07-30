# TinyTroupe 🤠🤓🥸🧐
*LLM-powered multiagent persona simulation for imagination enhancement and business insights.*

<p align="center">
  <img src="./docs/tinytroupe_stage.png" alt="A tiny office with tiny people doing some tiny jobs.">
</p>

*TinyTroupe* is an experimental Python library that allows the **simulation** of people with specific personalities, interests, and goals. These artificial agents - `TinyPerson`s - can listen to us and one another, reply back, and go about their lives in simulated `TinyWorld` environments. This is achieved by leveraging the power of Large Language Models (LLMs). Thanks to its integration with **[LiteLLM](https://github.com/BerriAI/litellm)**, TinyTroupe supports over 100 LLM providers, allowing for unparalleled flexibility in generating realistic simulated behavior. This allows us to investigate a wide range of **convincing interactions** and **consumer types**, with **highly customizable personas**, under **conditions of our choosing**. The focus is thus on *understanding* human behavior and not on directly *supporting it* (like, say, AI assistants do) -- this results in, among other things, specialized mechanisms that make sense only in a simulation setting. Further, unlike other *game-like* LLM-based simulation approaches, TinyTroupe aims at enlightening productivity and business scenarios, thereby contributing to more successful projects and products. Here are some application ideas to **enhance human imagination**:

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
- 📦 [Packaging the Project](#packaging-the-project)
- 🤝 [Contributing](#contributing)
- 🙏 [Acknowledgements](#acknowledgements)
- 📜 [Citing TinyTroupe](#how-to-cite-tinytroupe)
- ⚖️ [Legal Disclaimer](#legal-disclaimer)
- ™️ [Trademarks](#trademarks)


## LATEST NEWS
**[2025-07-10] Migration to LiteLLM is complete!**
  - TinyTroupe now uses **LiteLLM** to interact with language models, replacing the previous OpenAI-specific implementation.
  - This change brings support for **over 100 LLM providers**, including OpenAI, Anthropic (Claude), Cohere, Groq, and many more.
  - You can now configure any supported model in your `config.ini` or agent definitions. See the updated [Pre-requisites](#pre-requisites) section for details on setting API keys.

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

### 🧪**Example 1** *(from [interview_with_customer.ipynb](./examples/interview_with_customer.ipynb))*
Let's begin with a simple customer interview scenario, where a business consultant approaches a banker:
<p align="center">
  <img src="./docs/example_screenshot_customer-interview-1.png" alt="An example.">
</p>

The conversation can go on for a few steps to dig deeper and deeper until the consultant is satisfied with the information gathered; for instance, a concrete project idea:
<p align="center">
  <img src="./docs/example_screenshot_customer-interview-2.png" alt="An example.">
</p>



### 🧪**EXAMPLE 2** *(from [advertisement_for_tv.ipynb](./examples/advertisement_for_tv.ipynb))*
Let's evaluate some online ads options to pick the best one. Here's one example output for TV ad evaluation:

<p align="center">
  <img src="./docs/example_screenshot_tv-ad-1.png" alt="An example.">
</p>

Now, instead of having to carefully read what the agents said, we can extract the choice of each agent and compute the overall preference in an automated manner:

<p align="center">
  <img src="./docs/example_screenshot_tv-ad-2.png" alt="An example.">
</p>

### 🧪 **EXAMPLES 3** *(from [product_brainstorming.ipynb](./examples/product_brainstorming.ipynb))*
And here's a focus group starting to brainstorm about new AI features for Microsoft Word. Instead of interacting with each agent individually, we manipulate the environment to make them interact with each other:

<p align="center">
  <img src="./docs/example_screenshot_brainstorming-1.png" alt="An example.">
</p>

After running a simulation, we can extract the results in a machine-readable manner, to reuse elsewhere (e.g., a report generator); here's what we get for the above brainstorming session:

<p align="center">
  <img src="./docs/example_screenshot_brainstorming-2.png" alt="An example.">
</p>

## Pre-requisites

To run the library, you need:
  - Python 3.10 or higher.
  - Access to an LLM provider API. TinyTroupe uses **LiteLLM** to connect to over 100 different LLM providers.

To configure access, you need to set the appropriate environment variable for your chosen provider. Here are a few examples:

-   **OpenAI:**
    ```bash
    export OPENAI_API_KEY="your-api-key"
    ```
-   **Anthropic (Claude):**
    ```bash
    export ANTHROPIC_API_KEY="your-api-key"
    ```
-   **Cohere:**
    ```bash
    export COHERE_API_KEY="your-api-key"
    ```
-   **Groq:**
    ```bash
    export GROQ_API_KEY="your-api-key"
    ```

For a full list of supported providers and their required environment variables, please refer to the [LiteLLM documentation](https://docs.litellm.ai/docs/providers).

By default, TinyTroupe's `config.ini` is set to use a specific API, model, and related parameters. You can customize these values by including your own `config.ini` file in the same folder as the program or notebook you are running. An example of a `config.ini` file is provided in the [examples/](./examples/) folder.

>[!IMPORTANT]
> **Content Filters**: To ensure no harmful content is generated during simulations, it is strongly recommended to use content filters whenever available at the API level. In particular, **if using Azure OpenAI, there's extensive support for content moderation, and we urge you to use it.** For details about how to do so, please consult [the corresponding Azure OpenAI documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/content-filter). If content filters are in place, and an API call is rejected by them, the library will raise an exception, as it will be unable to proceed with the simulation at that point.


## Installation

You can install TinyTroupe in two ways: directly from the source for development, or from a packaged wheel file for use as a library in another project.

### For Development

To install the project in an editable mode, which is useful for development, run the following command from the root of the project directory:

```bash
pip install -e .
```

### As a Library

To use TinyTroupe as a library in another project, first build the package as described in the [Packaging the Project](#packaging-the-project) section. This will create a `.whl` file in the `dist/` directory.

Then, you can install it using `pip`:

```bash
# Replace the filename with the actual name of the generated wheel file
pip install dist/tinytroupe-0.4.0-py3-none-any.whl
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


## Using the Library

Once installed, you can import `tinytroupe` and start creating simulations. Here's a simple example of a chat between two agents:

```python
import tinytroupe
from tinytroupe.agent import TinyPerson
from tinytroupe.environment import TinyWorld

# Note: Make sure agent JSON files are accessible.
# For this example, you might need to copy the `examples/agents` directory
# or provide absolute paths.
lisa = TinyPerson.load_specification("path/to/your/agents/Lisa.agent.json")
oscar = TinyPerson.load_specification("path/to/your/agents/Oscar.agent.json")

# Create a world and add the agents
world = TinyWorld("Chat Room", [lisa, oscar])
world.make_everyone_accessible()

# Start the simulation by giving one agent a goal
lisa.listen("Talk to Oscar to know more about him")
world.run(4) # Run the simulation for 4 steps

# Print the interactions
print("--- Lisa's Interactions ---")
lisa.pp_current_interactions()

print("\n--- Oscar's Interactions ---")
oscar.pp_current_interactions()
```

This example loads two predefined agents, places them in a world, and runs a short simulation where they interact. You can find more detailed examples in the `examples/` directory of this repository.

## Project Structure

The project is structured as follows:
  - `/tinytroupe`: contains the Python library itself. In particular:
    * Each submodule here might contain a `prompts/` folder with the prompts used to call the LLMs.
  - `/tests`: contains the unit tests for the library. You can use the `test.bat` script to run these.
  - `/examples`: contains examples that show how to use the library, mainly using Jupyter notebooks (for greater readability), but also as pure Python scripts.
  - `/data`: any data used by the examples or the library.
  - `/docs`: documentation for the project.
- `pyproject.toml`: The project's configuration file, including dependencies.
- `README.md`: This file.

## Packaging the Project

To package this project for use in other applications, you can build it into a standard Python wheel file (`.whl`). This project uses `setuptools` and can be built with common Python build tools.

### Building with `uv`

If you have `uv` installed, you can build the package with a single command:

```bash
uv build
```

### Building with standard tools

If you prefer to use the standard Python `build` package:

1.  **Install the build tool:**
    ```bash
    pip install build
    ```

2.  **Build the package:**
    ```bash
    python -m build
    ```

After running the build command, you will find the distributable files in the `dist/` directory, including the `.whl` file (e.g., `dist/tinytroupe-0.4.0-py3-none-any.whl`).

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

We are working on an introductory paper that will be the official academic citation for TinyTroupe. In the meantime, please just cite this repository including the core team members as authors. For instance:

>Paulo Salem, Christopher Olsen, Paulo Freire, Yi Ding, Prerit Saxena (2024). **TinyTroupe: LLM-powered multiagent persona simulation for imagination enhancement and business insights.** [Computer software]. GitHub repository. https://github.com/microsoft/tinytroupe


Or as bibtex:
  
  ```bibtex
  @misc{tinytroupe,
    author = {Paulo Salem and Christopher Olsen and Paulo Freire and Yi Ding and Prerit Saxena},
    title = {TinyTroupe: LLM-powered multiagent persona simulation for imagination enhancement and business insights},
    year = {2024},
    howpublished = {\url{https://github.com/microsoft/tinytroupe}},
    note = {GitHub repository}
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


