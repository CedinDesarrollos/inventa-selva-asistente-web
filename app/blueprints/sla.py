from flask import Blueprint, render_template, request, jsonify
from ..utils.api import get, post
from ..utils.auth import auth_header

bp = Blueprint("sla", __name__, template_folder="../templates")

@bp.get("/")
def list_breaches():
    token = request.cookies.get("jwt")
    data = get("/api/cases/sla-breaches", headers=auth_header(token)).json()
    return render_template("sla/list.html", items=data.get("items", []))

@bp.post("/notify")
def simulate_notify():
    token = request.cookies.get("jwt")
    r = post("/api/wa/notify", json={"simulate": True}, headers=auth_header(token))
    return jsonify(r.json()), r.status_code
