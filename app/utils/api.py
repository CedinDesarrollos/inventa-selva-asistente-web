# app/utils/api.py
import requests
from flask import current_app

DEFAULT_TIMEOUT_GET = 30
DEFAULT_TIMEOUT_WRITE = 60

def api_base() -> str:
    base = current_app.config["API_BASE_URL"]
    return base.rstrip("/")

def _request(method: str, path: str, *, params=None, json=None, headers=None, files=None, data=None, timeout=None):
    url = f"{api_base()}{path}"
    # GET usa timeout más corto por defecto, el resto más largo
    if timeout is None:
        timeout = DEFAULT_TIMEOUT_GET if method.upper() == "GET" else DEFAULT_TIMEOUT_WRITE
    return requests.request(
        method=method.upper(),
        url=url,
        params=params,
        json=json,
        headers=headers or {},
        files=files,
        data=data,
        timeout=timeout
    )

def get(path: str, params=None, headers=None):
    return _request("GET", path, params=params, headers=headers)

def post(path: str, json=None, headers=None, files=None, data=None, method: str = "POST"):
    # Conserva compatibilidad con tu firma anterior.
    return _request(method, path, json=json, headers=headers, files=files, data=data)

def put(path: str, json=None, headers=None):
    return _request("PUT", path, json=json, headers=headers)

def delete(path: str, headers=None):
    return _request("DELETE", path, headers=headers)

def patch(path: str, json=None, headers=None):
    return _request("PATCH", path, json=json, headers=headers)
