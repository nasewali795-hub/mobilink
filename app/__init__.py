import os
from flask import Flask
from app.config import SECRET_KEY
from app.routes import register_blueprints
from app.state import seed_sample_data


_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def create_app():
    application = Flask(__name__, template_folder=os.path.join(_ROOT, 'templates'), static_folder=os.path.join(_ROOT, 'static'))
    application.config['SECRET_KEY'] = SECRET_KEY
    register_blueprints(application)
    return application


app = create_app()
