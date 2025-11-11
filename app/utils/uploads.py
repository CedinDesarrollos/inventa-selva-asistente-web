import requests
from .api import post
from .auth import auth_header

def presign_attachment(case_id: int, filename: str, content_type: str, token: str):
    r = post(f"/api/cases/{case_id}/attachments/presign",
             json={"filename": filename, "content_type": content_type},
             headers=auth_header(token))
    r.raise_for_status()
    return r.json()  # { upload_url, final_key, ... }

def upload_binary_to_presigned_url(upload_url: str, blob: bytes, content_type: str):
    rr = requests.put(upload_url, data=blob, headers={"Content-Type": content_type}, timeout=120)
    rr.raise_for_status()

def commit_attachment(case_id: int, final_key: str, token: str):
    r = post(f"/api/cases/{case_id}/attachments/commit",
             json={"key": final_key},
             headers=auth_header(token))
    r.raise_for_status()
    return r.json()
