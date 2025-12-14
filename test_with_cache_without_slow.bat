REM This script runs pytest on the tests directory without using examples or slow tests, in order to finish faster.
pytest -s --use_cache -m "not examples and not slow"