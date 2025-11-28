# app/blueprints/chat.py
from flask import Blueprint, render_template, request, jsonify
from ..utils.api import post
from ..utils.auth import auth_header

bp = Blueprint("chat", __name__, template_folder="../templates")


@bp.get("/")
def chat_home():
    """
    Página principal del chat con Viki.
    """
    # En el futuro puedes sacar el username real del JWT o de la sesión.
    username = request.cookies.get("username") or "Usuario Web"
    return render_template("chat/index.html", username=username)


@bp.post("/api/send")
def chat_send():
    """
    Proxy web → backend real (/api/assistant/chat) para hablar con Viki.
    """
    token = request.cookies.get("jwt")
    payload = request.get_json(force=True) or {}

    text = (payload.get("text") or "").strip()
    if not text:
        return jsonify({"ok": False, "error": "Texto vacío"}), 400

    username = payload.get("username") or "Usuario Web"
    external_id = payload.get("external_id") or f"WEB-{username}"

    # 🔹 Este body es el que espera el backend en /api/assistant/chat
    body = {
        "text": text,
        "username": username,
        "external_id": external_id,
        "identity_id": payload.get("identity_id"),
        "identity_rol": payload.get("identity_rol"),
        "attachments_raw": payload.get("attachments_raw"),
        "has_voice": False,
        "channel": payload.get("channel") or "WEB_CHAT",
    }

    headers = auth_header(token) if token else {}

    # 🔹 Llamamos al nuevo endpoint del backend
    r = post("/api/assistant/chat", json=body, headers=headers)

    raw_text = r.text

    # Intentamos parsear JSON del backend
    try:
        data = r.json()
    except Exception:
        # El backend devolvió HTML o texto plano
        return jsonify({
            "ok": False,
            "error": f"Backend devolvió {r.status_code} sin JSON",
            "backend_status": r.status_code,
            "backend_text": raw_text[:500],
        }), r.status_code

    # A partir de acá, SIEMPRE devolvemos 200 al front
    # y dejamos el detalle del error en el JSON.
    if not data.get("ok"):
        return jsonify({
            "ok": False,
            "error": data.get("error") or "Error en backend assistant/chat",
            "backend_status": r.status_code,
            "backend_raw": data,
        }), 200  # 👈 importante: ya no 400

    return jsonify({
        "ok": True,
        "reply_text": data.get("reply_text"),
        "reply_voice": data.get("reply_voice"),
        "audio_filename": data.get("audio_filename"),
        "media_url": data.get("media_url"),
        "backend_status": r.status_code,
        "backend_raw": data.get("raw"),  # por si querés debugear
    }), 200
