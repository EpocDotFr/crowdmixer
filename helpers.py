from crowdmixer import app, cache
import audioplayers

__all__ = [
    'chunks',
    'get_current_audio_player_class',
    'get_current_audio_player_instance',
    'get_now_playing_song',
    'parse_duration'
]


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
