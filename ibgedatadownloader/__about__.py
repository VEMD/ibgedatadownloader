"""Metadata about the package to easily retrieve informations about it.

See: https://packaging.python.org/guides/single-sourcing-package-version/
"""

# ############################################################################
# ########## Libraries #############
# ##################################

# standard library
import unicodedata
from configparser import ConfigParser
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

# ############################################################################
# ########## Globals ###############
# ##################################
__all__: List[str] = [
    "__author__",
    "__copyright__",
    "__email__",
    "__license__",
    "__summary__",
    "__title__",
    "__uri__",
    "__version__",
]


DIR_PLUGIN_ROOT: Path = Path(__file__).parent
PLG_METADATA_FILE: Path = DIR_PLUGIN_ROOT.resolve() / "metadata.txt"


# ############################################################################
# ########## Functions #############
# ##################################
def plugin_metadata_as_dict() -> Dict[str, Dict[str, str]]:
    """Read plugin metadata.txt and returns it as a Python dict.

    Raises:
        FileNotFoundError: if metadata.txt is not found
        Exception: if metadata.txt doesn't contain a [general] section or required fields are missing

    Returns:
        dict: dict of dicts.
    """
    if not PLG_METADATA_FILE.is_file():
        raise FileNotFoundError(f"Plugin metadata.txt not found at {PLG_METADATA_FILE.parent}")

    config = ConfigParser()
    config.read(PLG_METADATA_FILE.resolve(), encoding="UTF-8")
    metadata = {s: dict(config.items(s)) for s in config.sections()}

    if metadata.get("general") is None:
        raise Exception(f"No [general] section in {PLG_METADATA_FILE}")

    required = ("name", "qgisminimumversion", "description", "about", "version", "author", "repository")
    missing = [field for field in required if not metadata["general"].get(field)]
    if missing:
        raise Exception(f"Required fields missing from [general] section in metadata.txt: {', '.join(missing)}")

    return metadata


# ############################################################################
# ########## Variables #############
# ##################################

# store full metadata.txt as dict into a var
__plugin_md__ = plugin_metadata_as_dict()

__author__: str = __plugin_md__["general"]["author"]
__copyright__: str = f"2022 - {date.today().year}, {__author__}"
__email__: Optional[str] = __plugin_md__["general"].get("email") or None
__icon_path__: Optional[Path] = (
    DIR_PLUGIN_ROOT.resolve() / __plugin_md__["general"]["icon"] if __plugin_md__["general"].get("icon") else None
)
__keywords__: List[str] = [t.strip() for t in __plugin_md__["general"].get("tags", "").split(",")]
__license__: str = "GPLv2+"
__summary__: str = f'{__plugin_md__["general"].get("description", "")}\n{__plugin_md__["general"].get("about", "")}'

__title__: str = __plugin_md__["general"]["name"]
__title_clean__: str = "".join(char for char in unicodedata.normalize("NFD", __title__) if char.isalnum())

__uri_homepage__: Optional[str] = __plugin_md__["general"].get("homepage") or None
__uri_repository__: str = __plugin_md__["general"]["repository"]
__uri_tracker__: Optional[str] = __plugin_md__["general"].get("tracker") or None
__uri__: str = __uri_repository__

__version__: str = __plugin_md__["general"]["version"]
__version_info__: Tuple[Union[int, str], ...] = tuple(
    int(num) if num.isdigit() else num for num in (__version__).replace("-", ".", 1).split(".")
)


# #############################################################################
# ##### Main #######################
# ##################################
if __name__ == "__main__":
    print(f"Plugin: {__title__}")
    print(f"By: {__author__}")
    print(f"Version: {__version__}")
    print(f"Description: {__summary__}")
    print(f"Repository: {__uri_repository__}")
    print(f"Icon: {__icon_path__}")
    general_md = __plugin_md__["general"]
    qgis_max_ver = general_md.get("qgismaximumversion") or general_md["qgisminimumversion"].split(".", 1)[0] + ".99"
    print(f'For: {general_md["qgisminimumversion"]} > QGIS > {qgis_max_ver}')

    print(__title_clean__)
