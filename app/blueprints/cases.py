from flask import Blueprint, render_template, request, jsonify
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
    data = get(f"/api/cases/{case_id}", headers=auth_header(token)).json()
    return render_template("cases/detail.html", c=data)

@bp.post("/<int:case_id>/event")
def add_event(case_id):
    token = request.cookies.get("jwt")
    payload = request.get_json(force=True)
    r = post(f"/api/cases/{case_id}/events", json=payload, headers=auth_header(token))
    return jsonify(r.json()), r.status_code

@bp.post("/quote")
def quote():
    token = request.cookies.get("jwt")
    body = request.get_json(force=True)
    kind = body.pop("kind", "goods")
    path = "/api/quotes/goods" if kind.upper() == "GOODS" else "/api/quotes/remit"
    r = post(path, json=body, headers=auth_header(token))
    return jsonify(r.json()), r.status_code

@bp.get("/new")
def new_case():
    # Renderiza el asistente paso a paso
    return render_template("cases/create_wizard.html")

@bp.post("/create")
def create_case():
    """
    Adapta el payload del wizard al contrato del backend Railway:
      {
        "case_type": "GOODS",
        "customer_id": 1,
        "contact_id": 1,
        "title": "iPhone 15 128GB Blue",
        "meta": {
          "items": [{"sku":"iphone15-blue","qty":1,"usd":900}],
          "shipping_usd": 80
        },
        "fee_override_json": {"fee_pct": 0, "fee_flat": 0}   # opcional
      }
    """
    token = request.cookies.get("jwt")
    src = request.get_json(force=True) or {}

    # ---- 1) Campos base
    case_type = src.get("case_type", "GOODS")

    # En tu MVP no tenés un selector real de cliente/contacto.
    # Usa IDs por defecto o permite que vengan del front si los tenés.
    customer_id = src.get("customer_id") or 1
    contact_id  = src.get("contact_id")  or 1

    # ---- 2) Title: del primer ítem o fallback
    title = src.get("title")
    if not title:
        first_desc = (src.get("items") or [{}])[0].get("description", "").strip()
        title = first_desc or f"{case_type} Selva"

    # ---- 3) Meta.items: mapear a {sku, qty, usd}
    items_src = src.get("items") or []
    items_meta = []
    for i, it in enumerate(items_src, start=1):
        desc = (it.get("description") or f"item-{i}").strip()
        qty  = int(it.get("qty") or 1)
        # usd: precio final. Si no hay, usar cost_usd.
        usd  = float(it.get("price_usd") or it.get("cost_usd") or 0)
        # sku: un slug simple; si no querés, podés dejarlo como desc.
        sku  = (desc.lower()
                    .replace(" ", "-")
                    .replace("/", "-")
                    .replace("--", "-"))[:60] or f"item-{i}"
        items_meta.append({"sku": sku, "qty": qty, "usd": usd})

    meta = {"items": items_meta}

    # ---- 4) Shipping (del toggle del paso 1)
    shipping = src.get("shipping") or {}
    ship_amount = float(shipping.get("amount") or 0)
    if ship_amount > 0:
        meta["shipping_usd"] = ship_amount

    # ---- 5) Fee override (solo si modo NONE)
    fee_override = None
    if src.get("fee_mode") == "NONE":
        fee_override = {"fee_pct": 0, "fee_flat": 0}

    backend_body = {
        "case_type": case_type,
        "customer_id": customer_id,
        "contact_id": contact_id,
        "title": title,
        "meta": meta,
    }
    if fee_override is not None:
        backend_body["fee_override_json"] = fee_override

    # ---- 6) Llamada al backend
    headers = auth_header(token) if token else {}
    r = post("/api/cases", json=backend_body, headers=headers)

    # ---- 7) Respuesta robusta (evita 500 si el upstream no retorna JSON)
    try:
        data = r.json()
        return jsonify(data), r.status_code
    except ValueError:
        return (r.text or "", r.status_code, {
            "Content-Type": r.headers.get("Content-Type", "text/plain")
        })