import requests
import time

def notify_evaluator(url, payload):
    max_retry=10
    delay=1
    headers = {"Content-Type": "application/json"}

    for attempt in range(max_retry):
        try:
            r = requests.post(url, json=payload, headers=headers)
            print(f"Response status: {r.status_code}",flush=True)
            r.raise_for_status()
            return r
        except requests.exceptions.RequestException as e:
            print("Inside the retry request block",flush=True)
            if attempt < max_retry - 1:
                    time.sleep(delay)
                    delay *= 2

            else:   
                raise RuntimeError(f"Failed to notify evaluator after {max_retry} attempts. Last error: {e}")