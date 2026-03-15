from configparser import ConfigParser
import PUMI
import os

cfg_parser = ConfigParser()
cfg_parser.optionxform = str
cfg_parser.read(os.path.join(os.path.dirname(PUMI.__file__), 'settings.ini'))