SECRET_KEY = 'secretkeyhere'
DEBUG = False
LOGGER_HANDLER_POLICY = 'production'
FORCE_LANGUAGE = None
DEFAULT_LANGUAGE = 'en'
MUSIC_DIRS = []
NOW_PLAYING_CACHE_TIME = 60
MODE = 'Immediate'
VOTES_THRESHOLD = 3
BLOCK_TIME = 7200
REQUEST_LIMIT = 900
SHOW_CURRENT_PLAYING = True
PLAYER_TO_USE = 'Vlc'
PLAYERS = {
    'Clementine': {
        'ip': '127.0.0.1',
        'port': 5500,
        'auth_code': None
    },
    'Vlc': {
        'ip': '127.0.0.1',
        'port': 8080,
        'username': '',
        'password': ''
    }
}
