REM This script runs the gpt-4.1-mini compatibility tests with caching enabled.
REM These tests verify TinyTroupe works correctly with the gpt-4.1-mini model.
pytest -s --use_cache -m "gpt41mini"
