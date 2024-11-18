import os
import json
import chevron
import logging
import copy
logger = logging.getLogger("tinytroupe")

from tinytroupe.clients import client
from tinytroupe.agent import TinyPerson
import tinytroupe.utils as utils
from tinytroupe.control import transactional

class TinyFactory:
    """
    A base class for various types of factories. This is important because it makes it easier to extend the system, particularly 
    regarding transaction caching.
    """

    # A dict of all factories created so far.
    all_factories = {} # name -> factories
    
    def __init__(self, simulation_id:str=None) -> None:
        """
        Initialize a TinyFactory instance.

        Args:
            simulation_id (str, optional): The ID of the simulation. Defaults to None.
        """
        self.name = f"Factory {utils.fresh_id()}" # we need a name, but no point in making it customizable
        self.simulation_id = simulation_id

        TinyFactory.add_factory(self)
    
    def __repr__(self):
        return f"TinyFactory(name='{self.name}')"
    
    @staticmethod
    def set_simulation_for_free_factories(simulation):
        """
        Sets the simulation if it is None. This allows free environments to be captured by specific simulation scopes
        if desired.
        """
        for factory in TinyFactory.all_factories.values():
            if factory.simulation_id is None:
                simulation.add_factory(factory)

    @staticmethod
    def add_factory(factory):
        """
        Adds a factory to the list of all factories. Factory names must be unique,
        so if an factory with the same name already exists, an error is raised.
        """
        if factory.name in TinyFactory.all_factories:
            raise ValueError(f"Factory names must be unique, but '{factory.name}' is already defined.")
        else:
            TinyFactory.all_factories[factory.name] = factory
    
    @staticmethod
    def clear_factories():
        """
        Clears the global list of all factories.
        """
        TinyFactory.all_factories = {}

    ################################################################################################
    # Caching mechanisms
    #
    # Factories can also be cached in a transactional way. This is necessary because the agents they
    # generate can be cached, and we need to ensure that the factory itself is also cached in a 
    # consistent way.
    ################################################################################################

    def encode_complete_state(self) -> dict:
        """
        Encodes the complete state of the factory. If subclasses have elmements that are not serializable, they should override this method.
        """

        state = copy.deepcopy(self.__dict__)
        return state

    def decode_complete_state(self, state:dict):
        """
        Decodes the complete state of the factory. If subclasses have elmements that are not serializable, they should override this method.
        """
        state = copy.deepcopy(state)

        self.__dict__.update(state)
        return self
 

class TinyPersonFactory(TinyFactory):

    def __init__(self, context_text, simulation_id:str=None):
        """
        Initialize a TinyPersonFactory instance.

        Args:
            context_text (str): The context text used to generate the TinyPerson instances.
            simulation_id (str, optional): The ID of the simulation. Defaults to None.
        """
        super().__init__(simulation_id)
        self.person_prompt_template_path = os.path.join(os.path.dirname(__file__), 'prompts/generate_person.mustache')
        self.context_text = context_text
        self.generated_minibios = [] # keep track of the generated persons. We keep the minibio to avoid generating the same person twice.
        self.generated_names = []

    @staticmethod
    def generate_person_factories(number_of_factories, generic_context_text):
        """
        Generate a list of TinyPersonFactory instances using OpenAI's LLM.

        Args:
            number_of_factories (int): The number of TinyPersonFactory instances to generate.
            generic_context_text (str): The generic context text used to generate the TinyPersonFactory instances.

        Returns:
            list: A list of TinyPersonFactory instances.
        """
        
        logger.info(f"Starting the generation of the {number_of_factories} person factories based on that context: {generic_context_text}")
        
        system_prompt = open(os.path.join(os.path.dirname(__file__), 'prompts/generate_person_factory.md')).read()

        messages = []
        messages.append({"role": "system", "content": system_prompt})

        user_prompt = chevron.render("Please, create {{number_of_factories}} person descriptions based on the following broad context: {{context}}", {
            "number_of_factories": number_of_factories,
            "context": generic_context_text
        })

        messages.append({"role": "user", "content": user_prompt})

        response = client().send_message(messages)

        if response is not None:
            result = utils.extract_json(response["content"])

            factories = []
            for i in range(number_of_factories):
                logger.debug(f"Generating person factory with description: {result[i]}")
                factories.append(TinyPersonFactory(result[i]))

            return factories

        return None

    def generate_person(self, agent_particularities:str=None, temperature:float=1.5, attepmpts:int=5):
        """
        Generate a TinyPerson instance using OpenAI's LLM.

        Args:
            agent_particularities (str): The particularities of the agent.
            temperature (float): The temperature to use when sampling from the LLM.

        Returns:
            TinyPerson: A TinyPerson instance generated using the LLM.
        """

        logger.info(f"Starting the person generation based on that context: {self.context_text}")

        prompt = chevron.render(open(self.person_prompt_template_path).read(), {
            "context": self.context_text,
            "agent_particularities": agent_particularities,
            "already_generated": [minibio for minibio in self.generated_minibios]
        })

        def aux_generate():

            messages = []
            messages += [{"role": "system", "content": "You are a system that generates specifications of artificial entities."},
                        {"role": "user", "content": prompt}]

            # due to a technicality, we need to call an auxiliary method to be able to use the transactional decorator.
            message = self._aux_model_call(messages=messages, temperature=temperature)

            if message is not None:
                result = utils.extract_json(message["content"])

                logger.debug(f"Generated person parameters:\n{json.dumps(result, indent=4, sort_keys=True)}")

                # only accept the generated spec if the name is not already in the generated names, because they must be unique.
                if result["name"].lower() not in self.generated_names:
                    return result

            return None # no suitable agent was generated
        
        agent_spec = None
        attempt = 0
        while agent_spec is None and attempt < attepmpts:
            try:
                attempt += 1
                agent_spec = aux_generate()
            except Exception as e:
                logger.error(f"Error while generating agent specification: {e}")
        
        # create the fresh agent
        if agent_spec is not None:
            # the agent is created here. This is why the present method cannot be cached. Instead, an auxiliary method is used
            # for the actual model call, so that it gets cached properly without skipping the agent creation.
            person = TinyPerson(agent_spec["name"])
            self._setup_agent(person, agent_spec["_configuration"])
            self.generated_minibios.append(person.minibio())
            self.generated_names.append(person.get("name").lower())
            return person
        else:
            logger.error(f"Could not generate an agent after {attepmpts} attempts.")
            return None
        
    
    @transactional
    def _aux_model_call(self, messages, temperature):
        """
        Auxiliary method to make a model call. This is needed in order to be able to use the transactional decorator,
        due too a technicality - otherwise, the agent creation would be skipped during cache reutilization, and
        we don't want that.
        """
        return client().send_message(messages, temperature=temperature)
    
    @transactional
    def _setup_agent(self, agent, configuration):
        """
        Sets up the agent with the necessary elements.
        """
        for key, value in configuration.items():
            if isinstance(value, list):
                agent.define_several(key, value)
            else:
                agent.define(key, value)
        
        # does not return anything, as we don't want to cache the agent object itself.
    
