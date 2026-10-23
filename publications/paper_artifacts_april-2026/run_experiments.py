"""
Automated Notebook Execution Script

This script runs selected Jupyter notebooks multiple times, saves outputs to separate files,
and logs execution times. It handles errors gracefully and provides comprehensive logging.

Usage:
    python run_experiments.py

Customize the NOTEBOOK_FILES list below with the notebooks you want to run.
"""

import json
import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Jupyter/IPython imports for cell-level execution
try:
    import nbformat
    from nbconvert.preprocessors import ExecutePreprocessor
    from nbconvert.preprocessors.execute import CellExecutionError

    JUPYTER_AVAILABLE = True
except ImportError:
    JUPYTER_AVAILABLE = False
    logger.warning(
        "⚠️  nbformat/nbconvert not available. Cell-level progress reporting disabled."
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("experiment_runs.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION - Customize this section
# =============================================================================

# List of notebook files to run (customize this list with your desired notebooks)
NOTEBOOK_FILES = [
    "Brainstorming and Focus Group Quantitative Experimentation 1.ipynb",
    "Brainstorming and Focus Group Quantitative Experimentation 2.1.ipynb",
    "Brainstorming and Focus Group Quantitative Experimentation 2.2.ipynb",
    "Brainstorming and Focus Group Quantitative Experimentation 2.3.ipynb",
]

# Number of times to run each notebook: Control, Treatment and comparison
NUM_RUNS = 3

# Output directory for results
OUTPUT_DIR = "experiment_outputs"

# Timeout for each notebook execution (in seconds)
TIMEOUT_SECONDS = 60 * 60 * 24  # 24 hours per notebook at most

# Enable cell-level progress reporting (requires nbformat/nbconvert)
ENABLE_CELL_PROGRESS = True

# Cell execution timeout (in seconds)
CELL_TIMEOUT_SECONDS = 60 * 60 * 5  # 5 hours per cell at most

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def setup_output_directory():
    """Create output directory structure."""
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(exist_ok=True)

    # Create subdirectories for each notebook
    for notebook in NOTEBOOK_FILES:
        notebook_name = Path(notebook).stem
        notebook_dir = output_path / notebook_name
        notebook_dir.mkdir(exist_ok=True)

    logger.info(f"Output directory structure created at: {output_path.absolute()}")


def get_notebook_name(notebook_file):
    """Extract clean notebook name from filename."""
    return Path(notebook_file).stem


class ProgressReportingExecutePreprocessor(ExecutePreprocessor):
    """
    Custom ExecutePreprocessor that reports progress for each cell.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.total_cells = 0
        self.current_cell = 0

    def preprocess(self, nb, resources=None, km=None):
        """Count total executable cells before processing."""
        self.total_cells = sum(1 for cell in nb.cells if cell.cell_type == "code")
        self.current_cell = 0
        logger.info(f"    📊 Total executable cells: {self.total_cells}")
        return super().preprocess(nb, resources, km)

    def preprocess_cell(self, cell, resources, cell_index, **kwargs):
        """Report progress before executing each cell."""
        if cell.cell_type == "code":
            self.current_cell += 1
            cell_source_preview = (
                cell.source[:100].replace("\n", " ") if cell.source else "<empty>"
            )
            if len(cell.source) > 100:
                cell_source_preview += "..."
            logger.info(
                f"    🔄 Executing cell {self.current_cell}/{self.total_cells}: {cell_source_preview}"
            )

        cell_start_time = time.time()

        try:
            cell, resources = super().preprocess_cell(
                cell, resources, cell_index, **kwargs
            )

            if cell.cell_type == "code":
                execution_time = time.time() - cell_start_time
                logger.info(
                    f"    ✅ Cell {self.current_cell} completed in {execution_time:.2f}s"
                )

            return cell, resources

        except CellExecutionError as e:
            execution_time = time.time() - cell_start_time
            logger.error(
                f"    ❌ Cell {self.current_cell} failed after {execution_time:.2f}s: {str(e)[:200]}"
            )
            raise
        except Exception as e:
            execution_time = time.time() - cell_start_time
            logger.error(
                f"    💥 Unexpected error in cell {self.current_cell} after {execution_time:.2f}s: {str(e)[:200]}"
            )
            raise


def execute_notebook_with_progress(notebook_path, output_path, run_number):
    """
    Execute a notebook with cell-level progress reporting and save the output.

    Args:
        notebook_path (str): Path to the input notebook
        output_path (str): Path where to save the executed notebook
        run_number (int): Current run number

    Returns:
        tuple: (success: bool, execution_time: float, error_message: str)
    """
    start_time = time.time()

    try:
        # Read the notebook
        with open(notebook_path, "r", encoding="utf-8") as f:
            nb = nbformat.read(f, as_version=4)

        # Create the custom executor with progress reporting
        ep = ProgressReportingExecutePreprocessor(
            timeout=CELL_TIMEOUT_SECONDS,
            kernel_name="python3",
            allow_errors=False,  # Stop on first error
        )

        logger.info(f"    🚀 Starting notebook execution with cell-level progress...")

        # Execute the notebook
        ep.preprocess(nb, {"metadata": {"path": str(notebook_path.parent)}})

        # Save the executed notebook
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            nbformat.write(nb, f)

        execution_time = time.time() - start_time
        logger.info(f"    ✅ Notebook executed successfully in {execution_time:.2f}s")
        return True, execution_time, None

    except CellExecutionError as e:
        execution_time = time.time() - start_time
        error_msg = f"Cell execution failed: {str(e)}"
        logger.error(f"    ❌ Notebook execution failed: {error_msg}")
        return False, execution_time, error_msg

    except Exception as e:
        execution_time = time.time() - start_time
        error_msg = f"Unexpected error during notebook execution: {str(e)}"
        logger.error(f"    💥 {error_msg}")
        return False, execution_time, error_msg


def execute_notebook_fallback(notebook_path, output_path, run_number):
    """
    Fallback notebook execution using nbconvert (original method).

    Args:
        notebook_path (str): Path to the input notebook
        output_path (str): Path where to save the executed notebook
        run_number (int): Current run number

    Returns:
        tuple: (success: bool, execution_time: float, error_message: str)
    """
    start_time = time.time()

    try:
        # Use nbconvert to execute the notebook
        cmd = [
            "jupyter",
            "nbconvert",
            "--to",
            "notebook",
            "--execute",
            "--output",
            str(output_path),
            str(notebook_path),
            "--ExecutePreprocessor.timeout={}".format(TIMEOUT_SECONDS),
        ]

        logger.info(f"    🚀 Executing: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS + 60,  # Extra buffer for nbconvert overhead
        )

        execution_time = time.time() - start_time

        if result.returncode == 0:
            logger.info(
                f"    ✅ Notebook executed successfully in {execution_time:.2f}s"
            )
            return True, execution_time, None
        else:
            error_msg = f"nbconvert failed with return code {result.returncode}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
            logger.error(f"    ❌ Notebook execution failed: {error_msg}")
            return False, execution_time, error_msg

    except subprocess.TimeoutExpired:
        execution_time = time.time() - start_time
        error_msg = f"Notebook execution timed out after {TIMEOUT_SECONDS} seconds"
        logger.error(f"    ⏰ {error_msg}")
        return False, execution_time, error_msg

    except Exception as e:
        execution_time = time.time() - start_time
        error_msg = f"Unexpected error during notebook execution: {str(e)}"
        logger.error(f"    💥 {error_msg}")
        return False, execution_time, error_msg


def execute_notebook(notebook_path, output_path, run_number):
    """
    Execute a notebook with optional cell-level progress reporting.

    This function automatically chooses between progress-enabled execution
    (if nbformat is available and enabled) or falls back to standard nbconvert.
    """
    if ENABLE_CELL_PROGRESS and JUPYTER_AVAILABLE:
        return execute_notebook_with_progress(notebook_path, output_path, run_number)
    else:
        if ENABLE_CELL_PROGRESS and not JUPYTER_AVAILABLE:
            logger.warning(
                "    ⚠️  Cell progress requested but nbformat not available. Using fallback method."
            )
        return execute_notebook_fallback(notebook_path, output_path, run_number)


def save_execution_summary(results):
    """Save a summary of all execution results to JSON."""
    summary_path = Path(OUTPUT_DIR) / "execution_summary.json"

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Execution summary saved to: {summary_path.absolute()}")


def print_execution_statistics(results):
    """Print summary statistics of the execution results."""
    total_notebooks = len(results)
    total_runs = sum(
        len(notebook_results["runs"]) for notebook_results in results.values()
    )
    successful_runs = sum(
        sum(1 for run in notebook_results["runs"] if run["success"])
        for notebook_results in results.values()
    )
    failed_runs = total_runs - successful_runs

    total_execution_time = sum(
        sum(run["execution_time"] for run in notebook_results["runs"])
        for notebook_results in results.values()
    )

    logger.info("=" * 60)
    logger.info("EXECUTION STATISTICS")
    logger.info("=" * 60)
    logger.info(f"📊 Total notebooks: {total_notebooks}")
    logger.info(f"🔄 Total runs: {total_runs}")
    logger.info(f"✅ Successful runs: {successful_runs}")
    logger.info(f"❌ Failed runs: {failed_runs}")
    logger.info(f"📈 Success rate: {(successful_runs/total_runs)*100:.1f}%")
    logger.info(
        f"⏱️  Total execution time: {total_execution_time:.2f}s ({total_execution_time/60:.1f} minutes)"
    )
    logger.info(f"⏱️  Average time per run: {total_execution_time/total_runs:.2f}s")
    logger.info("=" * 60)


# =============================================================================
# MAIN EXECUTION FUNCTION
# =============================================================================


def run_experiments():
    """Main function to run all notebook experiments."""
    logger.info("🚀 Starting automated notebook execution experiments")
    logger.info(f"📋 Notebooks to run: {len(NOTEBOOK_FILES)}")
    logger.info(f"🔄 Runs per notebook: {NUM_RUNS}")
    logger.info(f"📁 Output directory: {OUTPUT_DIR}")

    # Setup output directory
    setup_output_directory()

    # Results tracking
    results = {}
    experiment_start_time = time.time()

    # Process each notebook
    for notebook_idx, notebook_file in enumerate(NOTEBOOK_FILES, 1):
        logger.info(
            f"\n📓 Processing notebook {notebook_idx}/{len(NOTEBOOK_FILES)}: {notebook_file}"
        )

        # Check if notebook file exists
        notebook_path = Path(notebook_file)
        if not notebook_path.exists():
            logger.warning(f"⚠️  Notebook file not found: {notebook_path.absolute()}")
            continue

        notebook_name = get_notebook_name(notebook_file)
        notebook_results = {
            "notebook_file": notebook_file,
            "notebook_name": notebook_name,
            "runs": [],
        }

        # Run the notebook multiple times
        for run_num in range(1, NUM_RUNS + 1):
            logger.info(f"  🔄 Run {run_num}/{NUM_RUNS}")

            # Create short output filename to avoid Windows path length issues
            # The notebook name is preserved in the parent folder name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"run{run_num:02d}_{timestamp}.ipynb"
            output_path = Path(OUTPUT_DIR) / notebook_name / output_filename

            # Execute the notebook
            success, execution_time, error_message = execute_notebook(
                notebook_path, output_path, run_num
            )

            # Record the results
            run_result = {
                "run_number": run_num,
                "success": success,
                "execution_time": execution_time,
                "output_file": str(output_path) if success else None,
                "error_message": error_message,
                "timestamp": datetime.now().isoformat(),
            }

            notebook_results["runs"].append(run_result)

            if not success:
                logger.warning(f"  ⚠️  Run {run_num} failed - continuing with next run")

        results[notebook_name] = notebook_results

    # Calculate total experiment time
    total_experiment_time = time.time() - experiment_start_time

    # Save results and print statistics
    save_execution_summary(results)
    print_execution_statistics(results)

    logger.info(
        f"\n🏁 Experiment completed in {total_experiment_time:.2f}s ({total_experiment_time/60:.1f} minutes)"
    )
    logger.info(f"📊 Results saved to: {Path(OUTPUT_DIR).absolute()}")


def check_requirements():
    """Check if required tools are available."""
    try:
        # Check if jupyter is available
        result = subprocess.run(
            ["jupyter", "--version"], capture_output=True, text=True
        )
        if result.returncode != 0:
            logger.error("❌ Jupyter is not installed or not in PATH")
            return False
        logger.info(f"✅ Jupyter found: {result.stdout.strip()}")

        # Check if nbconvert is available
        result = subprocess.run(
            ["jupyter", "nbconvert", "--version"], capture_output=True, text=True
        )
        if result.returncode != 0:
            logger.error("❌ nbconvert is not available")
            return False
        logger.info(f"✅ nbconvert found: {result.stdout.strip()}")

        # Check for enhanced progress reporting capabilities
        if ENABLE_CELL_PROGRESS:
            if JUPYTER_AVAILABLE:
                logger.info(
                    "✅ Cell-level progress reporting enabled (nbformat available)"
                )
            else:
                logger.warning(
                    "⚠️  Cell-level progress requested but nbformat not available"
                )
                logger.info(
                    "💡 To enable cell progress: pip install nbformat nbconvert"
                )
        else:
            logger.info("ℹ️  Cell-level progress reporting disabled")

        return True
    except FileNotFoundError:
        logger.error("❌ Jupyter is not installed or not in PATH")
        return False


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    try:
        # Check requirements
        if not check_requirements():
            logger.error(
                "❌ Requirements check failed. Please install Jupyter and nbconvert."
            )
            sys.exit(1)

        # Run the experiments
        run_experiments()

    except KeyboardInterrupt:
        logger.info("\n🛑 Execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {str(e)}")
        sys.exit(1)
