import subprocess

__all__ = [
    'Aimp'
]


class AudioPlayer:
    name = None

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

        subprocess.run(cli, check=True)


class Clementine(AudioPlayer):
    name = 'Clementine'

    def queue(self, file):
        cli = [
            'clementine_path', # TODO Autodetect with psutil?
            '--append',
            file
        ]

        subprocess.run(cli, check=True)


class Vlc(AudioPlayer):
    name = 'VLC'

    def queue(self, file):
        cli = [
            'vlc_path', # TODO Autodetect with psutil?
            file
        ]

        subprocess.run(cli, check=True)


class Winamp(AudioPlayer):
    name = 'Winamp'

    def queue(self, file):
        cli = [
            'winamp_path', # TODO Autodetect with psutil?
            '/ADD',
            file
        ]

        subprocess.run(cli, check=True)


class Rhythmbox(AudioPlayer):
    name = 'Rhythmbox'

    def queue(self, file):
        cli = [
            'rhythmbox_client_path', # TODO Autodetect with psutil?
            '--no-start',
            '--enqueue',
            file
        ]

        subprocess.run(cli, check=True)


class MusicBee(AudioPlayer):
    name = 'MusicBee'

    def queue(self, file):
        cli = [
            'musicbee_path', # TODO Autodetect with psutil?
            '/QueueLast',
            file
        ]

        subprocess.run(cli, check=True)
