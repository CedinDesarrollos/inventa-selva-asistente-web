from flask import Blueprint, render_template, request, jsonify, abort
from ..utils.api import get, post, patch
from ..utils.auth import auth_header
from urllib.parse import quote_plus
from urllib.parse import urlencode
from uuid import uuid4

bp = Blueprint("cases", __name__, template_folder="../templates")


@bp.get("/")
def list_cases():
    token = request.cookies.get("jwt")
    resp = get("/api/cases", headers=auth_header(token))
    data = resp.json()
    return render_template("cases/list.html", items=data.get("items", []))

@bp.get("/<int:case_id>")
def case_detail(case_id: int):
    """
    Renderiza la vista de detalle de un caso:
    - Estado actual
    - Datos de cliente/contacto
    - Historial de eventos
    """
    token = request.cookies.get("jwt")
    headers = auth_header(token) if token else {}

    r = get(f"/api/cases/{case_id}", headers=headers)
    if r.status_code != 200:
        # Si el backend devuelve 404 u otro error, mostramos algo razonable
        try:
            data = r.json()
            msg = data.get("error") or f"backend devolvió {r.status_code}"
        except Exception:
            msg = f"backend devolvió {r.status_code}"
        abort(r.status_code, description=msg)

    data = r.json()
    case = data.get("case") or {}

    return render_template("cases/detail.html", case=case)

@bp.post("/<int:case_id>/state")
def case_change_state(case_id: int):
    """
    Proxy para cambiar el estado del caso desde la web.

    Espera un JSON como:
    {
      "new_state": "PAGADO",
      "actor": "user:alguien@dominio",
      "force": false,
      "payload": {
        "reason": "...",
        "comment": "..."
      }
    }
    """
    token = request.cookies.get("jwt")
    headers = auth_header(token) if token else {}

    payload = request.get_json(force=True) or {}

    r = post(f"/api/cases/{case_id}/state", json=payload, headers=headers)

    # Devolvemos el JSON tal cual para que el JS del frontend decida qué hacer
    try:
        data = r.json()
    except Exception:
        data = {
            "ok": False,
            "error": "backend no devolvió JSON",
            "status_code": r.status_code,
        }

    return jsonify(data), r.status_code

@bp.post("/<int:case_id>/event")
def add_event(case_id):
    token = request.cookies.get("jwt")
    payload = request.get_json(force=True)
    r = post(f"/api/cases/{case_id}/events", json=payload, headers=auth_header(token))
    return jsonify(r.json()), r.status_code

@bp.post("/quote")
def quote():
    token = request.cookies.get("jwt")
    body = request.get_json(force=True) or {}

    kind = (body.pop("kind", "GOODS") or "GOODS").upper()
    path = "/api/quotes/goods" if kind == "GOODS" else "/api/quotes/remit"

    headers = auth_header(token) if token else {}
    r = post(path, json=body, headers=headers)

    # Proxy robusto: intenta parsear JSON; si no, devuelve texto
    try:
        data = r.json()
        # Si el upstream ya devuelve {"ok": true/false, ...} lo respetamos.
        return jsonify(data), r.status_code
    except ValueError:
        # No era JSON (por ej. HTML de error). Log + JSON de fallback.
        print(f"[QUOTE PROXY] Error al parsear JSON desde {path}: status={r.status_code}")
        print(f"[QUOTE PROXY] Body:\n{(r.text or '')[:1000]}")
        return (
            jsonify({
                "ok": False,
                "error": f"Upstream {path} devolvió {r.status_code} no JSON",
                "status_code": r.status_code,
                "raw": (r.text or "")[:500],
            }),
            r.status_code,
        )


@bp.get("/new")
def new_case():
    # Renderiza el asistente paso a paso
    return render_template("cases/create_wizard.html")

@bp.post("/create")
def create_case():
    """
    Adapta el payload del wizard al contrato del backend Railway:
      {
        "case_type": "GOODS" | "REMIT",
        "customer_id": 1,
        "contact_id": 1,
        "title": "...",
        "meta": { ... },
        "fee_override_json": {...}   # opcional
      }
    """
    token = request.cookies.get("jwt")
    src = request.get_json(force=True) or {}

    # ---- 1) Campos base
    case_type   = src.get("case_type", "GOODS")
    customer_id = src.get("customer_id") or 1
    contact_id  = src.get("contact_id")  or 1
    title       = src.get("title")

    # ---- 2) Title fallback si no vino desde el front
    if not title:
        first_desc = (src.get("items") or [{}])[0].get("description", "").strip()
        title = first_desc or f"{case_type} Selva"

    # ---- 3) META: preferir lo que manda el wizard
    meta = src.get("meta")
    fee_override = src.get("fee_override_json")

    if meta is None:
        # ====== MODO LEGACY (para clientes viejos que no envían meta) ======
        items_src = src.get("items") or []
        items_meta = []
        for i, it in enumerate(items_src, start=1):
            desc = (it.get("description") or f"item-{i}").strip()
            qty  = int(it.get("qty") or 1)
            usd  = float(it.get("price_usd") or it.get("cost_usd") or 0)
            sku  = (desc.lower()
                        .replace(" ", "-")
                        .replace("/", "-")
                        .replace("--", "-"))[:60] or f"item-{i}"
            items_meta.append({"sku": sku, "qty": qty, "usd": usd})

        meta = {"items": items_meta}

        # Shipping legacy
        shipping = src.get("shipping") or {}
        ship_amount = float(shipping.get("amount") or 0)
        if ship_amount > 0:
            meta["shipping_usd"] = ship_amount

        # Fee override legacy (si no vino explícito)
        if fee_override is None and src.get("fee_mode") == "NONE":
            fee_override = {"fee_pct": 0, "fee_flat": 0}

    # ---- 4) Construir body final para el backend real
    backend_body = {
        "case_type":   case_type,
        "customer_id": customer_id,
        "contact_id":  contact_id,
        "title":       title,
        "meta":        meta,
    }
    if fee_override is not None:
        backend_body["fee_override_json"] = fee_override

    # ---- 5) Llamada al backend
    headers = auth_header(token) if token else {}
    r = post("/api/cases", json=backend_body, headers=headers)

    # ---- 6) Respuesta robusta (evita 500 si el upstream no retorna JSON)
    try:
        data = r.json()
        return jsonify(data), r.status_code
    except ValueError:
        return (r.text or "", r.status_code, {
            "Content-Type": r.headers.get("Content-Type", "text/plain")
        })


@bp.patch("/<int:case_id>")
def update_case(case_id):
    """
    Proxy para actualizar un caso existente en el backend real.
    Espera un JSON parcial, por ahora al menos: { "meta": { ... } }
    """
    token = request.cookies.get("jwt")
    payload = request.get_json(force=True) or {}

    headers = auth_header(token) if token else {}
    # Reenviamos como PATCH al backend Railway
    r = patch(f"/api/cases/{case_id}", json=payload, headers=headers)

    try:
        data = r.json()
        return jsonify(data), r.status_code
    except ValueError:
        # Respuesta no-JSON (por ejemplo HTML de error)
        return (
            r.text or "",
            r.status_code,
            {"Content-Type": r.headers.get("Content-Type", "text/plain")}
        )

@bp.get("/customer-lookup")
def customer_lookup_proxy():
    """
    Proxy web -> backend API para autocompletar cliente por teléfono.
    Front llama a:  /cases/customer-lookup?phone=+595981514767
    Esto redirige a: /api/customers/lookup?phone=+595981514767
    usando el mismo JWT.
    """
    token = request.cookies.get("jwt")
    raw_phone = (request.args.get("phone") or "").strip()

    if not raw_phone:
        return jsonify({"ok": False, "error": "phone requerido"}), 400

    # Construimos la querystring para el backend real
    qs = urlencode({"phone": raw_phone})
    path = f"/api/customers/lookup?{qs}"

    headers = auth_header(token) if token else {}
    try:
        r = get(path, headers=headers)
    except Exception as e:
        print("[customer_lookup_proxy] Error llamando backend:", e)
        return jsonify({"ok": False, "error": "error backend proxy"}), 500

    try:
        data = r.json()
    except Exception:
        # Backend no devolvió JSON
        print("[customer_lookup_proxy] Respuesta no JSON:", r.status_code, r.text[:500])
        return jsonify({
            "ok": False,
            "error": "backend no devolvió JSON",
            "status_code": r.status_code,
        }), r.status_code

    return jsonify(data), r.status_code

@bp.post("/customer-create")
def customer_create_proxy():
    """
    Crea un customer en el backend real.
    Body esperado: { "name": "...", "phone": "+595981..." , "email"?: "..." }
    """
    token = request.cookies.get("jwt")
    payload = request.get_json(force=True) or {}

    headers = auth_header(token) if token else {}
    r = post("/api/customers", json=payload, headers=headers)

    try:
        data = r.json()
        return jsonify(data), r.status_code
    except Exception:
        return jsonify({
            "ok": False,
            "error": "backend no devolvió JSON",
            "status_code": r.status_code,
        }), r.status_code
    

@bp.post("/<int:case_id>/attachments/presign")
def attachments_presign(case_id: int):
    token = request.cookies.get("jwt")
    headers = auth_header(token) if token else {}

    payload = request.get_json(force=True) or {}
    filename = payload.get("filename") or "file.bin"
    content_type = payload.get("content_type", "application/octet-stream")

    key = f"cases/{case_id}/{uuid4().hex}-{filename}"

    try:
        r = post(
            f"/api/cases/{case_id}/attachments/presign",
            json={"key": key, "content_type": content_type},
            headers=headers,
        )
    except Exception as e:
        print("[proxy presign] error llamando backend:", repr(e))
        return jsonify({
            "ok": False,
            "error": "No se pudo contactar al backend real en /attachments/presign",
        }), 500

    # Logueamos SIEMPRE la respuesta del backend real
    print("[proxy presign] backend status:", r.status_code)
    print("[proxy presign] backend body:", r.text)

    try:
        data = r.json()
    except Exception:
        return jsonify({
            "ok": False,
            "error": "backend no devolvió JSON en presign",
            "status_code": r.status_code,
        }), r.status_code

    if not r.ok or not data.get("upload_url"):
        return jsonify({
            "ok": False,
            "error": data.get("error") or "backend presign sin upload_url",
            "status_code": r.status_code,
        }), r.status_code

    return jsonify({
        "ok": True,
        "upload_url": data["upload_url"],
        "final_key": key,
    }), 200

@bp.post("/<int:case_id>/attachments/commit")
def attachments_commit(case_id: int):
    """
    Proxy web -> backend real para registrar el adjunto.
    Front manda:
      { "key": "<final_key>", "kind"?: "COMPROBANTE", "meta"?: {...} }
    """

    token = request.cookies.get("jwt")
    headers = auth_header(token) if token else {}

    payload = request.get_json(force=True) or {}
    key = payload.get("key")
    if not key:
        return jsonify({"ok": False, "error": "key requerido"}), 400

    kind = payload.get("kind", "COMPROBANTE")
    meta = payload.get("meta")

    r = post(
        f"/api/cases/{case_id}/attachments/commit",
        json={"key": key, "kind": kind, "meta": meta},
        headers=headers,
    )

    try:
        data = r.json()
    except Exception:
        return jsonify({
            "ok": False,
            "error": "backend no devolvió JSON en commit",
            "status_code": r.status_code,
        }), r.status_code

    return jsonify(data), r.status_code