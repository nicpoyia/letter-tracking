import os

from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from app.config import config

app = Flask(__name__)
CORS(app, origins="*", supports_credentials=True)
config_name = os.getenv("FLASK_CONFIG") or "default"
app.config.from_object(config[config_name])

db = SQLAlchemy(app)
Migrate(app, db)

from .models import *
from .views import *
