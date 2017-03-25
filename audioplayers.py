import subprocess
import os

# Optional modules/packages
try:
    import requests
except ImportError:
    pass

try:
    import pyaimp
except ImportError:
    pass

__all__ = [
    'Aimp',
    'Audacious',
    'Clementine',
    'Foobar2000',
    'MediaMonkey',
    'MusicBee',
    'Mpd',
    'Rhythmbox',
    'Vlc',
    'Winamp',
    'Xmms2'
]


class AudioPlayer:
    def __init__(self, config={}):
        self.config = config

    def _run_process(self, args):
        subprocess.run(args, check=True)

    @staticmethod
    def name():
        raise NotImplementedError('Must be implemented')

    @staticmethod
    def is_now_playing_supported():
        raise NotImplementedError('Must be implemented')

    def get_now_playing(self):
        raise NotImplementedError('Must be implemented')

    def queue(self, file):
        raise NotImplementedError('Must be implemented')


class Aimp(AudioPlayer):
    def __init__(self, *args, **kwargs):
        super(Vlc, self).__init__(*args, **kwargs)

        self.client = pyaimp.Client()

    @staticmethod
    def name():
        return 'AIMP'

    @staticmethod
    def is_now_playing_supported():
        return True

    def get_now_playing(self):
        current_track_info = self.client.get_current_track_info()

        return {
            'artist': current_track_info['artist'],
            'title': current_track_info['title'],
            'album': current_track_info['album'],
            'filename': os.path.splitext(os.path.basename(current_track_info['filename']))[0]
        }

    def queue(self, file):
        self.client.add_to_active_playlist(file)


class Audacious(AudioPlayer):
    @staticmethod
    def name():
        return 'Audacious'

    @staticmethod
    def is_now_playing_supported():
        return False

    def queue(self, file):
        args = [
            'audacious_path', # TODO Autodetect with psutil?
            '--enqueue',
            file
        ]

        self._run_process(args)


class Clementine(AudioPlayer):
    def __init__(self, *args, **kwargs):
        super(Vlc, self).__init__(*args, **kwargs)

        # TODO

    @staticmethod
    def name():
        return 'Clementine'

    @staticmethod
    def is_now_playing_supported():
        return True

    def get_now_playing(self):
        pass # TODO

    def queue(self, file):
        args = [
            'clementine_path', # TODO Autodetect with psutil?
            '--append',
            file
        ]

        self._run_process(args)


class Foobar2000(AudioPlayer):
    @staticmethod
    def name():
        return 'foobar2000'

    @staticmethod
    def is_now_playing_supported():
        return False

    def queue(self, file):
        args = [
            'foobar2000_path', # TODO Autodetect with psutil?
            '/immediate',
            '/add',
            file
        ]

        self._run_process(args)


class MediaMonkey(AudioPlayer):
    @staticmethod
    def name():
        return 'MediaMonkey'

    @staticmethod
    def is_now_playing_supported():
        return False

    def queue(self, file):
        args = [
            'mediamonkey_path', # TODO Autodetect with psutil?
            '/NoSplash',
            '/Add',
            file
        ]

        self._run_process(args)


class MusicBee(AudioPlayer):
    @staticmethod
    def name():
        return 'MusicBee'

    @staticmethod
    def is_now_playing_supported():
        return False

    def queue(self, file):
        args = [
            'musicbee_path', # TODO Autodetect with psutil?
            '/QueueLast',
            file
        ]

        self._run_process(args)


class Mpd(AudioPlayer):
    @staticmethod
    def name():
        return 'Music Player Daemon'

    @staticmethod
    def is_now_playing_supported():
        return True

    def get_now_playing(self):
        pass # TODO

    def queue(self, file):
        args = [
            'mpc_path', # TODO Autodetect with psutil?
            'add',
            file
        ]

        self._run_process(args)


class Rhythmbox(AudioPlayer):
    @staticmethod
    def name():
        return 'Rhythmbox'

    @staticmethod
    def is_now_playing_supported():
        return False

    def queue(self, file):
        args = [
            'rhythmbox_client_path', # TODO Autodetect with psutil?
            '--no-start',
            '--enqueue',
            file
        ]

        self._run_process(args)


class Vlc(AudioPlayer):
    def __init__(self, *args, **kwargs):
        super(Vlc, self).__init__(*args, **kwargs)

        self.endpoint = 'http://{}:{}/requests/'.format(self.config['ip'], self.config['port'])

    def _query(self, method, resource, frmt, params=None):
        url = self.endpoint + resource + '.' + frmt

        response = requests.request(method, url, auth=(self.config['username'], self.config['password']), params=params)

        response.raise_for_status()

        return response.json()

    @staticmethod
    def name():
        return 'VLC'

    @staticmethod
    def is_now_playing_supported():
        return True

    def get_now_playing(self):
        status = self._query('GET', 'status', 'json')

        status = status['information']['category']['meta']

        return {
            'artist': status['artist'] if 'artist' in status else None,
            'title': status['title'] if 'title' in status else None,
            'album': status['album'] if 'album' in status else None,
            'filename': os.path.splitext(os.path.basename(status['filename']))[0] if 'filename' in status else None
        }

    def queue(self, file):
        params = {
            'command': 'in_enqueue',
            'input': file
        }

        self._query('GET', 'status', 'json', params=params)


class Winamp(AudioPlayer):
    @staticmethod
    def name():
        return 'Winamp'

    @staticmethod
    def is_now_playing_supported():
        return False

    def queue(self, file):
        args = [
            'winamp_path', # TODO Autodetect with psutil?
            '/ADD',
            file
        ]

        self._run_process(args)


class Xmms2(AudioPlayer):
    @staticmethod
    def name():
        return 'XMMS2'

    @staticmethod
    def is_now_playing_supported():
        return True

    def get_now_playing(self):
        pass # TODO

    def queue(self, file):
        args = [
            'xmms2_path', # TODO Autodetect with psutil?
            'add',
            '--file',
            file
        ]

        self._run_process(args)
