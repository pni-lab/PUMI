from configparser import SafeConfigParser
import PUMI
import os

cfg_parser = SafeConfigParser()
cfg_parser.read(os.path.join(os.path.dirname(PUMI.__file__), 'settings.ini'))