from flask import Blueprint, render_template, request
from collections import defaultdict, OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..utils.api import get
from ..utils.auth import auth_header

bp = Blueprint("dashboard", __name__, template_folder="../templates")

# Caché simple en memoria para nombres de clientes
_CUSTOMER_CACHE: dict[int, str] = {}

def _first_non_empty(*vals):
    for v in vals:
        if v not in (None, "", [], {}):
            return v
    return None

def _fetch_customer_name(cid: int, headers: dict) -> str:
    if cid in _CUSTOMER_CACHE:
        return _CUSTOMER_CACHE[cid]
    try:
        r = get(f"/api/customers/{cid}", headers=headers)
        print(f"[CUSTOMER FETCH] {cid} -> {r.status_code} {r.text}")  # 👈 agrega esto
        if getattr(r, "ok", False):
            data = r.json() or {}
            name = _first_non_empty(data.get("name"), f"Cliente #{cid}")
        else:
            name = f"Cliente #{cid}"
    except Exception as e:
        print(f"[CUSTOMER ERROR] {cid} -> {e}")
        name = f"Cliente #{cid}"
    _CUSTOMER_CACHE[cid] = name
    return name


@bp.get("/")
def index():
    token = request.cookies.get("jwt")
    headers = auth_header(token)

    # 1) Casos
    r_cases = get("/api/cases", headers=headers)
    cases_raw = (r_cases.json() or {}).get("items", []) if getattr(r_cases, "ok", False) else []
    print(f"Cases Raw: {cases_raw}")

    # 2) SLA
    r_sla = get("/api/cases/sla-breaches", headers=headers)
    sla_breaches = (r_sla.json() or {}).get("items", []) if getattr(r_sla, "ok", False) else []
    print(f"SLA Breaches: {sla_breaches}")

    # 3) Resolver nombres de clientes (SECUENCIAL, sin threads)
    customer_ids = {c.get("customer_id") for c in cases_raw if c.get("customer_id")}
    customer_map: dict[int, str] = {}

    for cid in customer_ids:
        try:
            r = get(f"/api/customers/{cid}", headers=headers)
            print(f"[CUSTOMER FETCH] {cid} -> {getattr(r, 'status_code', '?')}")
            if getattr(r, "ok", False):
                data = r.json() or {}
                # puede venir plano {"id":..,"name":..} o envuelto {"customer":{...}}
                cust = data.get("customer", data)
                name = _first_non_empty(cust.get("name"), f"Cliente #{cid}")
            else:
                name = f"Cliente #{cid}"
        except Exception as e:
            print(f"[CUSTOMER ERROR] {cid} -> {e}")
            name = f"Cliente #{cid}"
        _CUSTOMER_CACHE[cid] = name
        customer_map[cid] = name

    # 4) Armar KPI y agrupación por tipo
    por_estado = defaultdict(int)
    cases_by_type = defaultdict(list)

    for c in cases_raw:
        case_type = _first_non_empty(c.get("case_type"), c.get("type"), "Otros")
        state = _first_non_empty(c.get("state"), "—")
        title = _first_non_empty(c.get("title"), c.get("code"), f"Caso #{c.get('id')}")
        updated_at = _first_non_empty(c.get("updated_at"), c.get("created_at"), "")
        cid = c.get("customer_id")
        customer_nombre = (
            customer_map.get(cid)
            or ((c.get("customer") or {}).get("name") if isinstance(c.get("customer"), dict) else None)
            or c.get("customer_nombre")
            or (f"Cliente #{cid}" if cid else "—")
        )


        norm = {
            "id": c.get("id"),
            "code": c.get("code"),
            "case_type": case_type,
            "state": state,
            "state_lower": (state or "").lower(),
            "title": title,
            "updated_at": updated_at,
            "customer_nombre": customer_nombre,
        }

        por_estado[state] += 1
        cases_by_type[case_type].append(norm)

    # Ordenar tipos por cantidad
    cases_by_type = OrderedDict(sorted(cases_by_type.items(), key=lambda kv: len(kv[1]), reverse=True))

    return render_template(
        "dashboard/index.html",
        total=len(cases_raw),
        sla=len(sla_breaches),
        por_estado=dict(por_estado),
        cases_by_type=cases_by_type,
    )
