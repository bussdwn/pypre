__version__ = "1.4.0"
__version_info__ = tuple(int(i) for i in __version__.split(".") if i.isdigit())

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
