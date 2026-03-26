import requests
import json

base_url = "http://localhost:8000/api/v1/meetings"

try:
    # 1. Check meeting details
    resp = requests.get(f"{base_url}/15")
    if resp.ok:
        print("Meeting 15 Details:")
        print(json.dumps(resp.json(), indent=2))
    
    # 2. Check active sessions
    resp = requests.get(f"{base_url}/agent/status")
    if resp.ok:
        print("\nActive Sessions:")
        print(json.dumps(resp.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
