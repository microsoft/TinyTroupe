##########################
# Global testing options
##########################
refresh_cache = False
use_cache = False
#test_examples = False # will use Pytest markers instead

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