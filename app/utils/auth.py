def auth_header(token: str | None):
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}
