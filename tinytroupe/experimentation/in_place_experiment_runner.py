import IPython
from IPython.display import display, Javascript

from tinytroupe.experimentation import logger
from tinytroupe.experimentation.statistical_tests import StatisticalTester

class InPlaceExperimentRunner:
    """
    This class allows the execution of "in-place" experiments. That is to say, it allows the user to run experiments on the current codebase without needing to create a separate script for each experiment. This is achieved by:
       - having an external configuration file that saves the overall state of the experiment.
       - having methods that clients can call to know what is the current experiment (e.g. treatment, control, etc.)
       - clients taking different actions based on the current active experiment.
    """
    def __init__(self, config_file_path: str="experiment_config.json"):
        self.config_file_path = config_file_path
        self.experiment_config = self._load_or_create_config(config_file_path)
        self._save_config()

    def add_experiment(self, experiment_name: str):
        """
        Add a new experiment to the configuration file.

        Args:
            experiment_name (str): Name of the experiment to add.
        """
        if experiment_name in self.experiment_config["experiments"]:
            logger.info(f"Experiment '{experiment_name}' already exists, nothihg to add.")
        else:
            self.experiment_config["experiments"][experiment_name] = {}
            self._save_config()
    
    def activate_next_experiment(self):
        """
        Activate the next experiment in the list.
        """
        if not self.experiment_config["finished_all_experiments"]:
            experiments = list(self.experiment_config["experiments"].keys())
            if not experiments:
                raise ValueError("No experiments available to activate.")
            
            current_experiment = self.experiment_config.get("active_experiment")
            if current_experiment:
                current_index = experiments.index(current_experiment)
                next_index = current_index + 1
                if next_index >= len(experiments):
                    self.experiment_config["active_experiment"] = None
                    self.experiment_config["finished_all_experiments"] = True
                else:
                    self.experiment_config["active_experiment"] = experiments[next_index]
            else:
                self.experiment_config["active_experiment"] = experiments[0] if experiments else None
            
            self._save_config()
        
        else:
            logger.info("All experiments have been finished. No more experiments to activate.")

    def fix_active_experiment(self, experiment_name: str):
        """
        Fix the active experiment to a specific one.

        Args:
            experiment_name (str): Name of the experiment to fix.
        """
        if experiment_name not in self.experiment_config["experiments"]:
            raise ValueError(f"Experiment '{experiment_name}' does not exist.")
        
        self.experiment_config["active_experiment"] = experiment_name
        self.experiment_config["finished_all_experiments"] = False
        self._save_config()

    def get_active_experiment(self):

        """
        Get the currently active experiment.

        Returns:
            str: Name of the active experiment.
        """
        return self.experiment_config.get("active_experiment")

    def has_finished_all_experiments(self):
        """
        Check if all experiments have been finished.

        Returns:
            bool: True if all experiments are finished, False otherwise.
        """
        return self.experiment_config.get("finished_all_experiments", False)

    def add_experiment_results(self, experiment_name: str, result: dict):
        """
        Add a result for a specific experiment.

        Args:
            experiment_name (str): Name of the experiment.
            result (dict): Result to add.
        """
        if experiment_name not in self.experiment_config["experiments"]:
            raise ValueError(f"Experiment '{experiment_name}' does not exist.")
        
        if "results" not in self.experiment_config["experiments"][experiment_name]:
            self.experiment_config["experiments"][experiment_name]["results"] = {}
        
        self.experiment_config["experiments"][experiment_name]["results"].update(result)
        self._save_config()
    
    def get_experiment_results(self, experiment_name: str):
        """
        Get the results of a specific experiment.

        Args:
            experiment_name (str): Name of the experiment.

        Returns:
            list: List of results for the specified experiment.
        """
        if experiment_name not in self.experiment_config["experiments"]:
            raise ValueError(f"Experiment '{experiment_name}' does not exist.")
        
        return self.experiment_config["experiments"][experiment_name].get("results", [])
    
    def run_statistical_tests(self, control_experiment_name: str):
        """
        Run statistical tests on the results of experiments, comparing one selected as control to the others,
        which are considered treatments.
        
        Args:
            control_experiment_name (str): Name of the control experiment. All other experiments will be treated as treatments 
                and compared to this one.

        Returns:
            dict: Results of the statistical tests.
        """
        if not self.experiment_config["experiments"]:
            raise ValueError("No experiments available to run statistical tests.")
        
        # pop control from cloned list of experiment results
        experiment_results = self.experiment_config["experiments"].copy()
        control_experiment_results = {control_experiment_name: experiment_results.pop(control_experiment_name, None)}

        tester = StatisticalTester(control_experiment_data=control_experiment_results, 
                                   treatments_experiment_data=experiment_results,
                                   results_key="results")
        
        results = tester.run_test()
        self.experiment_config["experiments"][control_experiment_name]["statistical_test_results_vs_others"] = results
        self._save_config()
        
        return results
       
    def _load_or_create_config(self, config_file_path: str):
        """
        Load the configuration file if it exists, otherwise create a new one.

        Args:
            config_file_path (str): Path to the configuration file.

        Returns:
            dict: Loaded or newly created configuration.
        """
        try:
            config = self._load_config(config_file_path)
            logger.warning(f"Configuration file '{config_file_path}' exists and was loaded successfully. If you are trying to fully rerun the experiments, delete it first.")
            return config
        
        except FileNotFoundError:
            return self._create_default_config(config_file_path)

    def _create_default_config(self, config_file_path):
        """
        Create a default configuration file.

        Returns:
            dict: Default configuration.
        """
        default_config = {
            "experiments": {},
            "active_experiment": None,
            "finished_all_experiments": False
        }

        return default_config

    def _load_config(self, config_file_path: str):
        import json
        with open(config_file_path, 'r') as file:
            config = json.load(file)
        return config
    
    def _save_config(self):
        import json
        with open(self.config_file_path, 'w') as file:
            json.dump(self.experiment_config, file, indent=4)
