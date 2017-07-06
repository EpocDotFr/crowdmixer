import subprocess
import os
import socket
import struct
import logging

# Optional modules/packages
try:
    import requests
except ImportError:
    pass

try:
    import pyaimp
except ImportError:
    pass

try:
    import musicpd
except ImportError:
    pass

try:
    import appscript
except ImportError:
    pass

try:
    import clementine_protobuf
except ImportError:
    pass

__all__ = [
    'Aimp',
    'Audacious',
    'Clementine',
    'Foobar2000',
    'Itunes',
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

    def _run_process(self, args, get_output=False):
        if get_output:
            return subprocess.run(args, check=True, stdout=subprocess.PIPE, universal_newlines=True).stdout.strip()
        else:
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
    """AIMP wrapper for CrowdMixer.

    **Method used to add a song:** CLI
    **Method used to get the currently playing song:** Windows Messages

    **Documentation:** http://www.aimp.ru/index.php?do=download&cat=sdk (inside the ``.chm`` file)
    """
    def __init__(self, *args, **kwargs):
        super(Aimp, self).__init__(*args, **kwargs)

        self.client = pyaimp.Client()

    @staticmethod
    def name():
        return 'AIMP'

    @staticmethod
    def is_now_playing_supported():
        return True

    def get_now_playing(self):
        if self.client.get_playback_state() != pyaimp.PlayBackState.Playing:
            return None

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
    """Audacious wrapper for CrowdMixer.

    **Method used to add a song:** CLI
    **Method used to get the currently playing song:** ?

    **Documentation:** https://www.mankier.com/1/audacious
    """
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
    """Clementine wrapper for CrowdMixer.

    **Method used to add a song:** TCP
    **Method used to get the currently playing song:** TCP

    **Documentation:** https://github.com/clementine-player/Android-Remote/wiki/Developer-Documentation
    """
    def __init__(self, *args, **kwargs):
        super(Clementine, self).__init__(*args, **kwargs)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.config['ip'], self.config['port']))

    def _send_message(self, msg):
        if self.socket is not None:
            msg.version = 21
            serialized = msg.SerializeToString()
            data = struct.pack('>I', len(serialized)) + serialized

            try:
                self.socket.send(data)
            except Exception as e:
                logging.error(e)
        else:
            logging.error('Socket is closed')

    def _get_response(self, msg_types):
        msgs = []

        while True:
            chunk = self.socket.recv(4)

            if not chunk:
                break

            (msg_length, ) = struct.unpack(">I", chunk)

            data = bytes()

            while len(data) < msg_length:
                chunk = self.socket.recv(min(4096, msg_length - len(data)))

                if not chunk:
                    break

                data += chunk

            if not chunk:
                break

            try:
                msg = clementine_protobuf.Message()
                msg.ParseFromString(data)

                logging.info('Got message {} from Clementine'.format(msg.type))

                if msg.type in msg_types:
                    msgs.append(msg)

                    if len(msgs) == len(msg_types):
                        return msgs
            except Exception as e:
                logging.error(e)

    def _connect(self):
        msg = clementine_protobuf.Message()
        msg.type = clementine_protobuf.CONNECT
        msg.request_connect.auth_code = self.config['auth_code'] if self.config['auth_code'] else 0
        msg.request_connect.send_playlist_songs = False
        msg.request_connect.downloader = False

        self._send_message(msg)

    @staticmethod
    def name():
        return 'Clementine'

    @staticmethod
    def is_now_playing_supported():
        return True

    def get_now_playing(self):
        self._connect()

        info, metainfo = self._get_response([clementine_protobuf.INFO, clementine_protobuf.CURRENT_METAINFO])

        self.socket.close()

        if info.response_clementine_info.state != clementine_protobuf.Playing:
            return None

        return {
            'artist': metainfo.response_current_metadata.song_metadata.artist,
            'title': metainfo.response_current_metadata.song_metadata.title,
            'album': metainfo.response_current_metadata.song_metadata.album,
            'filename': os.path.splitext(os.path.basename(metainfo.response_current_metadata.song_metadata.filename))[0]
        }

    def queue(self, file):
        self._connect()

        _, _ = self._get_response([clementine_protobuf.INFO, clementine_protobuf.CURRENT_METAINFO]) # We don't care about the responses here, so just pull them without doing anything

        msg = clementine_protobuf.Message()
        msg.type = clementine_protobuf.INSERT_URLS
        msg.request_insert_urls.urls.append(file)
        msg.request_insert_urls.play_now = False
        msg.request_insert_urls.enqueue = True

        self._send_message(msg)

        self.socket.close()


class Foobar2000(AudioPlayer):
    """foobar2000 wrapper for CrowdMixer.

    **Method used to add a song:** CLI
    **Method used to get the currently playing song:** ?

    **Documentation:** http://wiki.hydrogenaud.io/index.php?title=Foobar2000:Commandline_Guide
    """
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


class Itunes(AudioPlayer):
    """iTunes wrapper for CrowdMixer.

    **Method used to add a song:** AppleScript
    **Method used to get the currently playing song:** AppleScript

    **Documentation:** http://appscript.sourceforge.net/py-appscript/index.html
    """
    def __init__(self, *args, **kwargs):
        super(Itunes, self).__init__(*args, **kwargs)

        if not self.is_itunes_running():
            raise RuntimeError('iTunes is not running')

        self.itunes = appscript.app('iTunes')

    def is_itunes_running(self):
        return appscript.app('System Events').processes[appscript.its.name == 'iTunes'].count() == 1

    @staticmethod
    def name():
        return 'iTunes'

    @staticmethod
    def is_now_playing_supported():
        return True

    def get_now_playing(self):
        if not self.itunes.player_state.get() == appscript.k.playing:
            return None

        track = self.itunes.current_track.get()

        return {
            'artist': track.artist(),
            'title': track.name(),
            'album': track.album(),
            'filename': track.location().path
        }

    def queue(self, file):
        # self.itunes.enqueue(file)
        pass


class MediaMonkey(AudioPlayer):
    """MediaMonkey wrapper for CrowdMixer.

    **Method used to add a song:** CLI
    **Method used to get the currently playing song:** ?

    **Documentation:** http://www.mediamonkey.com/support/index.php?/Knowledgebase/Article/View/44/2/command-line-startup-options-for-mediamonkey
    """
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
    """MusicBee wrapper for CrowdMixer.

    **Method used to add a song:** CLI
    **Method used to get the currently playing song:** ?

    **Documentation:** http://musicbee.wikia.com/wiki/Command_Line_Parameters
    """
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
    """Music Player Daemon wrapper for CrowdMixer.

    **Method used to add a song:** TCP
    **Method used to get the currently playing song:** TCP

    **Documentation:** https://www.musicpd.org/doc/protocol/
    """
    def __init__(self, *args, **kwargs):
        super(Mpd, self).__init__(*args, **kwargs)

        self.client = musicpd.MPDClient()
        self.client.connect(self.config['ip'], self.config['port'])

    @staticmethod
    def name():
        return 'Music Player Daemon'

    @staticmethod
    def is_now_playing_supported():
        return True

    def get_now_playing(self):
        status = self.client.status()

        if status.state != 'play':
            self.client.disconnect()
            return None

        current_song = self.client.currentsong()

        self.client.disconnect()

        return {
            'artist': current_song.artist,
            'title': current_song.title,
            'album': current_song.album,
            'filename': None
        }

    def queue(self, file):
        self.client.add(file)
        self.client.disconnect()


class Rhythmbox(AudioPlayer):
    """Rhythmbox wrapper for CrowdMixer.

    **Method used to add a song:** CLI
    **Method used to get the currently playing song:** CLI

    **Documentation:** http://manpages.ubuntu.com/manpages/trusty/man1/rhythmbox-client.1.html
    """
    def __init__(self, *args, **kwargs):
        super(Rhythmbox, self).__init__(*args, **kwargs)

        self.exec = 'rhythmbox-client' # TODO Autodetect with psutil?

    @staticmethod
    def name():
        return 'Rhythmbox'

    @staticmethod
    def is_now_playing_supported():
        return True

    def get_now_playing(self):
        # TODO First check the playback status if it is playing

        args = [
            self.exec,
            '--no-start',
            '--no-present',
            '--print-playing',
            '--print-playing-format=%tt==%ta==%at'
        ]

        output = self._run_process(args, get_output=True)

        title, artist, album = output.split('==', maxsplit=2)

        return {
            'artist': artist if artist else None,
            'title': title if title else None,
            'album': album if album else None,
            'filename': None
        }

    def queue(self, file):
        args = [
            self.exec,
            '--no-start',
            '--no-present',
            '--enqueue',
            file
        ]

        self._run_process(args)


class Vlc(AudioPlayer):
    """VLC wrapper for CrowdMixer.

    **Method used to add a song:** HTTP
    **Method used to get the currently playing song:** HTTP

    **Documentation:** https://wiki.videolan.org/VLC_HTTP_requests/
    """
    def __init__(self, *args, **kwargs):
        super(Vlc, self).__init__(*args, **kwargs)

        self.endpoint = 'http://{}:{}/requests/'.format(self.config['ip'], self.config['port'])

    def _query(self, method, resource, params=None):
        url = self.endpoint + resource + '.json'

        response = requests.request(method, url, auth=('', self.config['password']), params=params)

        response.raise_for_status()

        return response.json()

    @staticmethod
    def name():
        return 'VLC'

    @staticmethod
    def is_now_playing_supported():
        return True

    def get_now_playing(self):
        status = self._query('GET', 'status')

        if status['state'] != 'playing':
            return None

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

        self._query('GET', 'status', params=params)


class Winamp(AudioPlayer):
    """Winamp wrapper for CrowdMixer.

    **Method used to add a song:** CLI
    **Method used to get the currently playing song:** ?

    **Documentation:** http://forums.winamp.com/showthread.php?threadid=180297
    """
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
    """XMMS2 wrapper for CrowdMixer.

    **Method used to add a song:** TCP
    **Method used to get the currently playing song:** TCP

    **Documentation:** https://doxygen.xmms2.org/clientlib/stable/xmmsclient-python/xmmsclient.html
    """
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
