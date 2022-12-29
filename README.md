# pypre - a cbftp python wrapper to manage uploads and pres

Note: this repository is a mirror, and only tagged releases are tracked.

pypre gives convenient commands to upload, fxp and pre releases using the [cbftp REST API](https://cbftp.gay/svn/cbftp/API).
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
  - [Todo](#todo)

## Installation

pypre requires Python>=3.9, and is only tested on Linux.

It is recommended to use a virtual environment to run this program. Be sure to have [setuptools](https://setuptools.pypa.io/en/latest/index.html) installed.

```sh
virtualenv env
pip install -U pip setuptools wheels
```

To install the package:

```sh
pip install .
```

Make sure to have cbftp up and running, and check that the REST API is activated.

## Configuration

pypre is almost entirely configurable. You can find an example config at [`config_example.toml`](config/config_example.toml).

By default, pypre will use the environment variable `PYPRE_CONFIG` to determine the location of your config file. If not set, it will use the path `config/config.toml` from the current working directory.

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

Each regex value of the configuration will be tested one by one, until a match is found (matches are case insensitive). It is therefore recommended to define the most specific sections first.

To determine the site section, this matching pattern will be used. By default, the key corresponding to the regex pattern will be used. If `sections_config` is defined in the [site configuration](#sites), the mapping from the site will be used (see below).

### Sites

The following example will be used:

```toml
[sites.XX]
id = 'XX'
groups_dir = '/groups/'
[sites.XX.dir_config]
all = 'GROUP'
match_group = true
default = 'DEFAULT_GROUP'
[sites.XX.dir_config.group_map]
GROUP = 'GROUP_ALT'

[sites.XX.sections_config]
ebook-fr = 'ebook'
```

- `id`: the cbftp site name, case sensitive. It is advised to use the same as the config key.
- `groups_dir`: the site group directory.
- `dir_config`: defines which group directory should be used on site depending on the release name.
  - `all`: this group directory will be used in any case, no matter the release name group tag.
  - `match_group`: will use the release name tag as the group directory.
  - `default`: if the returned group directory does not exist on the site, will use this one instead.
  - `group_map`: If 'all' or 'match_group' is not set, will use this dictionnary to map group tag from the release name to a specific directory
- `sections_config`: optional section configuration. Once the section have been determined using the `[sections]` mapping, the section will be mapped to a site specific section.

Here is a use case of the last parameter:

The section of the release `release.FRENCH.eBook-GRP` returned by the the `[sections]` regex pattern matching is `ebook-fr`.

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
pypre cmd -h  # Or pp cmd -h
```

For generic parameters, you can check the main command help:

```sh
pypre -h
```

To tell which cbftp server to use, specify the server name via the `--cbftp` option:

```sh
pypre --cbftp cbftp_1 cmd
```

You can also set a default value with the `[arguments]` configuration. See the example config for more details.

You can provide the releases to be processed in several ways:
- Using the `--releases` argument
- From a file using the `--file` argument
- Using a glob expression with the `--glob` argument

To abort transfers, you can use your keyboard interrupt key.

## Todo

- Use spread jobs to FXP.
- Check if exceptions are defined properly.
- Fix progress bars on fxp transfers.
- Add more logging.
- Fix MP3 internal releases not parsed properly by `CBFTPManager.get_group_dir`
