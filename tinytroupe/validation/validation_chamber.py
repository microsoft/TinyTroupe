from tinytroupe.experimentation import Proposition


class ValidationChamber:
    """  
    An Validation Chamber is a container where autonomous agents can be put to be validated with respect to various custom validation tasks.

    Validation tasks types include:
      - Question answering: given either a concrete question or a question pattern (to be instantitated via an LLM call), and an expectation, 
        the agent is expected to answer the question correctly. To check correctness, an LLM-based Proposer is used.
      - Behavioral patterns:
          * repeated actions - does the agent keep repeating the same action like a crazy person?
          * self-consistency - does the agent contradict itself over time?
    

    The class also provides convenience auxiliary methods to:
      - generate reasonable question/answer pairs, given some general overall scenario and agent description.
      - generate reasonable behavioral patterns, given some general overall scenario and agent description.
          
    """ 

