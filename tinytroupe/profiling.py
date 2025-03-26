"""
Provides mechanisms for creating understanding the characteristics of agent populations, such as
their age distribution, typical interests, and so on.

Guideline for plotting the methods: all plot methods should also return a Pandas dataframe with the data used for 
plotting.
"""
import pandas as pd
import matplotlib.pyplot as plt
from tinytroupe.agent import TinyPerson


import pandas as pd
import matplotlib.pyplot as plt
from typing import List


class Profiler:

    def __init__(self, attributes: List[str]=["age", "occupation.title", "nationality"]) -> None: 
        self.attributes = attributes
        
        self.attributes_distributions = {} # attribute -> Dataframe

    def profile(self, agents: List[dict], plot:bool=True) -> dict:   
        """
        Profiles the given agents.

        Args:
            agents (List[dict]): The agents to be profiled.
        
        """

        self.attributes_distributions = self._compute_attributes_distributions(agents)

        if plot:
            self.render()
            
        return self.attributes_distributions

    def render(self) -> None:
        """
        Renders the profile of the agents.
        """
        return self._plot_attributes_distributions()
        

    def _compute_attributes_distributions(self, agents:list) -> dict:
        """
        Computes the distributions of the attributes for the agents.

        Args:
            agents (list): The agents whose attributes distributions are to be computed.
        
        Returns:
            dict: The distributions of the attributes.
        """
        distributions = {}
        for attribute in self.attributes:
            distributions[attribute] = self._compute_attribute_distribution(agents, attribute)
        
        return distributions
    
    def _compute_attribute_distribution(self, agents: list, attribute: str) -> pd.DataFrame:
        """
        Computes the distribution of a given attribute for the agents and plots it.

        Args:
            agents (list): The agents whose attribute distribution is to be plotted.
        
        Returns:
            pd.DataFrame: The data used for plotting.
        """
        values = [agent.get(attribute) for agent in agents]

        # corresponding dataframe of the value counts. Must be ordered by value, not counts 
        df = pd.DataFrame(values, columns=[attribute]).value_counts().sort_index()

        return df
    
    def _plot_attributes_distributions(self) -> None:
        """
        Plots the distributions of the attributes for the agents.
        """

        for attribute in self.attributes:
            self._plot_attribute_distribution(attribute)
        
    def _plot_attribute_distribution(self, attribute: str) -> pd.DataFrame:
        """
        Plots the distribution of a given attribute for the agents.

        Args:
            attribute (str): The attribute whose distribution is to be plotted.
        
        Returns:
            pd.DataFrame: The data used for plotting.
        """

        df = self.attributes_distributions[attribute]
        df.plot(kind='bar', title=f"{attribute.capitalize()} distribution")
        plt.show()



        


