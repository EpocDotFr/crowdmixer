from flask import render_template, g, request, flash, redirect, url_for, session
from flask_babel import _
from crowdmixer import app
from helpers import *
from models import *
from forms import *


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
