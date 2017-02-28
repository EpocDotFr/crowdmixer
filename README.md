# CrowdMixer

Let the crowd make its own mix without hassling you.

## Supported audio file formats

CrowdMixer maintain its own music library database. The following audio file formats are supported by the CrowdMixer music
indexer:

  - `.mp3`, `.m4a`
  - `.ogg`, `.oga`, `.opus`
  - `.flac`
  - `.wma`
  - `.wav`

## Supported audio players

CrowdMixer requires to be ran on the same computer that is running your prefered audio player.

Some audio players - which may or may not be listed below - support being controlled remotely, but CrowdMixer doesn't
support this feature yet.

The method used to control an audio player from CrowdMixer is choosed regarding three criteria:

  1. **Simplicity of implementation:** CLI is easier than everything, HTTP is easier than raw TCP, etc.
  2. **Cross-platformness:** CLI is fully cross-platform, dbus is only supported on Linux-based operating systems, etc. This criteria depends of course of the operating system availability of the audio player.
  3. **As native as possible**: Doesn't require installation of a third-party software like a plugin, etc.

| Name | Windows | Linux | Mac OS | Method used |
|------|---------|-------|--------|-------------|
| [AIMP](https://www.aimp.ru/) | ✅ | ❌ | ❌ | [CLI](http://www.aimp.ru/index.php?do=download&cat=sdk) |
| [Audacious](http://audacious-media-player.org/) | ✅ | ✅ | ❌ | [CLI](https://www.mankier.com/1/audacious) |
| [Clementine](https://www.clementine-player.org/) | ✅ | ✅ | ✅ | [CLI](https://github.com/clementine-player/Clementine/issues/4030#issuecomment-30595412) |
| [foobar2000](http://www.foobar2000.org/) | ✅ | ❌ | ❌ | [CLI](http://wiki.hydrogenaud.io/index.php?title=Foobar2000:Commandline_Guide) |
| [MediaMonkey](http://www.mediamonkey.com/) | ✅ | ❌ | ❌ | [CLI](http://www.mediamonkey.com/support/index.php?/Knowledgebase/Article/View/44/2/command-line-startup-options-for-mediamonkey) |
| [MusicBee](http://getmusicbee.com/) | ✅ | ❌ | ❌ | [CLI](http://musicbee.wikia.com/wiki/Command_Line_Parameters) |
| [Rhythmbox](https://wiki.gnome.org/Apps/Rhythmbox) | ❌ | ✅ | ❌ | [CLI](http://manpages.ubuntu.com/manpages/trusty/man1/rhythmbox-client.1.html) |
| [VLC](http://www.videolan.org/vlc/) | ✅ | ✅ | ✅ | [CLI](https://wiki.videolan.org/VLC_command-line_help/) |
| [Winamp](http://www.winamp.com/) | ✅ | ❌ | ✅ | [CLI](http://forums.winamp.com/showthread.php?threadid=180297) |
