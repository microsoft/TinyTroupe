
import threading

import pytest
from tinytroupe.utils.concurrency import monitor_threads
import time

##########################
# Global testing options
##########################
refresh_cache = False
use_cache = False
#test_examples = False # will use Pytest markers instead

_MONITOR_INTERVAL_SECONDS = 30
monitor_stop_event = None
monitor_thread = None

_DELAY = 0  # seconds

@pytest.fixture(autouse=True)
def pause_between_tests():
    """Fixture to add a delay between tests to reduce resource contention."""
    yield
    if _DELAY > 0:
        print(f"\n****** Pausing for {_DELAY} seconds between tests to reduce resource contention... ******\n")
        time.sleep(_DELAY)

#def pytest_sessionstart(session):
#    global monitor_stop_event, monitor_thread
#    # Start monitoring in the background to observe potential deadlocks
#    monitor_stop_event = threading.Event()
#    monitor_thread = threading.Thread(
#        target=monitor_threads,
#        args=(_MONITOR_INTERVAL_SECONDS, monitor_stop_event),
#        daemon=True,
#    )
#    monitor_thread.start()
#    
#def pytest_sessionfinish(session, exitstatus):
#    global monitor_stop_event, monitor_thread
#    print("************************* Test session finished *************************")
#    # Signal the monitoring thread to stop once pytest is done.
#    if monitor_stop_event is not None:
#        monitor_stop_event.set()
#    if monitor_thread is not None:
#        monitor_thread.join(timeout=_MONITOR_INTERVAL_SECONDS)

def pytest_addoption(parser):
    parser.addoption("--refresh_cache", action="store_true", help="Refreshes the API cache for the tests, to ensure the latest data is used.")
    parser.addoption("--use_cache", action="store_true", help="Uses the API cache for the tests, to reduce the number of actual API calls.")
    #parser.addoption("--test_examples", action="store_true", help="Also reruns all examples to make sure they still work. This can substantially increase the test time.")

def pytest_generate_tests(metafunc):
    global refresh_cache, use_cache, test_examples
    refresh_cache = metafunc.config.getoption("refresh_cache")
    use_cache = metafunc.config.getoption("use_cache")
    #test_examples = metafunc.config.getoption("test_examples")

    # Get the name of the test case being analyzed
    test_case_name = metafunc.function.__name__

    # Show info to user for this specific test (get from metafunc)
    print(f"Test case: {test_case_name}")
    print(f"  - refresh_cache: {refresh_cache}")
    print(f"  - use_cache: {use_cache}")
    #print(f"  - test_examples: {test_examples}")
    print("")


