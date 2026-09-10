from app.routes.shops import shops_bp
from app.routes.clients import clients_bp
from app.routes.loans import loans_bp
from app.routes.hq import hq_bp
from app.routes.inventory import inventory_bp
from app.routes.reports import reports_bp
from app.routes.admin import admin_bp


def register_blueprints(app):
    app.register_blueprint(shops_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(loans_bp)
    app.register_blueprint(hq_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)
