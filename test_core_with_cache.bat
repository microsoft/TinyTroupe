REM This script runs the core test suite for quick validation after important modifications.
REM Core tests are designed to catch critical bugs while completing in approximately 1 hour.
REM Excludes slow tests for faster execution.
pytest -s --use_cache -m "core and not slow"
