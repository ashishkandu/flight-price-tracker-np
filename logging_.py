import logging
import logging.config
import yaml
import os

def log_setup(cfg_path:str = 'cfg.yaml', default_level = logging.DEBUG):
    """Initializes logging configuration"""
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, 'rt') as cfg_file:
                config = yaml.safe_load(cfg_file.read())
                logging.config.dictConfig(config)
        except Exception as e:
            print("Failed to load configuration, using default configuration!")
            logging.basicConfig(level=default_level)
    else:
        print("Configuration file not found, using default configuration!")
        logging.basicConfig(level=default_level)