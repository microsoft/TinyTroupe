from concurrent.futures import ThreadPoolExecutor
from typing import List, Any, Callable, Optional, Dict, Tuple, TypeVar, Iterator, Iterable
from itertools import product

def parallel_map(
    objects: List[Any],
    operation: Callable[[Any], Any],
    max_workers: Optional[int] = None
) -> List[Any]:
    """
    Execute operations on multiple objects in parallel and return the results.
    
    Args:
        objects: List of objects to process
        operation: A callable (typically a lambda) that takes each object and returns a result
        max_workers: Maximum number of threads to use for parallel execution
                    (None means use the default, which is min(32, os.cpu_count() + 4))
    
    Returns:
        List of results in the same order as the input objects
    
    Example:
        # For propositions p1, p2, p3
        results = parallel_map([p1, p2, p3], lambda p: p.check())
        
        # With arguments
        results = parallel_map(
            [p1, p2, p3], 
            lambda p: p.check(additional_context="Some context", return_full_response=True)
        )
        
        # Works with any operation
        scores = parallel_map([p1, p2, p3], lambda p: p.score())
    """
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(operation, objects))
    
    return results


K = TypeVar('K')  # Key type
V = TypeVar('V')  # Value type
R = TypeVar('R')  # Result type

def parallel_map_dict(
    dictionary: Dict[K, V],
    operation: Callable[[Tuple[K, V]], R],
    max_workers: Optional[int] = None
) -> Dict[K, R]:
    """
    Execute operations on dictionary items in parallel and return results as a dictionary.
    
    Args:
        dictionary: Dictionary whose items will be processed
        operation: A callable that takes a (key, value) tuple and returns a result
        max_workers: Maximum number of threads to use
    
    Returns:
        Dictionary mapping original keys to operation results
    
    Example:
        # For environment propositions
        results = parallel_map_dict(
            environment_propositions,
            lambda item: item[1].score(world, return_full_response=True)
        )
    """
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create a list of (key, result) tuples
        items = list(dictionary.items())
        results = list(executor.map(operation, items))
        
        # Combine original keys with results
        return {item[0]: result for item, result in zip(items, results)}


def parallel_map_cross(
    iterables: List[Iterable],
    operation: Callable[..., R],
    max_workers: Optional[int] = None
) -> List[R]:
    """
    Apply operation to each combination of elements from the iterables in parallel.
    This is similar to using nested loops.
    
    Args:
        iterables: List of iterables to generate combinations from
        operation: A callable that takes elements from each iterable and returns a result
        max_workers: Maximum number of threads to use
    
    Returns:
        List of results from applying operation to each combination
    
    Example:
        # For every agent and proposition
        results = parallel_map_cross(
            [agents, agent_propositions.items()],
            lambda agent, prop_item: (prop_item[0], prop_item[1].score(agent))
        )
    """
    combinations = list(product(*iterables))
    
    def apply_to_combination(combo):
        return operation(*combo)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(apply_to_combination, combinations))
    
    return results