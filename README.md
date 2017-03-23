# CrowdMixer

Let the crowd make its own mix without hassling you.

> TODO Screenshot

## Features

> TODO

## Prerequisites

  - Should work on any Python 3.x version. Feel free to test with another Python version and give me feedback
  - A [uWSGI](https://uwsgi-docs.readthedocs.io/en/latest/)-capable web server (optional, but recommended)

## Installation

  1. Clone this repo somewhere
  2. `pip install -r requirements.txt`
  3. `export FLASK_APP=crowdmixer.py` (Windows users: `set FLASK_APP=crowdmixer.py`)
  4. `flask create_database` (WARNING: don't re-run this command unless you want to start from scratch, it will wipe out all the data)
  5. `flask index` (this will index your songs, don't forget to set the `MUSIC_DIRS` configuration parameter before, read below)

## Configuration

Copy the `config.example.py` file to `config.py` and fill in the configuration parameters.

Available configuration parameters are:

  - `SECRET_KEY` Set this to a complex random value
  - `DEBUG` Enable/disable debug mode
  - `LOGGER_HANDLER_POLICY` Policy of the default logging handler

More informations on the three above can be found [here](http://flask.pocoo.org/docs/0.12/config/#builtin-configuration-values).

  - `USERS` The credentials required to access the app. You can specify multiple ones. **It is highly recommended to serve CrowdMixer through HTTPS** because it uses [HTTP basic auth](https://en.wikipedia.org/wiki/Basic_access_authentication)
  - `FORCE_LANGUAGE` Force the lang to be one of the supported ones (defaults to `None`: auto-detection from the `Accept-Language` HTTP header). See in the features section above for a list of available lang keys
  - `DEFAULT_LANGUAGE` Default language if it cannot be determined automatically. Not taken into account if `FORCE_LANGUAGE` is defined. See in the features section above for a list of available lang keys
  - `MUSIC_DIRS` A list of directories absolute paths containing songs (read below for a list of supported formats)
  - `NOW_PLAYING_CACHE_TIME` Number of seconds the "Now playing" information will be stored in the cache

I'll let you search yourself about how to configure a web server along uWSGI.

## Usage

  - Standalone

Run the internal web server, which will be accessible at `http://localhost:8080`:

```
python local.py
```

Edit this file and change the interface/port as needed.

  - uWSGI

The uWSGI file you'll have to set in your uWSGI configuration is `uwsgi.py`. The callable is `app`.

  - Others

You'll probably have to hack with this application to make it work with one of the solutions described
[here](http://flask.pocoo.org/docs/0.12/deploying/). Send me a pull request if you make it work.

## How it works

This project is built on [Flask](http://flask.pocoo.org/) (Python) for the backend which is using a small [SQLite](https://en.wikipedia.org/wiki/SQLite)
database to persist data. The `flask index` command is used to index the songs with the help of the [tinytag](https://github.com/devsnd/tinytag) package.

Several methods are used to control and retrieve information of an audio player, read below for more information.

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

The method used to control and retrieve information of an audio player from CrowdMixer is choosed regarding three criteria:

  1. **Simplicity of implementation**: CLI is easier than everything, HTTP is easier than raw TCP, etc.
  2. **Cross-platformness**: CLI is fully cross-platform, dbus is only supported on Linux-based operating systems, etc. This criteria depends of course of the operating system availability of the audio player.
  3. **As native as possible**: Doesn't require installation of a third-party software like a plugin, an external tool, etc. other than one needed by CrowdMixer internally.
  4. **As fast as possible**: CLI is faster than everything, HTTP is slower than raw TCP, etc.

| Name | Method used to add a song | Method used to get the currently playing song |
|------|---------------------------|-----------------------------------------------|
| [AIMP](https://www.aimp.ru/) | [CLI](http://www.aimp.ru/index.php?do=download&cat=sdk) | [Windows Messages](http://www.aimp.ru/index.php?do=download&cat=sdk) |
| [Audacious](http://audacious-media-player.org/) | [CLI](https://www.mankier.com/1/audacious) | ❌ |
| [Clementine](https://www.clementine-player.org/) | [CLI](https://github.com/clementine-player/Clementine/issues/4030#issuecomment-30595412) | [TCP](https://github.com/clementine-player/Android-Remote/wiki/Developer-Documentation) |
| [foobar2000](http://www.foobar2000.org/) | [CLI](http://wiki.hydrogenaud.io/index.php?title=Foobar2000:Commandline_Guide) | ❌ |
| [MediaMonkey](http://www.mediamonkey.com/) | [CLI](http://www.mediamonkey.com/support/index.php?/Knowledgebase/Article/View/44/2/command-line-startup-options-for-mediamonkey) | ❌ |
| [MusicBee](http://getmusicbee.com/) | [CLI](http://musicbee.wikia.com/wiki/Command_Line_Parameters) | ❌ |
| [Music Player Daemon](https://www.musicpd.org/) | [CLI](https://linux.die.net/man/1/mpc) | [CLI](https://linux.die.net/man/1/mpc) |
| [Rhythmbox](https://wiki.gnome.org/Apps/Rhythmbox) | [CLI](http://manpages.ubuntu.com/manpages/trusty/man1/rhythmbox-client.1.html) | ❌ |
| [VLC](http://www.videolan.org/vlc/) | [CLI](https://wiki.videolan.org/VLC_command-line_help/) | [HTTP](https://wiki.videolan.org/VLC_HTTP_requests/) |
| [Winamp](http://www.winamp.com/) | [CLI](http://forums.winamp.com/showthread.php?threadid=180297) | ❌ |
| [XMMS2](https://xmms2.org/) | [CLI](http://manpages.ubuntu.com/manpages/zesty/man1/xmms2.1.html) | [CLI](http://manpages.ubuntu.com/manpages/zesty/man1/xmms2.1.html) |

## End words

If you have questions or problems, you can [submit an issue](https://github.com/EpocDotFr/crowdmixer/issues).

You can also submit pull requests. It's open-source man!
