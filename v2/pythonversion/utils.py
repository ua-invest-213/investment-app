# utils.py
import time
from datetime import datetime

# Global variables for rate limiting
api_call_count = 0
start_time = time.time()

def rate_limit_check():
    """
    Check if the API call limit has been reached and wait if necessary.
    """
    global api_call_count, start_time
    elapsed_time = time.time() - start_time
    if elapsed_time > 60:
        api_call_count = 0
        start_time = time.time()
    if api_call_count >= 5:
        wait_time = 60 - elapsed_time
        print(f"Rate limit reached. Waiting for {wait_time:.2f} seconds...")
        time.sleep(wait_time)
        api_call_count = 0
        start_time = time.time()
    api_call_count += 1

def log_error(message):
    """
    Log errors to a file with a timestamp.
    """
    with open("error_log.txt", "a") as log_file:
        log_file.write(f"{datetime.now()} - {message}\n")