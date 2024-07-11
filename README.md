# pypre - a cbftp python wrapper to manage uploads and pres

pypre gives convenient commands to upload, fxp and pre releases using the [cbftp REST API](https://cbftp.glftpd.io/svn/cbftp/API).
It does not handle spread jobs.

pypre is fully typed and mypy compliant.

- [pypre - a cbftp python wrapper to manage uploads and pres](#pypre---a-cbftp-python-wrapper-to-manage-uploads-and-pres)
  - [Installation](#installation)
  - [Configuration](#configuration)
    - [cbftp](#cbftp)
    - [Sections](#sections)
    - [Sites](#sites)
    - [Proxies](#proxies)
    - [Logging](#logging)
  - [Usage](#usage)
    - [Example commands](#example-commands)
  - [Configuration encryption](#configuration-encryption)
  - [Todo](#todo)

## Installation

pypre requires Python>=3.9, and is only tested on Linux.

It is recommended to use a virtual environment to run this program.

```sh
virtualenv env
```

To install the package:

```sh
pip install .
```

Make sure to have cbftp up and running, and check that the REST API is activated.

## Configuration

pypre is almost entirely configurable. You can find an example config at [`config_example.toml`](config/config_example.toml).

By default, pypre will use the `PYPRE_CONFIG` environment variable to determine the location of your config file. If not set, it will use the file `config.toml`, relative to the current working directory.

### cbftp

You can add multiple cbftp servers. Here is an example configuration:

```toml
[cbftp]

[cbftp.cbftp_1]
base_url = 'https://adress:port'
password = 'password'
verify = false
proxy = 'my_proxy'
```

- `cbftp_1` is a generic name. You can set any name you want.
- `base_url` and `password` are the REST API url and password.
- `verify` is used to determine wether SSL certificates should be ignored. By default, should be set to `false`.
- `proxy` is the proxy name to be used to request the cbftp API. The proxy should be defined in [proxies](#Proxies).

### Sections

To determine the section from the release name, a regex matching configuration must be set:

```toml
sections = [
    ['ebook-fr','.+FRENCH\.(HYBRID|SCAN|RETAIL).+eBook-.+'],
    ['ebook','.+(HYBRID|SCAN|RETAIL).+eBook-.+'],
    ['tv-720p','.+S\d{2,3}E\d+720p.+x264.+']
]
```

Each section is defined as a two-tuple, the first element being the section identifier (it's a generic one, not related to section names of any site). The second one is a regex value that is compiled with the [`re.IGNORECASE` flag](https://docs.python.org/fr/3/library/re.html#re.I).

Each regex value of the configuration will be tested one by one against the release name, until a match is found (matches are case insensitive). It is therefore recommended to define the most specific sections first, as showed in the example above.

To determine the section name for each site, this matching pattern will be used. By default, the key corresponding to the regex pattern will be used. If `sections_config` is defined in the [site configuration](#sites), the mapping from the site will be used (see below).

### Sites

Here is a working example of a site configuration:

```toml
[sites.XX]
id = 'XX'
pre_command = 'site pre {release} {section}'
groups_dir = '/groups/'
[sites.XX.dir_config]
match_group = true

[sites.XX.sections_config]
ebook-fr = 'ebook'
```

- `id`: the cbftp site name, case sensitive. It is advised to use the same as the config key.
- `pre_command`: The pre command template to be used. Must contain the two template strings `{release}` and `{section}`.
- `groups_dir`: the site group directory. Must be the absolute path from `/`.

#### `dir_config`

Releases will be uploaded into this directory relative to `groups_dir` (e.g. if the determined group directory is `GROUP1`, and `groups_dir` is set to `/groups/`, the release will be uploaded in `/groups/GROUP1/`).

Different settings are available:

- `all` (string): this group directory will be used in all cases, no matter the release name group tag.

```toml
[sites.XX]
id = 'XX'
groups_dir = '/groups/'
[sites.XX.dir_config]
all = 'GROUP1'  # All releases will be uploaded to /groups/GROUP1/
```

- `match_group` (boolean): will extract the group tag from the release name as the group directory.
- `group_map` (dict): if 'all' or 'match_group' is not set, will use this dictionary to map group tag from the release name to a specific directory.

```toml
[sites.XX]
id = 'XX'
groups_dir = '/groups/'
[sites.XX.dir_config.group_map]
CoolTVGRP_SD = 'CoolTVGRP'  # Releases having the CoolTVGRP_SD tag will be uploaded to /groups/CoolTVGRP/
CoolTVGRP_HD = 'CoolTVGRP'  # Releases having the CoolTVGRP_HD tag will be uploaded to /groups/CoolTVGRP/
```

- `default` (string): if the group directory from the above parameters does not exist on the site, this one will be used instead.

#### `sections_config`

Optional section configuration. Once the section identifier has been determined using the `[sections]` mapping, the section will be mapped to a site specific section.

Here is a use case of the last parameter:

The section of the release `release.FRENCH.eBook-GRP` returned by the `[sections]` regex pattern matching is `ebook-fr`.

Let's say we have two sites, `S1` and `S2`:
- The French ebook section of `S1` is `ebook-fr`. Therefore we don't need any more configuration and `sections_config` can be omitted.
- There is no French ebook section on `S2`, and `ebook` should be used. We can then define a `sections_config` this way:

```toml
[sites.S2.sections_config]
ebook-fr = 'ebook'
```

### Proxies

```toml
[proxies]
my_proxy = ''
```

You can define proxies here. If set, the socks5 proxy from the cbftp config will be used when connecting to the API.

### Logging

Logging can be configured through the use of the configuration file ([`dictConfig`](https://docs.python.org/3/library/logging.config.html#logging.config.dictConfig) is used). A default config is given in [`config_example.toml`](config/config_example.toml)

To add another handler (say a [`RotatingFileHandler`](https://docs.python.org/3/library/logging.handlers.html#rotatingfilehandler)) to `pypre`, add the following to your config:

```toml
[logging.handlers.rotatingfile]
class = 'logging.handlers.RotatingFileHandler'
formatter = 'verbose'
filename = 'pypre.log'
maxBytes = 10485760
backupCount = 5
```

And add the created `rotatingfile` handler to the `logging.loggers.pypre.handlers` list.

## Usage

pypre provides three main commands, `upload`, `fxp` and `pre`.

You can find help for each command using:

```sh
pypre cmd --help  # Or pp cmd --help
```

For generic parameters, you can check the main command help:

```sh
pypre --help
```

To tell which cbftp server to use, specify the server name via the `--cbftp` option:

```sh
pypre --cbftp cbftp_1 cmd
```

You can also set a default value with the `[arguments]` configuration. See the [example config](config/config_example.toml) for more details.

You can provide the releases to be processed in several ways:
- Using the `--releases` argument (short: `-r`)
- From a file using the `--file` argument
- Using a glob expression with the `--glob` argument (short: `-g`)

To abort transfers, you can use your keyboard interrupt key.

### Example commands

Upload all releases matching the glob pattern `*x264*MYGRP` to site `S1`, wait for uploads to complete before exiting, and check completeness of releases once uploaded:

```sh
pypre upload -g "*x264*MYGRP" -s S1 -w -c
```

FXP the previously uploaded releases from `S1` to `S2` and `S3`:

```sh
pypre fxp -g "*x264*MYGRP" -f S1 -t S2 -t S3 -w -c
```

Pre the previously uploaded and transferred releases on `S1`, `S2` and `S3`, with a cooldown of 10 seconds between each pre:

```sh
pypre pre -g "*x264*MYGRP" -s S1 -s S2 -s S3 -c 10
```

## Configuration encryption

It is possible to encrypt your configuration file with a passphrase. The [encrypt_config.py](scripts/encrypt_config.py) script can be used to do so:

```sh
python scripts/encrypt_config.py /path/to/config.toml --outpath /path/to/encrypted
```

If `--outpath` isn't provided, the original config file will be overridden. The passphrase will then be asked each time `pypre` is used, unless the `PYPRE_CONFIG_KEY` environment variable is set.

`cryptography` is required to use this feature, and can be installed using the following command: `pip install pypre[crypto]`.

## Todo

- Use spread jobs to FXP.
- Check if exceptions are defined properly.
- Fix progress bars on fxp transfers.
- Add more logging.
- Fix MP3 internal releases not parsed properly by `CBFTPManager.get_group_dir`
