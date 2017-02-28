import subprocess

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
    def _run_process(self, cli):
        subprocess.run(cli, check=True)

    @staticmethod
    def name():
        raise NotImplementedError('Must be implemented')

    def queue(self, file):
        raise NotImplementedError('Must be implemented')


class Aimp(AudioPlayer):
    @staticmethod
    def name():
        return 'AIMP'

    def queue(self, file):
        cli = [
            'aimp_path', # TODO Autodetect with psutil?
            '/FILE',
            file
        ]

        self._run_process(cli)


class Audacious(AudioPlayer):
    @staticmethod
    def name():
        return 'Audacious'

    def queue(self, file):
        cli = [
            'audacious_path', # TODO Autodetect with psutil?
            '--enqueue',
            file
        ]

        self._run_process(cli)


class Clementine(AudioPlayer):
    @staticmethod
    def name():
        return 'Clementine'

    def queue(self, file):
        cli = [
            'clementine_path', # TODO Autodetect with psutil?
            '--append',
            file
        ]

        self._run_process(cli)


class Foobar2000(AudioPlayer):
    @staticmethod
    def name():
        return 'foobar2000'

    def queue(self, file):
        cli = [
            'foobar2000_path', # TODO Autodetect with psutil?
            '/immediate',
            '/add',
            file
        ]

        self._run_process(cli)


class MediaMonkey(AudioPlayer):
    @staticmethod
    def name():
        return 'MediaMonkey'

    def queue(self, file):
        cli = [
            'mediamonkey_path', # TODO Autodetect with psutil?
            '/NoSplash',
            '/Add',
            file
        ]

        self._run_process(cli)


class MusicBee(AudioPlayer):
    @staticmethod
    def name():
        return 'MusicBee'

    def queue(self, file):
        cli = [
            'musicbee_path', # TODO Autodetect with psutil?
            '/QueueLast',
            file
        ]

        self._run_process(cli)


class Mpd(AudioPlayer):
    @staticmethod
    def name():
        return 'Music Player Daemon'

    def queue(self, file):
        cli = [
            'mpc_path', # TODO Autodetect with psutil?
            'add',
            file
        ]

        self._run_process(cli)


class Rhythmbox(AudioPlayer):
    @staticmethod
    def name():
        return 'Rhythmbox'

    def queue(self, file):
        cli = [
            'rhythmbox_client_path', # TODO Autodetect with psutil?
            '--no-start',
            '--enqueue',
            file
        ]

        self._run_process(cli)


class Vlc(AudioPlayer):
    @staticmethod
    def name():
        return 'VLC'

    def queue(self, file):
        cli = [
            'vlc_path', # TODO Autodetect with psutil?
            file
        ]

        self._run_process(cli)


class Winamp(AudioPlayer):
    @staticmethod
    def name():
        return 'Winamp'

    def queue(self, file):
        cli = [
            'winamp_path', # TODO Autodetect with psutil?
            '/ADD',
            file
        ]

        self._run_process(cli)


class Xmms2(AudioPlayer):
    @staticmethod
    def name():
        return 'XMMS2'

    def queue(self, file):
        cli = [
            'xmms2_path', # TODO Autodetect with psutil?
            'add',
            '--file',
            file
        ]

        self._run_process(cli)
