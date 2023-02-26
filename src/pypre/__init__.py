__version__ = "1.3.1"
__version_info__ = tuple(int(i) for i in __version__.split(".") if i.isdigit())

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
