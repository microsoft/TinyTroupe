import sys
import threading
import time
from tinytroupe.utils import logger
    

def check_threads_for_lock(blocked_keywords=None):
    """
    Inspects all active threads and reports if any thread appears to be blocked
    on a lock acquisition or waiting condition.

    :param blocked_keywords: List of function names or keywords to check in stack frames.
    """
    if blocked_keywords is None:
        blocked_keywords = ['acquire', 'wait', 'Condition.wait']
    
    frames = sys._current_frames()
    print("\n--- Thread Lock Check ---")
    for thread in threading.enumerate():
        frame = frames.get(thread.ident)
        if not frame:
            continue
        
        stack_trace = []
        suspected_block = False
        while frame:
            func_name = frame.f_code.co_name
            file_name = frame.f_code.co_filename
            line_no = frame.f_lineno
            stack_trace.append(f"{func_name} at {file_name}:{line_no}")
            
            if any(keyword in func_name for keyword in blocked_keywords):
                suspected_block = True
            frame = frame.f_back
        
        if suspected_block:
            logger.info(f"[WARNING] Thread '{thread.name}' (ID: {thread.ident}) may be blocked.")
            logger.info("Stack trace:")
            for trace in stack_trace:
                logger.info(f"  {trace}")
        else:
            logger.info(f"[OK] Thread '{thread.name}' is running normally.")

def monitor_threads(interval=5, stop_event=None):
    """
    Periodically checks all threads for potential lock blocking.

    :param interval: Time in seconds between checks.
    :param stop_event: Optional threading.Event that signals monitoring should stop.
    """
    try:
        while True:
            check_threads_for_lock()
            if stop_event is None:
                time.sleep(interval)
            else:
                if stop_event.wait(interval):
                    break
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")

# Example usage:
# monitor_threads(interval=5)