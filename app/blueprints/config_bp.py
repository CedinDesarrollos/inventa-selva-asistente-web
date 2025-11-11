from flask import Blueprint, render_template, request, jsonify
from ..utils.api import get, put
from ..utils.auth import auth_header

bp = Blueprint("config", __name__, template_folder="../templates")

@bp.get("/sla")
def get_sla():
    token = request.cookies.get("jwt")
    data = get("/api/config/sla", headers=auth_header(token)).json()
    return render_template("config/sla.html", data=data)

@bp.put("/sla")
def put_sla():
    token = request.cookies.get("jwt")
    payload = request.get_json(force=True)
    r = put("/api/config/sla", json=payload, headers=auth_header(token))
    return jsonify(r.json()), r.status_code

@bp.get("/window")
def get_window():
    token = request.cookies.get("jwt")
    data = get("/api/config/notification-window", headers=auth_header(token)).json()
    return render_template("config/window.html", data=data)

@bp.put("/window")
def put_window():
    token = request.cookies.get("jwt")
    payload = request.get_json(force=True)
    r = put("/api/config/notification-window", json=payload, headers=auth_header(token))
    return jsonify(r.json()), r.status_code

@bp.get("/settings")
def settings_list():
    token = request.cookies.get("jwt")
    r = get("/api/settings", headers=auth_header(token))
    return (r.text, r.status_code, {"Content-Type": r.headers.get("Content-Type","application/json")})

@bp.get("/settings/<key>")
def settings_get(key):
    token = request.cookies.get("jwt")
    r = get(f"/api/config/settings/{key}", headers=auth_header(token))
    return (r.text, r.status_code, {"Content-Type": r.headers.get("Content-Type","application/json")})

@bp.put("/settings/<key>")
def settings_put(key):
    token = request.cookies.get("jwt")
    payload = request.get_json(force=True)
    r = put(f"/api/settings/{key}", json=payload, headers=auth_header(token))
    return (r.text, r.status_code, {"Content-Type": r.headers.get("Content-Type","application/json")})