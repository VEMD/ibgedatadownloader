import configparser

from qgispluginci import changelog, parameters, utils

config = configparser.ConfigParser()
config.read("setup.cfg", encoding="utf-8")

utils.replace_in_file(
    f"{parameters.Parameters(dict(config.items('qgis-plugin-ci'))).plugin_path}/metadata.txt",
    r"^version=.*$",
    f"version={changelog.ChangelogParser().latest_version()}",
)
