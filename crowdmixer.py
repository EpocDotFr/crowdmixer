from flask import Flask, render_template, make_response, g, request, flash, redirect, url_for, session
from wtforms import StringField, SelectField
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from sqlalchemy_utils import ArrowType
from sqlalchemy import or_
from flask_babel import Babel, _, lazy_gettext as __
from flask_wtf import FlaskForm
from werkzeug.exceptions import HTTPException
from tinytag import TinyTag
from glob import glob
from datetime import timedelta
from time import time
import wtforms.validators as validators
import logging
import sys
import arrow
import os
import audioplayers
import click


# -----------------------------------------------------------
# Boot


app = Flask(__name__, static_url_path='')
app.config.from_pyfile('config.py')

app.config['CACHE_TYPE'] = 'filesystem'
app.config['CACHE_DIR'] = 'storage/cache'
app.config['CACHE_THRESHOLD'] = 100
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
    search_form = SearchForm(formdata=request.args, meta={'csrf': False})

    search_term = search_form.q.default
    where = search_form.w.default

    if search_form.validate():
        search_term = search_form.q.data
        where = search_form.w.data

    songs_paginated = Song.query.search_paginated(
        search_term=search_term,
        where=where,
        order_by_votes=app.config['MODE'] == 'Vote',
        page=request.args.get('p', default=1, type=int)
    )

    now_playing = None
    already_submitted_time = None

    if app.config['SHOW_CURRENT_PLAYING'] and get_current_audio_player_class().is_now_playing_supported():
        try:
            now_playing = get_now_playing_song()
        except Exception as e:
            flash(_('Error while getting the now playing song: %(error)s', error=e), 'error')

    if 'already_submitted_time' in session and session['already_submitted_time']:
        already_submitted_time = arrow.get(session['already_submitted_time'])

    return render_template('home.html', songs_paginated=songs_paginated, now_playing=now_playing, already_submitted_time=already_submitted_time, search_form=search_form)


@app.route('/submit/<song_id>')
def submit(song_id):
    song = Song.query.get(song_id)

    already_submitted_time = None
    queue_song = False
    update_db = False

    if 'already_submitted_time' in session and session['already_submitted_time']:
        already_submitted_time = arrow.get(session['already_submitted_time'])

    if not song:
        flash(_('This song doesn\'t exist.'), 'error')
    elif not os.path.isfile(song.path):
        flash(_('This song file doesn\'t seems to exist anymore. Please choose another one.'), 'error')

        try:
            db.session.delete(song)
            db.session.commit()
        except Exception as e:
            flash(_('Error while deleting this song from the database: %(error)s', error=e), 'error')
    elif song.last_queued_at and (arrow.now().timestamp - song.last_queued_at.timestamp) <= app.config['BLOCK_TIME']:
        flash(_('This song has already been queued %(last_queued_at)s. A song can be queued only one time every %(block_time)i minutes.', block_time=app.config['BLOCK_TIME'] / 60, last_queued_at=song.last_queued_at.humanize(locale=g.CURRENT_LOCALE)), 'error')
    elif already_submitted_time and (arrow.now().timestamp - already_submitted_time.timestamp) <= app.config['REQUEST_LIMIT']:
        if app.config['MODE'] == 'Vote':
            action = _('voted for')
            cannot = _('vote more than one time')
        elif app.config['MODE'] == 'Immediate':
            action = _('queued')
            cannot = _('queue more than one')

        flash(_('You already %(action)s a song %(already_submitted_time)s. You cannot %(cannot)s every %(request_limit)i minutes.', action=action, cannot=cannot, request_limit=app.config['REQUEST_LIMIT'] / 60, already_submitted_time=already_submitted_time.humanize(locale=g.CURRENT_LOCALE)), 'error')
    else:
        if app.config['MODE'] == 'Vote':
            song.votes += 1

            if song.votes == app.config['VOTES_THRESHOLD']:
                song.votes = 0

                queue_song = True
            else:
                session['already_submitted_time'] = arrow.now().format()

                if song.artist:
                    from_artist = ' ' + _('from <strong>%(artist)s</strong>', artist=song.artist)
                else:
                    from_artist = ''

                flash(_('Your vote for <strong>%(title)s</strong>%(from_artist)s was successfuly saved! <strong>%(remaining_votes)i</strong> vote(s) is(are) remaining before this song is queued.', title=song.title, from_artist=from_artist, remaining_votes=app.config['VOTES_THRESHOLD'] - song.votes), 'success')

            update_db = True
        elif app.config['MODE'] == 'Immediate':
            queue_song = True

        if queue_song:
            song.total_times_queued += 1
            song.last_queued_at = arrow.now()

            try:
                audio_player = get_current_audio_player_instance()
                audio_player.queue(song.path)

                if song.artist:
                    from_artist = ' ' + _('from <strong>%(artist)s</strong>', artist=song.artist)
                else:
                    from_artist = ''

                flash(_('<strong>%(title)s</strong>%(from_artist)s was successfully queued! It should be played shortly.', title=song.title, from_artist=from_artist), 'success')

                session['already_submitted_time'] = arrow.now().format()

                update_db = True
            except Exception as e:
                flash(_('Error while queuing this song: %(error)s', error=e), 'error')

        if update_db:
            try:
                db.session.add(song)
                db.session.commit()
            except Exception as e:
                flash(_('Error while updating data related to this song: %(error)s', error=e), 'error')

    return redirect(url_for('home', **request.args.to_dict()))


# -----------------------------------------------------------
# Models


class Song(db.Model):
    class SongQuery(db.Query):
        def search_paginated(self, search_term=None, where='a', order_by_votes=False, page=1):
            q = self

            if order_by_votes:
                q = q.order_by(Song.votes.desc())

            q = q.order_by(Song.title.asc())
            q = q.order_by(Song.artist.asc())

            if search_term:
                if where == 'ar':
                    fil = Song.artist.like('%' + search_term + '%')
                elif where == 'al':
                    fil = Song.album.like('%' + search_term + '%')
                elif where == 't':
                    fil = Song.title.like('%' + search_term + '%')
                elif where == 'a':
                    fil = or_(Song.artist.like('%' + search_term + '%'), Song.album.like('%' + search_term + '%'), Song.title.like('%' + search_term + '%'))

                q = q.filter(fil)

            return q.paginate(page=page, per_page=app.config['SONGS_PER_PAGE'])

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
# Forms


class SearchForm(FlaskForm):
    where = [
        ('a', __('All')),
        ('t', __('Title')),
        ('ar', __('Artist')),
        ('al', __('Album'))
    ]

    q = StringField(__('Search term'), [validators.DataRequired()], default=None)
    w = SelectField(__('Where to search'), choices=where, default='a')

# -----------------------------------------------------------
# CLI commands


@app.cli.command()
def create_database():
    """Delete then create all the database tables."""
    db.drop_all()
    db.create_all()


@app.cli.command()
@click.option('--min_duration', default=None, help='Don\'t index songs with a duration greater than this value (format: MM(:SS))')
@click.option('--max_duration', default=None, help='Don\'t index songs with a duration smaller than this value (format: MM(:SS))')
def index(min_duration=None, max_duration=None):
    """Index songs in the configured directories."""
    Song.query.delete()
    db.session.commit()

    music_dirs = app.config['MUSIC_DIRS']
    supported_audio_formats = app.config['SUPPORTED_AUDIO_FORMATS']

    app.logger.info('{} directories configured'.format(len(music_dirs)))

    songs = []

    min_duration = parse_duration(min_duration)
    max_duration = parse_duration(max_duration)

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
            try:
                song_tags = TinyTag.get(song)

                if min_duration and song_tags.duration < min_duration:
                    app.logger.info('Ignoring {} because duration is under the minimal required'.format(song))
                    continue

                if max_duration and song_tags.duration > max_duration:
                    app.logger.info('Ignoring {} because duration is above the maximal allowed'.format(song))
                    continue

                if song_tags.artist and not song_tags.albumartist or song_tags.artist and song_tags.albumartist:
                    artist = song_tags.artist
                elif not song_tags.artist and song_tags.albumartist:
                    artist = song_tags.albumartist
                else:
                    artist = None

                if not song_tags.title:
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
            except Exception as e:
                app.logger.error('{}: {}'.format(song, e))

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


@cache.cached(timeout=app.config['NOW_PLAYING_CACHE_TIME'], key_prefix='now_playing_song')
def get_now_playing_song():
    audio_player = get_current_audio_player_instance()

    return audio_player.get_now_playing()


def parse_duration(duration):
    if not duration:
        return None

    duration = duration.split(':')

    if len(duration) == 1:
        return int(duration[0]) * 60 # Minutes
    elif len(duration) == 2:
        return (int(duration[0]) * 60) + duration[1] # Minutes + seconds
    else:
        return None
