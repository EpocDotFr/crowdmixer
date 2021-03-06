from flask_babel import _
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
    import clementine_protobuf
except ImportError:
    pass

try:
    import psutil
except ImportError:
    pass

try:
    import xmmsclient
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

    def _run_process(self, args, get_output=False):
        if get_output:
            return subprocess.run(args, check=True, stdout=subprocess.PIPE, universal_newlines=True).stdout.strip()
        else:
            subprocess.run(args, check=True)

    def _get_executable_path(self, proc_name):
        path = None

        for proc in psutil.process_iter():
            try:
                if proc_name in proc.name():
                    path = proc.exe()
                    break
            except psutil.NoSuchProcess:
                pass

        if not path:
            raise Exception(_('%(name)s doesn\'t seems to be running.', name=self.name()))

        return path

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
        audacious_path = self._get_executable_path('audacious')

        args = [
            audacious_path,
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
        foobar2000_path = self._get_executable_path('foobar2000')

        args = [
            foobar2000_path,
            '/immediate',
            '/add',
            file
        ]

        self._run_process(args)


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
        mediamonkey_path = self._get_executable_path('MediaMonkey')

        args = [
            mediamonkey_path,
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
        musicbee_path = self._get_executable_path('MusicBee')

        args = [
            musicbee_path,
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

    **Documentation:** http://manpages.ubuntu.com/manpages/zesty/en/man1/rhythmbox-client.1.html
    """
    def __init__(self, *args, **kwargs):
        super(Rhythmbox, self).__init__(*args, **kwargs)

        self.common_args = [
            'rhythmbox-client'
            '--no-start',
            '--no-present'
        ]

    @staticmethod
    def name():
        return 'Rhythmbox'

    @staticmethod
    def is_now_playing_supported():
        return True

    def get_now_playing(self):
        playing_format_sep = '=='

        playing_format = playing_format_sep.join(['%tt', '%ta', '%at'])

        args = self.common_args.extend([
            '--print-playing',
            '--print-playing-format=' + playing_format
        ])

        output = self._run_process(args, get_output=True)

        if not output.replace(playing_format_sep, ''): # Nothing is playing
            return None

        title, artist, album = output.split(playing_format_sep, maxsplit=2)

        return {
            'artist': artist if artist else None,
            'title': title if title else None,
            'album': album if album else None,
            'filename': None
        }

    def queue(self, file):
        args = self.common_args.extend([
            '--enqueue',
            file
        ])

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

        response = requests.request(method, url, auth=('', self.config['password']), params=params, timeout=2)

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
        winamp_path = self._get_executable_path('winamp')

        args = [
            winamp_path,
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
    def __init__(self, *args, **kwargs):
        super(Xmms2, self).__init__(*args, **kwargs)

        self.client = xmmsclient.XMMS('crowdmixer')
        self.client.connect(os.getenv('XMMS_PATH'))

    def _get_result(self, result):
        result.wait()

        if result.iserror():
            self.client.quit()
            raise Exception(result.get_error())

        return result.value()

    @staticmethod
    def name():
        return 'XMMS2'

    @staticmethod
    def is_now_playing_supported():
        return True

    def get_now_playing(self):
        current_song_id = self._get_result(self.client.playback_current_id())

        if current_song_id == 0: # Nothing is playing
            self.client.quit()
            return None

        current_song = self._get_result(self.client.medialib_get_info(current_song_id))

        self.client.quit()

        return {
            'artist': current_song['artist'] if 'artist' in current_song else None,
            'title': current_song['title'] if 'title' in current_song else None,
            'album': current_song['album'] if 'album' in current_song else None,
            'filename': os.path.splitext(os.path.basename(current_song['url']))[0] if 'url' in current_song else None
        }

    def queue(self, file):
        self._get_result(self.client.playlist_add_url(file))

        self.client.quit()
