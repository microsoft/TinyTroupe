import logging
logger = logging.getLogger("tinytroupe")

###########################################################################
# Exposed API
###########################################################################
from tinytroupe.validation.tiny_person_validator import TinyPersonValidator
from tinytroupe.validation.propositions import *
from tinytroupe.validation.simulation_validator import SimulationExperimentEmpiricalValidator, SimulationExperimentDataset, SimulationExperimentEmpiricalValidationResult, validate_simulation_experiment_empirically