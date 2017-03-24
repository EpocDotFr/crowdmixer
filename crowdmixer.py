from flask import Flask, render_template, make_response, g, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cache import Cache
from sqlalchemy_utils import ArrowType
from sqlalchemy import or_
from flask_babel import Babel, _
from werkzeug.exceptions import HTTPException
from tinytag import TinyTag
from glob import glob
from datetime import timedelta
from time import time
import logging
import sys
import arrow
import os
import audioplayers


# -----------------------------------------------------------
# Boot


app = Flask(__name__, static_url_path='')
app.config.from_pyfile('config.py')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///storage/data/db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['LANGUAGES'] = {
    'en': 'English'
}

app.config['SUPPORTED_AUDIO_FORMATS'] = [
    'mp3', 'm4a',
    'ogg', 'oga', 'opus',
    'flac',
    'wma',
    'wav'
]

app.config['CACHE_TYPE'] = 'filesystem'
app.config['CACHE_DIR'] = 'storage/cache'

app.jinja_env.globals.update(arrow=arrow)

db = SQLAlchemy(app)
babel = Babel(app)
cache = Cache(app)

# Default Python logger
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S',
    stream=sys.stdout
)

logging.getLogger().setLevel(logging.INFO)

# Default Flask loggers
for handler in app.logger.handlers:
    handler.setFormatter(logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d/%m/%Y %H:%M:%S'))


# -----------------------------------------------------------
# Routes


@app.route('/')
def home():
    songs = Song.query.search(search_term=request.args.get('q'), order_by_votes=app.config['MODE'] == 'Vote')

    now_playing = None

    if app.config['SHOW_CURRENT_PLAYING'] and get_current_audio_player_class().is_now_playing_supported():
        try:
            now_playing = get_now_playing_song()
        except Exception as e:
            flash(_('Error while getting the now playing song: {}'.format(e)), 'error')

    return render_template('home.html', songs=songs, now_playing=now_playing)


@app.route('/submit/<song_id>')
def submit(song_id):
    song = Song.query.get(song_id)

    if not song:
        flash(_('This song doesn\'t exist.'), 'error')
    elif not os.path.isfile(song.path):
        flash(_('This song file doesn\'t seem to exist no more. Please choose another one.'), 'error')

        db.session.delete(song)
        db.session.commit()
    else:
        try:
            audio_player = get_current_audio_player_instance()
            audio_player.queue(song.path)

            flash(_('Song successfully queued!'), 'success') # TODO
        except Exception as e:
            flash(_('Error while queuing this song: {}'.format(e)), 'error') # TODO

    return redirect(url_for('home'))


# -----------------------------------------------------------
# Models


class Song(db.Model):
    class SongQuery(db.Query):
        def search(self, search_term=None, order_by_votes=False):
            q = self

            if order_by_votes:
                q = q.order_by(Song.votes.desc())

            q = q.order_by(Song.title.asc())
            q = q.order_by(Song.artist.asc())

            if search_term:
                q = q.filter(or_(Song.title.like('%' + search_term + '%'), Song.artist.like('%' + search_term + '%'), Song.album.like('%' + search_term + '%')))

            return q.all()

    __tablename__ = 'songs'
    query_class = SongQuery

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    title = db.Column(db.String, nullable=False)
    artist = db.Column(db.String, default=None)
    album = db.Column(db.String, default=None)
    path = db.Column(db.String, nullable=False)
    last_queued_at = db.Column(ArrowType, default=None)
    total_times_queued = db.Column(db.Integer, default=0)
    votes = db.Column(db.Integer, default=0)

    def __init__(self, title=None, artist=None, album=None, path=None, last_queued_at=None, total_times_queued=0, votes=0):
        self.title = title
        self.artist = artist
        self.album = album
        self.path = path
        self.last_queued_at = last_queued_at
        self.total_times_queued = total_times_queued
        self.votes = votes

    def __repr__(self):
        return '<Song> #{} : {}'.format(self.id, self.title)


# -----------------------------------------------------------
# CLI commands


@app.cli.command()
def create_database():
    """Delete then create all the database tables."""
    db.drop_all()
    db.create_all()


@app.cli.command()
def index():
    """Index all songs in the configured directories."""
    Song.query.delete()
    db.session.commit()

    music_dirs = app.config['MUSIC_DIRS']
    supported_audio_formats = app.config['SUPPORTED_AUDIO_FORMATS']

    app.logger.info('{} directories configured'.format(len(music_dirs)))

    songs = []

    start = time()

    for music_dir in music_dirs:
        app.logger.info('Scanning ' + music_dir)

        if not os.path.isdir(music_dir):
            app.logger.warning(music_dir + ' isn\'t a directory or doesn\'t exists')
            continue

        for audio_format in supported_audio_formats:
            songs.extend(glob(os.path.join(music_dir, '**', '*.' + audio_format), recursive=True))

    app.logger.info('{} supported audio files detected'.format(len(songs)))

    for songs_chunk in list(chunks(songs, 100)):
        for song in songs_chunk:
            song_tags = TinyTag.get(song)

            if song_tags.artist and not song_tags.albumartist or song_tags.artist and song_tags.albumartist:
                artist = song_tags.artist
            elif song_tags.albumartist and not song_tags.artist:
                artist = song_tags.albumartist
            else:
                artist = None

            if not artist and not song_tags.title:
                title = os.path.splitext(os.path.basename(song))[0]
            else:
                title = song_tags.title

            if not song_tags.album:
                album = None
            else:
                album = song_tags.album

            song_object = Song(
                title=title,
                artist=artist,
                album=album,
                path=song
            )

            app.logger.info('{} - {} ({})'.format(artist, title, album))

            db.session.add(song_object)

        db.session.commit()

    end = time()

    duration = end - start

    app.logger.info('Duration: {}'.format(timedelta(seconds=duration)))


# -----------------------------------------------------------
# Hooks


@app.before_request
def set_locale():
    if not hasattr(g, 'CURRENT_LOCALE'):
        if app.config['FORCE_LANGUAGE']:
            g.CURRENT_LOCALE = app.config['FORCE_LANGUAGE']
        else:
            g.CURRENT_LOCALE = request.accept_languages.best_match(app.config['LANGUAGES'].keys(), default=app.config['DEFAULT_LANGUAGE'])


@babel.localeselector
def get_app_locale():
    if not hasattr(g, 'CURRENT_LOCALE'):
        return app.config['DEFAULT_LANGUAGE']
    else:
        return g.CURRENT_LOCALE


# -----------------------------------------------------------
# HTTP errors handler


@app.errorhandler(401)
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(500)
@app.errorhandler(503)
def http_error_handler(error, without_code=False):
    if isinstance(error, HTTPException):
        error = error.code
    elif not isinstance(error, int):
        error = 500

    body = render_template('errors/{}.html'.format(error))

    if not without_code:
        return make_response(body, error)
    else:
        return make_response(body)


# -----------------------------------------------------------
# Helpers


def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


def get_current_audio_player_class():
    name = app.config['PLAYER_TO_USE']

    if name not in audioplayers.__all__:
        raise ValueError('{} isn\'t a valid audio player name'.format(name))

    return getattr(audioplayers, name)


def get_current_audio_player_instance():
    name = app.config['PLAYER_TO_USE']

    if name not in audioplayers.__all__:
        raise ValueError('{} isn\'t a valid audio player name'.format(name))

    config = {}

    if name in app.config['PLAYERS']:
        config = app.config['PLAYERS'][name]

    return getattr(audioplayers, name)(config)


@cache.cached(timeout=app.config['NOW_PLAYING_CACHE_TIME'])
def get_now_playing_song():
    audio_player = get_current_audio_player_instance()

    return audio_player.get_now_playing()
