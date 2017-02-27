import audioplayers


def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


def get_available_audio_players():
    return [(audio_player, getattr(audioplayers, audio_player).name()) for audio_player in audioplayers.__all__]
