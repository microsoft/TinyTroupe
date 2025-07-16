import os
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import pytest

import sys
sys.path.insert(0, '../../tinytroupe/') # ensures that the package is imported from the parent directory, not the Python installation
sys.path.insert(0, '../../') # ensures that the package is imported from the parent directory, not the Python installation
sys.path.insert(0, '..') # ensures that the package is imported from the parent directory, not the Python installation

import conftest

# Set the folder containing the notebooks
NOTEBOOK_FOLDER = os.path.join(os.path.dirname(__file__), "../../examples/")  # Update this path

# Set a timeout for long-running notebooks
TIMEOUT = 6000

KERNEL_NAME = "python3" #"py310"


def get_notebooks(folder):
    """Retrieve all Jupyter notebook files from the specified folder."""
    return [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.endswith(".ipynb") and not ".executed." in f and not ".local." in f
    ]

@pytest.mark.examples
@pytest.mark.notebooks
@pytest.mark.parametrize("notebook_path", get_notebooks(NOTEBOOK_FOLDER))
def test_notebook_execution(notebook_path):
    """Execute a Jupyter notebook and assert that no exceptions occur."""

    with open(notebook_path, "r", encoding="utf-8") as nb_file:
        notebook = nbformat.read(nb_file, as_version=4)

        # save a backup of the original notebook
        backup_path = notebook_path.replace(".ipynb", ".backup.local.ipynb")
        with open(backup_path, "w", encoding="utf-8") as backup_file:
            nbformat.write(notebook, backup_file)

        # Execute the notebook
        print(f"Executing notebook: {notebook_path} with kernel: {KERNEL_NAME}")
        ep = ExecutePreprocessor(timeout=TIMEOUT, kernel_name=KERNEL_NAME)

        try:
            ep.preprocess(notebook, {'metadata': {'path': NOTEBOOK_FOLDER}})
            print(f"Notebook {notebook_path} executed successfully.")

        except Exception as e:
            pytest.fail(f"Notebook {notebook_path} raised an exception: {e}")
        
        finally:
            
            # save the executed notebook in its original location
            with open(notebook_path, "w", encoding="utf-8") as out_file:
                nbformat.write(notebook, out_file)

            print(f"Executed notebook saved as: {notebook_path}")

