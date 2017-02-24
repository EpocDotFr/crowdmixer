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
        import pyaimp

        client = pyaimp.Client()

        client.add_files_to_playlist(file)
