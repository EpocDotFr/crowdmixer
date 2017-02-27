import subprocess

__all__ = [
    'Aimp',
    'Audacious',
    'Clementine',
    'Foobar2000',
    'MediaMonkey',
    'MusicBee',
    'Rhythmbox',
    'Vlc',
    'Winamp'
]


class AudioPlayer:
    name = None

    def _run_process(self, cli):
        subprocess.run(cli, check=True)

    def get_name(self):
        if not self.name:
            raise ValueError('self.name must be defined')

        return self.name

    def queue(self, file):
        raise NotImplementedError('Must be implemented')


class Aimp(AudioPlayer):
    name = 'AIMP'

    def queue(self, file):
        cli = [
            'aimp_path', # TODO Autodetect with psutil?
            '/FILE',
            file
        ]

        self._run_process(cli)


class Audacious(AudioPlayer):
    name = 'Audacious'

    def queue(self, file):
        cli = [
            'audacious_path', # TODO Autodetect with psutil?
            '--enqueue',
            file
        ]

        self._run_process(cli)


class Clementine(AudioPlayer):
    name = 'Clementine'

    def queue(self, file):
        cli = [
            'clementine_path', # TODO Autodetect with psutil?
            '--append',
            file
        ]

        self._run_process(cli)


class Foobar2000(AudioPlayer):
    name = 'foobar2000'

    def queue(self, file):
        cli = [
            'foobar2000_path', # TODO Autodetect with psutil?
            '/immediate',
            '/add',
            file
        ]

        self._run_process(cli)


class MediaMonkey(AudioPlayer):
    name = 'MediaMonkey'

    def queue(self, file):
        cli = [
            'mediamonkey_path', # TODO Autodetect with psutil?
            '/NoSplash',
            '/Add',
            file
        ]

        self._run_process(cli)


class MusicBee(AudioPlayer):
    name = 'MusicBee'

    def queue(self, file):
        cli = [
            'musicbee_path', # TODO Autodetect with psutil?
            '/QueueLast',
            file
        ]

        self._run_process(cli)


class Rhythmbox(AudioPlayer):
    name = 'Rhythmbox'

    def queue(self, file):
        cli = [
            'rhythmbox_client_path', # TODO Autodetect with psutil?
            '--no-start',
            '--enqueue',
            file
        ]

        self._run_process(cli)


class Vlc(AudioPlayer):
    name = 'VLC'

    def queue(self, file):
        cli = [
            'vlc_path', # TODO Autodetect with psutil?
            file
        ]

        self._run_process(cli)


class Winamp(AudioPlayer):
    name = 'Winamp'

    def queue(self, file):
        cli = [
            'winamp_path', # TODO Autodetect with psutil?
            '/ADD',
            file
        ]

        self._run_process(cli)
