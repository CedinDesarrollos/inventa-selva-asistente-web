from flask import Blueprint, render_template, request, jsonify, abort
from ..utils.api import get, post
from ..utils.auth import auth_header

bp = Blueprint("cases", __name__, template_folder="../templates")

@bp.get("/")
def list_cases():
    token = request.cookies.get("jwt")
    resp = get("/api/cases", headers=auth_header(token))
    data = resp.json()
    return render_template("cases/list.html", items=data.get("items", []))

@bp.get("/<int:case_id>")
def detail(case_id):
    token = request.cookies.get("jwt")
    resp = get(f"/api/cases/{case_id}", headers=auth_header(token))
    data = resp.json()
    print(f"Payload del evento: {data}")
    if not data.get("ok"):
        abort(resp.status_code)
    case = data["case"]
    return render_template("cases/detail.html", c=case)

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
