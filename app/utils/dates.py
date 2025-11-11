from datetime import datetime
import pytz

def utc_to_asuncion(iso_ts: str | None) -> str:
    if not iso_ts:
        return "-"
    # Admite '2025-11-06T12:34:56Z' o '2025-11-06 12:34:56'
    iso_ts = iso_ts.replace("Z", "+00:00")
    dt = datetime.fromisoformat(iso_ts)
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    asu = dt.astimezone(pytz.timezone("America/Asuncion"))
    return asu.strftime("%Y-%m-%d %H:%M")
