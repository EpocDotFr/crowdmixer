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
  3. **IMPORTANT:** Other dependencies are needed regarding the audio player you'll use. Please refer to the table in the **Supported audio players** section below and install them accordingly before continuing
  4. `export FLASK_APP=crowdmixer.py` (Windows users: `set FLASK_APP=crowdmixer.py`)
  5. `flask create_database` (WARNING: don't re-run this command unless you want to start from scratch, it will wipe out all the data)
  6. `flask index` (this will index your songs, don't forget to set the `MUSIC_DIRS` configuration parameter before, read below. Run `flask index --help` for the full list of arguments)

## Configuration

Copy the `config.example.py` file to `config.py` and fill in the configuration parameters.

Available configuration parameters are:

  - `SECRET_KEY` Set this to a complex random value
  - `DEBUG` Enable/disable debug mode
  - `LOGGER_HANDLER_POLICY` Policy of the default logging handler

More informations on the three above can be found [here](http://flask.pocoo.org/docs/0.12/config/#builtin-configuration-values).

  - `FORCE_LANGUAGE` Force the lang to be one of the supported ones (defaults to `None`: auto-detection from the `Accept-Language` HTTP header). See in the features section above for a list of available lang keys
  - `DEFAULT_LANGUAGE` Default language if it cannot be determined automatically. Not taken into account if `FORCE_LANGUAGE` is defined. See in the features section above for a list of available lang keys
  - `MUSIC_DIRS` A list of directories absolute paths containing songs (read below for a list of supported formats)
  - `NOW_PLAYING_CACHE_TIME` Number of seconds the "Now playing" information will be stored in the cache
  - `MODE` Submit mode that should be used. Can be either `Immediate` (song queuing is immediate) or `Vote` (song is queued when a votes threshold is reached)
  - `VOTES_THRESHOLD` If `MODE` is equal to `Vote`: number of votes required to actually queue a song in the playlist
  - `BLOCK_TIME` Define the number of seconds a song that have just been queued is unavailable to submit
  - `REQUEST_LIMIT` Define the minimum number of seconds a user have to wait between each submit
  - `SHOW_CURRENT_PLAYING` Enable or disable the display of the currently playing song (support may vary following the audio player used, more information in the **Supported audio players** section below)
  - `PLAYER_TO_USE` The audio player to use. Can be one of the ones in the table below, in the **Supported audio players** section
  - `PLAYERS` Self-explanatory audio players-specific configuration values. Change them if your audio player of choice (`PLAYER_TO_USE`) is requiring it (see the table below, in the **Supported audio players** section)

I'll let you search yourself about how to configure a web server along uWSGI.

**Some audio players needs to be themselves configured**, you'll find the configuration instructions below according to
your audio player of choice.

### Clementine

You'll have to enable the remote controlling feature of Clementine before to use CrowdMixer. To do so:

  1. In the menu bar of Clementine, click **Tools** > **Settings...**
  2. In the **Remote control** tab, check the **Use remote control** checkbox
  3. At this point, you can either use the default parameters, or customize them. If so, don't forget to change the configuration values of Clementine accordingly in your `config.py`
  4. Click on **OK**

### Music Player Daemon

MPD, by design and by default, always open a remote control TCP connection on `*:6600`. You can change this behavior in
the `/etc/mpd.conf` configuration file (depending of your operating system). If so, don't forget to change the configuration
values of MPD accordingly in your `config.py`.

For more information, please read the MPD man page: `man mpd.conf` or read the [example configuration file](https://github.com/andrewrk/mpd/blob/master/doc/mpdconf.example).

### VLC

You'll have to enable the web interface feature of VLC before to use CrowdMixer. To do so:

  1. In the menu bar of VLC, click **Tools** > **Settings...**
  2. On the bottom left of the Settings window, click on **All** in the **Settings to display** box
  3. In the left list box that has been shown, click on **Interface** > **Main interface**
  4. Check the **Web** checkbox
  5. In the left list box, click on **Interface** > **Main interface** > **Lua**
  6. In the **Lua via HTTP** > **Password** textbox, enter a password that will be required to remote control VLC. **If you do not enter a password, remote control will not be possible for security reasons**
  7. At this point, you can either save the settings, or customize them. For more information, please read the [VLC documentation](https://wiki.videolan.org/Documentation:Modules/http_intf/)

Don't forget to change the configuration values of VLC according to your VLC settings in your `config.py`.

### XMMS2

> TODO

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

**CrowdMixer requires to be ran on the same computer that is running your prefered audio player**.

The following methods are used to control and retrieve information of an audio player from CrowdMixer:

| Name | "Now playing" supported? | Configuration value | Additional PyPI dependencies | Needs additional configuration in `config.py`? |
|------|--------------------------|---------------------|------------------------------|------------------------------------------------|
| [AIMP](https://www.aimp.ru/) | ✔ | `Aimp` | `pyaimp` | ❌ |
| [Audacious](http://audacious-media-player.org/) | ? | `Audacious` | ? | ? |
| [Clementine](https://www.clementine-player.org/) | ✔ | `Clementine` | `protobuf` | ✔ |
| [foobar2000](http://www.foobar2000.org/) | ? | `Foobar2000` | ? | ? |
| [iTunes](https://www.apple.com/itunes/) | ✔ | `Itunes` | `appscript` | ❌ |
| [MediaMonkey](http://www.mediamonkey.com/) | ? | `MediaMonkey` | ? | ? |
| [MusicBee](http://getmusicbee.com/) | ? | `MusicBee` | ? | ? |
| [Music Player Daemon](https://www.musicpd.org/) | ✔ | `Mpd` | `python-musicpd` | ✔ |
| [Rhythmbox](https://wiki.gnome.org/Apps/Rhythmbox) | ? | `Rhythmbox` | ? | ? |
| [VLC](http://www.videolan.org/vlc/) | ✔ | `Vlc` | `requests` | ✔ |
| [Winamp](http://www.winamp.com/) | ? | `Winamp` | ? | ? |
| ~~[Windows Media Player](https://en.wikipedia.org/wiki/Windows_Media_Player)~~ |  |  |  |  |
| [XMMS2](https://xmms2.org/) | ✔ | `Xmms2` | ? | ✔ |

## End words

If you have questions or problems, you can [submit an issue](https://github.com/EpocDotFr/crowdmixer/issues).

You can also submit pull requests. It's open-source man!
