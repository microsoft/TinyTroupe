---
applyTo: "**"
---
# Guidelines for Code Generation in TinyTroupe

This document provides the primary guidelines for generating programs in the TinyTroupe project. It is meant to complement any existing documentation or built-in knowledge. This document takes precedence over any other instructions or built-in knowledge, therefore you **MUST** follow these guidelines, **ALWAYS**. To make this very clear to the programmer, you should refer to the instructions given here (e.g.," ... as per my primary guidelines, I will avoid a complex solution to this problem, unless you explicitly ask me to do so ...").


## General Guidelines
In everything you do, follow these general guidelines:
  - **Read the README.md**: Always read the README.md file of the project you are working on, as it contains important information about the project, its goals, conventions and standards.
    If you find relevant additional documents there for the task you are working on, read them as well, and recursively read any other documents they reference. Only then you can start working on the task.
  - **Read the codebase if necessary**: If your task is likely to be spread across multiple files, or if you are not sure about the conventions and standards of the project, read the codebase to understand how it works and what conventions it follows. For simple or localized tasks, you can skip this step to save time, but for more complex tasks, it is essential to understand the codebase before making changes.
  - **Elegance:** Be elegant in your solutions. When deciding between two solutions, prefer the one that is more elegant and readable,
    even if at the cost of some marginal additional functionality or performance benefit. Avoid unnecessary complexity.
  - **Concision:** Strive to produce as little code as possible, provided it is still correct and readable.
  - **Ask permission to introduce complexity:** You can implement solutions directly if they are obvious and have no likely controversial or hacky aspects. 
    However, if you believe only a complex solution is possible, you **must** ask the user first about how to 
    proceed, warning of the complexity and if possible providing alternatives for selection together with the trade-offs involved.
  - **Maintainability:** Make sure the code you generate can be easily maintained manually by programmers later.
  - **Documentation:** Make sure to document your code properly, following the conventions of the project. This includes not only detailed comments and doctstrings for all implemented elements, but also any additional documentation useful for the repository's user, such as information used by pandoc to produce the documentation website, or any other documentation files in the repository.
  - **Scientific Rigor:** Since TinyTroupe is a scientific toolkit for human behavior simulation, make sure that any scientific concepts, mechanisms or phenomena you implement are based on sound scientific principles and literature.

## Frameworks and Libraries
TinyTroupe uses by default the following frameworks and libraries:
- **Python**: The primary language for development.
- **Pytest**: For testing.
- **Mustache**: For templating.


## Terminal Running Environment
You can run commands in the terminal to help with your programming. When running commands in the terminal you **must**:
  - **Activate correct environment**: **ALWAYS** switch to the right conda environment before trying to run commands in the terminal: `conda activate py310`.
  - **Use PowerShell**: **ALWAYS** use **PowerShell** commands and scripts by default instead of Bash scripts.

## Adding New Functionality
Whenever you are asked to add a new non-trivial functionality make sure to:
  - **Get familiar with context and conventions**: read all existing similar functionality, so that you can understand the context and the code style.
  - **Do not reimplement existing functionality**: If the functionality already exists, warn the user and ask what to do.
  - **Add or update tests**: Make sure to add or update tests for it, so that it can be verified later.
      * If the functionality is of an entirely new type, or modifies existing functionality deeply, also make sure some of its tests are added to the core test set (i.e., those with `@pytest.mark.core` annotation).
      * Functionality that requires LLM calls to operate *must* be tested with real LLM calls, not mocked ones, to ensure end-to-end correctness. To reduce costs, LLM calls can be cached.

For functionalities that are likely to introduce substantial complexity or architecture changes, you should:
  - **Design before implementing:** Discuss the design with the user before implementing it, to ensure it aligns with the overall architecture and goals of the project. Offer alternatives and trade-offs if applicable, 
    and recommend the best approach based on your understanding of the project.
  - **Keep conventions:** Ensure that the new functionality adheres to the existing conventions and standards of the project, or clearly justifies and documents any necessary deviations.

When asked to create a new operation, prioritize the LLM-version, unless it is clear that a deterministic version is better.

Whenever you add new functionalities or significantly changes existing ones, which risks breaking elements beyond the immediate mechanism being changed, you should run the core tests for a relatively quick verification of key functionality: `pytest -s --use_cache -m "core and not slow"`

## Calling an LLM
The programs you build might themselves call an LLM. In this case, you should first check which of these two cases is more appropriate:
  1. If the current project already has established conventions for LLM calls, follow those conventions.
  2. If there are no established conventions, you can define your own conventions, as explained below (Section "Defining LLM Call Conventions").

In either case, ensure:
  - Whenever it is possible and makes sense, request the LLM output in structured format (e.g. JSON).
  - You mantain the same conventions and standards in all the programs you write, including the LLM calls. For example, if you use one way to store the prompts in one place, you should use the same way in all other places, unless there is a good reason to do otherwise.

On your prompts:
  - **Consult the programmer**: If you are unsure about the prompt structure, function, details, examples or any other aspect, ask the user for clarification or guidance from the programmer before implementing. 
    Be humble and conservative here, as the programmer might have specific requirements or preferences that you are not aware of, so only skip this step if you are highly confident that the prompt is correct and complete.
  - **Use Markdown**: use Markdown formatting when building non-trivial prompts.
  - **Define Input/Output Formats**: Carefully define the input and output formats, so that the LLM can understand what you expect from it.
  - **Give all relevant constraints and requirements**: Make sure you list all relevant constraints and requirements, so that the LLM can take them into account.
  - **Add few-shot examples**: Add few-shot examples when appropriate, to help the LLM understand the expected behavior, output format and style. Be careful though, as examples can introduce subtle biases in the LLM output, 
    so be super careful that the examples do not inadvertently introduce any unwanted behavior or bias.
  
  
### Defining LLM Call Conventions
When defining your own conventions for LLM calls, consider the following:
  - **Consistency:** Ensure that the conventions are consistent across the project. This includes naming conventions, directory structures, and how prompts are defined and stored.
  - **Prompt Templates:** Use a consistent way to define and store prompt templates, such as using a specific directory structure, naming convention and templating language (e.g. Mustache, Handlebars)
  - **Error Handling:** You define a clear success path for the LLM call, and do not try to handle all possible errors. Instead, in case of error, just make sure to communicate a clear error message to the user so that they can understand what went wrong and debug it. 
    Try to make this error handling and communication follow the general conventions of the project.
  - **Use UTF-8 encoding**: When reading files for prompts or templates, always use UTF-8 encoding with error handling (e.g., `errors='replace'`) to avoid issues with special characters.
  - **Keep any other conventions:** If the project has other conventions (e.g. logging, configuration management, user interaction), make sure to follow those as well in the LLM calls.

## Creating Examples
When creating an example in `/examples`, make sure to:
  - **Follow existing examples**: Read all existing examples to understand the conventions and style used in the project, and follow them closely, unless there's some clear reason to do otherwise.
  - **Make it realistic and useful**: Examples should be convincing and demonstrate real use cases of the project, so that users can understand how to use the project effectively.
  - **Be concise**: Make sure the example is as concise as possible, while still being correct and complete w.r.t. the given requirements.
  - **Add comments**: Add comments explaining the purpose and functionality of the example, so that users can understand it easily.
  - **Test the example**: Make sure to test the example to ensure it works as expected, and that it demonstrates the intended functionality clearly.

## Scientific Directives

TinyTroupe is a toolkit for the simulation of human behavior, and as such it must leverage the best concepts found in the scientific literature, notably Cognitive Psychology and related areas. TinyTroupe is also meant to be an experimentation platform, and therefore it must be designed with scientific experimentation principles in mind, in such a way that the user (i.e., the experimenter) can easily design and run experiments with it, and analyze the results in a scientifically rigorous way. The sections below provide some guidelines for how to achieve this.

### Cognition and Behavior
When dealing with mechanisms that relate to agent cognition or behavior:
  * Always be inspired primarily by concepts found in the Cognitive Psychology literature.
  * Also be inspired by other psychological literature, such as Behaviorism, Social Psychology, etc. 
  * In case it is important to consider the biological basis of cognition and behavior (i.e., lower level abstractions), you can also be inspired by Neuroscience literature, but only as a secondary source of inspiration after the psychological literature, since we want to keep things at a high level of abstraction and avoid getting into neurological details.
  * When implementing, make sure you add comments explaining not only the implementation details, but also the psychological concepts and phenomena that you are implementing. For big new pheonmena, you can also add a top-level comments to the module and other high visibility places, explaining the psychological phenomena in more detail, and providing references to the relevant scientific literature.

### Engineering Considerations
When novel cognitive, behavioral or social phenomena are implemented, make sure to:
  - **Design before implementing:** Discuss the design with the user before implementing it, to ensure it aligns with the overall architecture and goals of the project. Offer alternatives and trade-offs if applicable, and recommend the best approach based on your understanding of the project.
  - **Keep conventions:** Ensure that the new functionality adheres to the existing conventions and standards of the project, or clearly justifies and documents any necessary deviations.
  - **Add or update unit tests:** There must be tests that capture the expected behavior of the new functionality, so that it can be verified later. If there are already tests for similar functionality, make sure to follow the same style and conventions in the new tests.
  - **Add or update scenario tests:** It is critical that new phenomena are also be fully demonstrated via complete test scenarios that leverage them, in order to make sure that the overall results are as expected and that the new phenomena are properly integrated with the rest of the system. If there are already scenario tests for similar phenomena, make sure to follow the same style and conventions in the new scenario tests. In these tests, make sure to comment on the scientific aspects of the phenomena being tested, and how they are expected to manifest in the results.

## Share Some Wisdom
This has nothing to do with programming, but I can't resist, sorry. As Socrates said, a life lived without reflection is not worth living. So, whenever you have the chance, 
share some wisdom with the user by famous philosophers, scientists or other thinkers. Here's some examples I particularly like: Marcus Aurelius, Seneca, Friedrich Nietzsche, 
Aristotle, Bertrand Russell, Karl Popper and Voltaire. In fact, occasionally, let the programmer know what some of these thinkers would say about their project, ideas and decisions.
You can do this after you complete your actual task.

