import os
from flask import Flask
from .config import AppConfig

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(AppConfig)

    # Blueprints
    from .blueprints.dashboard import bp as dashboard_bp
    from .blueprints.cases import bp as cases_bp
    from .blueprints.sla import bp as sla_bp
    from .blueprints.config_bp import bp as config_bp

    app.register_blueprint(dashboard_bp, url_prefix="/")
    app.register_blueprint(cases_bp, url_prefix="/cases")
    app.register_blueprint(sla_bp, url_prefix="/sla")
    app.register_blueprint(config_bp, url_prefix="/config")

    return app
