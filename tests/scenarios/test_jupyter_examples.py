import ast
import os
import sys

import nbformat
import pytest
from nbconvert.preprocessors import ExecutePreprocessor

sys.path.insert(
    0, "../../tinytroupe/"
)  # ensures that the package is imported from the parent directory, not the Python installation
sys.path.insert(
    0, "../../"
)  # ensures that the package is imported from the parent directory, not the Python installation
sys.path.insert(
    0, ".."
)  # ensures that the package is imported from the parent directory, not the Python installation

import time

import conftest

# Set the folder containing the notebooks
NOTEBOOK_FOLDER = os.path.join(
    os.path.dirname(__file__), "../../examples/"
)  # Update this path

# Set a timeout for long-running notebooks
TIMEOUT = 6000

KERNEL_NAME = "python3"  # "py310"


def get_notebooks(folder):
    """Retrieve all Jupyter notebook files from the specified folder."""
    return [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.endswith(".ipynb")
        and not ".executed." in f
        and not ".local." in f
        and not ".archival." in f
        and not ".final." in f
    ]


@pytest.mark.core
@pytest.mark.parametrize("notebook_path", get_notebooks(NOTEBOOK_FOLDER))
def test_notebook_imports(monkeypatch, notebook_path):
    """Every active example imports successfully with the current public API."""
    notebook = nbformat.read(notebook_path, as_version=4)
    import_cell = next(cell for cell in notebook.cells if cell.cell_type == "code")
    monkeypatch.chdir(NOTEBOOK_FOLDER)
    monkeypatch.setattr(sys, "path", sys.path.copy())
    exec(compile(import_cell.source, notebook_path, "exec"), {})


@pytest.mark.core
@pytest.mark.parametrize("notebook_path", get_notebooks(NOTEBOOK_FOLDER))
def test_notebook_factory_configuration(notebook_path):
    """Factory population descriptions require a size; standalone context uses context=."""
    notebook = nbformat.read(notebook_path, as_version=4)
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        for node in ast.walk(ast.parse(cell.source)):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "TinyPersonFactory"
            ):
                continue
            keywords = {keyword.arg for keyword in node.keywords}
            has_description = bool(node.args) or "sampling_space_description" in keywords
            has_population_size = len(node.args) > 1 or "total_population_size" in keywords
            assert not has_description or has_population_size, (
                f"{notebook_path}: a standalone factory context must use context=; "
                "sampling_space_description is only used with total_population_size."
            )


@pytest.mark.slow
@pytest.mark.examples
@pytest.mark.notebooks
@pytest.mark.parametrize("notebook_path", get_notebooks(NOTEBOOK_FOLDER))
def test_notebook_execution(notebook_path):
    """Execute a Jupyter notebook and assert that no exceptions occur, printing execution time with emojis."""

    with open(notebook_path, "r", encoding="utf-8") as nb_file:
        notebook = nbformat.read(nb_file, as_version=4)

        # save a backup of the original notebook
        backup_path = notebook_path.replace(".ipynb", ".backup.local.ipynb")
        with open(backup_path, "w", encoding="utf-8") as backup_file:
            nbformat.write(notebook, backup_file)

        # Execute the notebook
        print(f"🚀 Executing notebook: {notebook_path} with kernel: {KERNEL_NAME}")
        ep = ExecutePreprocessor(timeout=TIMEOUT, kernel_name=KERNEL_NAME)

        start_time = time.time()
        try:
            ep.preprocess(notebook, {"metadata": {"path": NOTEBOOK_FOLDER}})
            elapsed = time.time() - start_time
            print(
                f"✅ Notebook {notebook_path} executed successfully in {elapsed:.2f} seconds. ⏱️"
            )

            # save the executed notebook in its original location
            with open(notebook_path, "w", encoding="utf-8") as out_file:
                nbformat.write(notebook, out_file)

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ Notebook {notebook_path} failed after {elapsed:.2f} seconds. ⚠️")
            pytest.fail(f"Notebook {notebook_path} raised an exception: {e}")

        finally:
            print(f"💾 Executed notebook saved as: {notebook_path}")
