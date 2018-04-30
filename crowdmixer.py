from logging.handlers import RotatingFileHandler
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from flask_babel import Babel
from flask import Flask
import logging
import arrow


# -----------------------------------------------------------
# Boot


app = Flask(__name__, static_url_path='')
app.config.from_pyfile('config.py')

if not app.config['TITLE']:
    app.config['TITLE'] = 'CrowdMixer'

app.config['CACHE_TYPE'] = 'filesystem'
app.config['CACHE_DIR'] = 'storage/cache'
app.config['CACHE_THRESHOLD'] = 200
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///storage/data/db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_I18N_ENABLED'] = True

app.config['LANGUAGES'] = {
    'en': 'English',
    'fr': 'Français'
}

app.config['SUPPORTED_AUDIO_FORMATS'] = [
    'mp3', 'm4a',
    'ogg', 'oga', 'opus',
    'flac',
    'wma',
    'wav'
]

db = SQLAlchemy(app)
babel = Babel(app)
cache = Cache(app)

handler = RotatingFileHandler('storage/logs/errors.log', maxBytes=10000000, backupCount=2)
handler.setLevel(logging.WARNING)
formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
handler.setFormatter(formatter)
app.logger.addHandler(handler)

app.jinja_env.globals.update(arrow=arrow)

# -----------------------------------------------------------
# After-init imports


import routes
import models
import commands
import hooks
