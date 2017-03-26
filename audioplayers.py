import subprocess
import os
import socket
import clementine_protobuf
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
                        self.socket.close()
                        return msgs
            except Exception as e:
                logging.error(e)

    @staticmethod
    def name():
        return 'Clementine'

    @staticmethod
    def is_now_playing_supported():
        return True

    def get_now_playing(self):
        msg = clementine_protobuf.Message()
        msg.type = clementine_protobuf.CONNECT
        msg.request_connect.auth_code = self.config['auth_code'] if self.config['auth_code'] else 0
        msg.request_connect.send_playlist_songs = False
        msg.request_connect.downloader = False

        self._send_message(msg)

        info, metainfo = self._get_response([clementine_protobuf.INFO, clementine_protobuf.CURRENT_METAINFO])

        if info.response_clementine_info.state != clementine_protobuf.Playing:
            return None

        return {
            'artist': metainfo.response_current_metadata.song_metadata.artist,
            'title': metainfo.response_current_metadata.song_metadata.title,
            'album': metainfo.response_current_metadata.song_metadata.album,
            'filename': os.path.splitext(os.path.basename(metainfo.response_current_metadata.song_metadata.filename))[0]
        }

    def queue(self, file):
        msg = clementine_protobuf.Message()
        msg.type = clementine_protobuf.INSERT_URLS
        msg.request_insert_urls.urls.append(file)
        msg.request_insert_urls.play_now = False
        msg.request_insert_urls.enqueue = True

        self._send_message(msg)
        self.socket.close()
        # FIXME Clementine crashes when sending it this message

        # msg = self._get_response(clementine_protobuf.CURRENT_METAINFO)


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
