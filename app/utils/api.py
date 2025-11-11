import os, requests
from flask import current_app

def api_base() -> str:
    return current_app.config["API_BASE_URL"].rstrip("/")

def get(path: str, params=None, headers=None):
    url = f"{api_base()}{path}"
    return requests.get(url, params=params, headers=headers or {}, timeout=30)

def post(path: str, json=None, headers=None, files=None, data=None, method="POST"):
    url = f"{api_base()}{path}"
    fn = requests.post if method == "POST" else requests.put
    return fn(url, json=json, headers=headers or {}, files=files, data=data, timeout=60)

def put(path: str, json=None, headers=None):
    url = f"{api_base()}{path}"
    return requests.put(url, json=json, headers=headers or {}, timeout=60)
