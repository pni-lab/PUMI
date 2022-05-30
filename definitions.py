import os

# includes important Paths which are used frequently

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_IN_DIR = os.path.join(ROOT_DIR, 'data_in')
DATA_OUT_DIR = os.path.join(ROOT_DIR, 'data_out')
BIDS_DIR = os.path.join(ROOT_DIR, 'data_in', 'bids')

