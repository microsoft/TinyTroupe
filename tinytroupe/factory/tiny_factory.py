import copy
import random

from tinytroupe.factory import logger
import tinytroupe.utils as utils

class TinyFactory:
    """
    A base class for various types of factories. This is important because it makes it easier to extend the system, particularly 
    regarding transaction caching.
    """

    # common randomizer used for samplings, with a default initial seed to allow for reproducibility. 
    # subclases can use this directly as well.
    randomizer = random.Random(42)

    # A dict of all factories created so far.
    all_factories = {} # name -> factories
    
    def __init__(self, simulation_id:str=None) -> None:
        """
        Initialize a TinyFactory instance.

        Args:
            simulation_id (str, optional): The ID of the simulation. Defaults to None.
        """
        self.name = f"Factory {utils.fresh_id(self.__class__.__name__)}" # we need a name, but no point in making it customizable
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
    
    @classmethod
    def clear_factories(cls):
        """
        Clears the global list of all factories.
        """
        cls.all_factories = {}
        cls._clear_factories()

    @classmethod
    def _clear_factories(cls):
        """
        Additional cleanup actions can be performed here by subclasses if needed.
        """
        pass

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
 

