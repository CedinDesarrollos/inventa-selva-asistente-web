import os
from flask import Flask
from .config import AppConfig

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    @app.template_filter('numfmt')
    def numfmt(value, decimals=0):
        """
        Formatea números con formato latam:
        - 8837.24  -> 8.837,24
        - 705000   -> 705.000
        """
        try:
            n = float(value)
        except (TypeError, ValueError):
            return value

        fmt = f"{{:,.{decimals}f}}"   # 8837.24 -> "8,837.24"
        s = fmt.format(n)
        # Cambiamos a formato 8.837,24
        s = s.replace(",", "X").replace(".", ",").replace("X", ".")
        if decimals == 0:
            # Si pedimos 0 decimales, sacamos la parte decimal
            s = s.split(',')[0]
        return s
    

    app.config.from_object(AppConfig)

    # Blueprints
    from .blueprints.dashboard import bp as dashboard_bp
    from .blueprints.cases import bp as cases_bp
    from .blueprints.sla import bp as sla_bp
    from .blueprints.config_bp import bp as config_bp
    from .blueprints.chat import bp as chat_bp

    app.register_blueprint(dashboard_bp, url_prefix="/")
    app.register_blueprint(cases_bp, url_prefix="/cases")
    app.register_blueprint(sla_bp, url_prefix="/sla")
    app.register_blueprint(config_bp, url_prefix="/config")
    app.register_blueprint(chat_bp, url_prefix="/chat")

    return app
