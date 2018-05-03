SECRET_KEY = 'secretkeyhere'
FORCE_LANGUAGE = None
DEFAULT_LANGUAGE = 'en'
TITLE = None
MUSIC_DIRS = []
NOW_PLAYING_CACHE_TIME = 60
MODE = 'Vote'
VOTES_THRESHOLD = 3
BLOCK_TIME = 7200
REQUEST_LIMIT = 900
SHOW_CURRENT_PLAYING = True
SONGS_PER_PAGE = 10
PLAYER_TO_USE = 'Clementine'
PLAYERS = {
    'Clementine': {
        'ip': '127.0.0.1',
        'port': 5500,
        'auth_code': None
    },
    'Vlc': {
        'ip': '127.0.0.1',
        'port': 8080,
        'password': ''
    },
    'Mpd': {
        'ip': '127.0.0.1',
        'port': 6600
    }
}
