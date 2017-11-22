from crowdmixer import app, db
from datetime import timedelta
from tinytag import TinyTag
from glob import glob
from time import time
from models import *
import click
import os


@app.cli.command()
def create_database():
    """Delete then create all the database tables."""
    if not click.confirm('Are you sure?'):
        click.secho('Aborted', fg='red')

        return

    click.echo('Dropping everything')

    db.drop_all()

    click.echo('Creating tables')

    db.create_all()

    click.secho('Done', fg='green')


@app.cli.command()
@click.option('--min_duration', default=None, help='Don\'t index songs with a duration greater than this value (format: MM(:SS))')
@click.option('--max_duration', default=None, help='Don\'t index songs with a duration smaller than this value (format: MM(:SS))')
def index(min_duration=None, max_duration=None):
    """Index songs in the configured directories."""
    Song.query.delete()
    db.session.commit()

    music_dirs = app.config['MUSIC_DIRS']
    supported_audio_formats = app.config['SUPPORTED_AUDIO_FORMATS']

    click.echo('{} directories configured'.format(len(music_dirs)))

    songs = []

    min_duration = parse_duration(min_duration)
    max_duration = parse_duration(max_duration)

    start = time()

    for music_dir in music_dirs:
        click.echo('Scanning ' + music_dir)

        if not os.path.isdir(music_dir):
            app.logger.warning(music_dir + ' isn\'t a directory or doesn\'t exists')
            continue

        for audio_format in supported_audio_formats:
            songs.extend(glob(os.path.join(music_dir, '**', '*.' + audio_format), recursive=True))

    click.echo('{} supported audio files detected'.format(len(songs)))

    for songs_chunk in list(chunks(songs, 100)):
        for song in songs_chunk:
            try:
                song_tags = TinyTag.get(song)

                if min_duration and song_tags.duration < min_duration:
                    click.echo('Ignoring {} because duration is under the minimal required'.format(song))

                    continue

                if max_duration and song_tags.duration > max_duration:
                    click.echo('Ignoring {} because duration is above the maximal allowed'.format(song))

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

                click.echo('{} - {} ({})'.format(artist, title, album))

                db.session.add(song_object)
            except Exception as e:
                click.echo('{}: {}'.format(song, e), err=True)

        db.session.commit()

    end = time()

    duration = end - start

    click.secho('Duration: {}'.format(timedelta(seconds=duration)), fg='green')
