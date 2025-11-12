# app/web/config_bp.py
from flask import Blueprint, render_template, request, jsonify
from ..utils.api import get, put, post, delete
from ..utils.auth import auth_header

bp = Blueprint("config", __name__, url_prefix="/config", template_folder="../templates")

# ===============================
# Página principal
# ===============================
@bp.get("/")
def config_index():
    # Renderiza la SPA de Config (JS hará llamadas a /config/api/*)
    return render_template("config/index.html")

def _h():
    token = request.cookies.get("jwt")
    return auth_header(token)

# ===============================
# Proxies API (web → backend real)
# ===============================
# SLA
@bp.get("/api/sla")
def web_get_sla():
    r = get("/api/config/sla", headers=_h())
    print(f"/api/sla = {r.text}")
    return (r.text, r.status_code, {"Content-Type": r.headers.get("Content-Type","application/json")})

@bp.put("/api/sla")
def web_put_sla():
    payload = request.get_json(force=True)
    r = put("/api/config/sla", json=payload, headers=_h())
    return (r.text, r.status_code, {"Content-Type": r.headers.get("Content-Type","application/json")})

# Ventana de notificación
@bp.get("/api/notification-window")
def web_get_window():
    r = get("/api/config/notification-window", headers=_h())
    print(f"/api/notification-window = {r.text}")
    return (r.text, r.status_code, {"Content-Type": r.headers.get("Content-Type","application/json")})

@bp.put("/api/notification-window")
def web_put_window():
    payload = request.get_json(force=True)
    r = put("/api/config/notification-window", json=payload, headers=_h())
    return (r.text, r.status_code, {"Content-Type": r.headers.get("Content-Type","application/json")})

# Feature Flags
@bp.get("/api/flags")
def web_get_flags():
    r = get("/api/config/flags", headers=_h())
    print(f"/api/flags = {r.text}")
    return (r.text, r.status_code, {"Content-Type": r.headers.get("Content-Type","application/json")})

@bp.put("/api/flags")
def web_put_flags():
    payload = request.get_json(force=True)
    r = put("/api/config/flags", json=payload, headers=_h())
    return (r.text, r.status_code, {"Content-Type": r.headers.get("Content-Type","application/json")})

# Pricing
@bp.get("/api/pricing")
def web_get_pricing():
    r = get("/api/config/pricing", headers=_h())
    print(f"/api/pricing = {r.text}")
    return (r.text, r.status_code, {"Content-Type": r.headers.get("Content-Type","application/json")})

@bp.put("/api/pricing/<case_type>")
def web_put_pricing(case_type: str):
    payload = request.get_json(force=True)
    r = put(f"/api/config/pricing/{case_type}", json=payload, headers=_h())
    return (r.text, r.status_code, {"Content-Type": r.headers.get("Content-Type","application/json")})

# FX
@bp.get("/api/fx")
def web_get_fx():
    r = get("/api/config/fx", headers=_h())
    print(f"/api/fx = {r.text}")
    return (r.text, r.status_code, {"Content-Type": r.headers.get("Content-Type","application/json")})

@bp.post("/api/fx")
def web_post_fx():
    payload = request.get_json(force=True)
    r = post("/api/config/fx", json=payload, headers=_h())
    return (r.text, r.status_code, {"Content-Type": r.headers.get("Content-Type","application/json")})

@bp.delete("/api/fx/<int:fx_id>")
def web_delete_fx(fx_id: int):
    r = delete(f"/api/config/fx/{fx_id}", headers=_h())
    return (r.text, r.status_code, {"Content-Type": r.headers.get("Content-Type","application/json")})

# Settings (listado, get/put por key, bulk)
@bp.get("/api/settings")
def web_settings_list():
    r = get("/api/config/settings", headers=_h())
    print(f"/api/settings = {r.text}")
    return (r.text, r.status_code, {"Content-Type": r.headers.get("Content-Type","application/json")})

@bp.get("/api/settings/<key>")
def web_settings_get(key):
    r = get(f"/api/config/settings/{key}", headers=_h())
    return (r.text, r.status_code, {"Content-Type": r.headers.get("Content-Type","application/json")})

@bp.put("/api/settings/<key>")
def web_settings_put(key):
    payload = request.get_json(force=True)
    r = put(f"/api/config/settings/{key}", json=payload, headers=_h())
    return (r.text, r.status_code, {"Content-Type": r.headers.get("Content-Type","application/json")})

@bp.put("/api/settings-bulk")
def web_settings_bulk():
    payload = request.get_json(force=True)
    r = put("/api/config/settings-bulk", json=payload, headers=_h())
    return (r.text, r.status_code, {"Content-Type": r.headers.get("Content-Type","application/json")})
