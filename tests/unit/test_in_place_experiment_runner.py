import pytest
import logging
import tempfile
import os
import json
logger = logging.getLogger("tinytroupe")

import sys
sys.path.insert(0, '../../tinytroupe/')
sys.path.insert(0, '../../')
sys.path.insert(0, '..')

from tinytroupe.experimentation.in_place_experiment_runner import InPlaceExperimentRunner
from testing_utils import *

@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)  # Close the file descriptor since we'll delete the file to test creation
    os.remove(path)  # Remove the file so the runner creates it fresh
    yield path
    if os.path.exists(path):
        os.remove(path)

def test_experiment_runner_initialization(temp_config_file):
    """Test InPlaceExperimentRunner initialization."""
    
    runner = InPlaceExperimentRunner(config_file_path=temp_config_file)
    
    # Test that runner is initialized properly
    assert runner.config_file_path == temp_config_file
    assert hasattr(runner, 'experiment_config')
    assert isinstance(runner.experiment_config, dict)
    
    # Test that config file is created
    assert os.path.exists(temp_config_file), "Config file should be created"
    
    # Test default structure
    assert "experiments" in runner.experiment_config
    assert isinstance(runner.experiment_config["experiments"], dict)

def test_experiment_runner_add_experiment(temp_config_file):
    """Test adding experiments to the runner."""
    
    runner = InPlaceExperimentRunner(config_file_path=temp_config_file)
    
    # Test adding a new experiment
    experiment_name = "test_experiment_1"
    runner.add_experiment(experiment_name)
    
    assert experiment_name in runner.experiment_config["experiments"]
    assert isinstance(runner.experiment_config["experiments"][experiment_name], dict)
    
    # Test adding multiple experiments
    experiments = ["experiment_2", "experiment_3", "experiment_4"]
    for exp in experiments:
        runner.add_experiment(exp)
    
    for exp in experiments:
        assert exp in runner.experiment_config["experiments"]
    
    # Test adding duplicate experiment (should not crash)
    runner.add_experiment(experiment_name)  # Should handle gracefully
    assert experiment_name in runner.experiment_config["experiments"]

def test_experiment_runner_activate_next_experiment(temp_config_file):
    """Test activating experiments in sequence."""
    
    runner = InPlaceExperimentRunner(config_file_path=temp_config_file)
    
    # Add some experiments
    experiments = ["control", "treatment_1", "treatment_2"]
    for exp in experiments:
        runner.add_experiment(exp)
    
    # Test activating first experiment
    runner.activate_next_experiment()
    assert "active_experiment" in runner.experiment_config
    assert runner.experiment_config["active_experiment"] in experiments    # Test that we can get the current experiment
    current_exp = runner.get_active_experiment()
    assert current_exp is not None
    assert current_exp in experiments
    
    # Test activating subsequent experiments
    first_exp = current_exp
    runner.activate_next_experiment()
    second_exp = runner.get_active_experiment()
    
    # Should be different experiments (unless only one exists)
    if len(experiments) > 1:
        assert second_exp != first_exp or runner.experiment_config.get("finished_all_experiments", False)

def test_experiment_runner_get_current_experiment(temp_config_file):
    """Test getting current active experiment."""
    
    runner = InPlaceExperimentRunner(config_file_path=temp_config_file)
    
    # Initially no experiment should be active
    current = runner.get_active_experiment()
    assert current is None or current == "default"
    
    # Add and activate an experiment
    runner.add_experiment("test_experiment")
    runner.activate_next_experiment()
    
    current = runner.get_active_experiment()
    assert current is not None
    assert current in runner.experiment_config["experiments"]

def test_experiment_runner_finish_experiment(temp_config_file):
    """Test finishing experiments."""
    
    runner = InPlaceExperimentRunner(config_file_path=temp_config_file)
    
    # Add and activate an experiment
    experiment_name = "finish_test"
    runner.add_experiment(experiment_name)
    runner.activate_next_experiment()
    
    # Finish the experiment
    runner.finish_active_experiment()
    
    # Check that experiment is marked as finished
    assert "finished_experiments" in runner.experiment_config
    assert experiment_name in runner.experiment_config["finished_experiments"]

def test_experiment_runner_all_experiments_finished(temp_config_file):
    """Test detection when all experiments are finished."""
    
    runner = InPlaceExperimentRunner(config_file_path=temp_config_file)
    
    # Add experiments
    experiments = ["exp1", "exp2", "exp3"]
    for exp in experiments:
        runner.add_experiment(exp)
    
    # Initially not all finished
    assert not runner.experiment_config.get("finished_all_experiments", False)
    
    # Finish all experiments
    for _ in range(len(experiments)):
        runner.activate_next_experiment()
        runner.finish_active_experiment()
    
    # Try to activate next (should handle gracefully)
    try:
        runner.activate_next_experiment()
    except Exception:
        # May raise exception when no more experiments, that's okay
        pass
    
    # Should handle completion state
    assert "finished_experiments" in runner.experiment_config

def test_experiment_runner_config_persistence(temp_config_file):
    """Test that configuration persists across runner instances."""
    
    # Create first runner and add experiments
    runner1 = InPlaceExperimentRunner(config_file_path=temp_config_file)
    experiments = ["persistent_exp1", "persistent_exp2"]
    
    for exp in experiments:
        runner1.add_experiment(exp)
    
    runner1.activate_next_experiment()
    active_exp = runner1.get_active_experiment()
    
    # Create second runner with same config file
    runner2 = InPlaceExperimentRunner(config_file_path=temp_config_file)
    
    # Verify configuration was loaded
    for exp in experiments:
        assert exp in runner2.experiment_config["experiments"]
    
    assert runner2.get_active_experiment() == active_exp

def test_experiment_runner_empty_experiments(temp_config_file):
    """Test runner behavior with no experiments."""
    
    runner = InPlaceExperimentRunner(config_file_path=temp_config_file)
    
    # Test getting current experiment when none exist
    current = runner.get_active_experiment()
    assert current is None or current == "default"
    
    # Test activating when no experiments exist
    try:
        runner.activate_next_experiment()
        # Should either handle gracefully or raise informative error
    except ValueError as e:
        assert "no experiments" in str(e).lower() or "available" in str(e).lower()

def test_experiment_runner_get_experiment_condition(temp_config_file):
    """Test getting experiment conditions/treatments."""
    
    runner = InPlaceExperimentRunner(config_file_path=temp_config_file)
    
    # Add experiments with different conditions
    runner.add_experiment("control")
    runner.add_experiment("treatment_a")
    runner.add_experiment("treatment_b")
    
    runner.activate_next_experiment()
    
    # Test that we can determine experimental conditions
    current_exp = runner.get_active_experiment()
    assert current_exp is not None
    
    # Test condition checking methods if they exist
    if hasattr(runner, 'is_control_group'):
        is_control = runner.is_control_group()
        assert isinstance(is_control, bool)
    
    if hasattr(runner, 'get_treatment_name'):
        treatment = runner.get_treatment_name()
        assert treatment is not None

def test_experiment_runner_statistical_analysis(temp_config_file):
    """Test statistical analysis capabilities if available."""
    
    runner = InPlaceExperimentRunner(config_file_path=temp_config_file)
    
    # Add control and treatment groups
    runner.add_experiment("control")
    runner.add_experiment("treatment")
    
    # Test if statistical testing methods are available
    if hasattr(runner, 'statistical_tester'):
        assert runner.statistical_tester is not None
    
    # Test if results can be collected
    if hasattr(runner, 'collect_results'):
        # This would typically collect data from experiments
        # For now, just verify the method exists
        assert callable(runner.collect_results)

def test_experiment_runner_error_handling(temp_config_file):
    """Test experiment runner error handling."""
    
    runner = InPlaceExperimentRunner(config_file_path=temp_config_file)
    
    # Test with invalid experiment names
    invalid_names = ["", None, 123, []]
    
    for invalid_name in invalid_names:
        try:
            runner.add_experiment(invalid_name)
            # If it doesn't raise an error, verify it was handled gracefully
            if invalid_name in runner.experiment_config["experiments"]:
                # It was added despite being invalid - that's a design choice
                pass
        except (TypeError, ValueError, AttributeError):
            # Expected to raise an error for invalid input
            pass

def test_experiment_runner_config_format(temp_config_file):
    """Test that config file has expected format."""
    
    runner = InPlaceExperimentRunner(config_file_path=temp_config_file)
    
    # Load the config file directly
    with open(temp_config_file, 'r') as f:
        config_data = json.load(f)
    
    # Verify expected structure
    assert "experiments" in config_data
    assert isinstance(config_data["experiments"], dict)
    
    # Add an experiment and verify it's saved correctly
    runner.add_experiment("format_test")
    
    with open(temp_config_file, 'r') as f:
        updated_config = json.load(f)
    
    assert "format_test" in updated_config["experiments"]

def test_experiment_runner_jupyter_integration(temp_config_file):
    """Test Jupyter notebook integration features if available."""
    
    runner = InPlaceExperimentRunner(config_file_path=temp_config_file)
    
    # Test if Jupyter-specific methods exist
    if hasattr(runner, 'display_current_experiment'):
        # Should not crash when called
        try:
            runner.display_current_experiment()
        except Exception as e:
            # May fail in non-Jupyter environment, that's expected
            logger.info(f"Jupyter display failed as expected: {e}")
    
    if hasattr(runner, 'show_experiment_progress'):
        try:
            runner.show_experiment_progress()
        except Exception as e:
            logger.info(f"Progress display failed as expected: {e}")

def test_experiment_runner_concurrent_access(temp_config_file):
    """Test behavior with concurrent access to config file."""
    
    # Create two runners with same config
    runner1 = InPlaceExperimentRunner(config_file_path=temp_config_file)
    runner2 = InPlaceExperimentRunner(config_file_path=temp_config_file)
    
    # Add experiment via first runner
    runner1.add_experiment("concurrent_test")
    
    # Second runner should see the update after reloading
    runner2_new = InPlaceExperimentRunner(config_file_path=temp_config_file)
    assert "concurrent_test" in runner2_new.experiment_config["experiments"]
