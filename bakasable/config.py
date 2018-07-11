from appdirs import user_config_dir
from configparser import ConfigParser
import os


def get_config():
    config_dir = user_config_dir('Bakasable')
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, 'config.ini')
    config = ConfigParser()
    config.read(config_path)
    return config
