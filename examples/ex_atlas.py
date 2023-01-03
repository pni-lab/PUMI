import os
from PUMI.pipelines.multimodal.atlas import *

ROOT_DIR = os.path.dirname(os.getcwd())

input_dir = os.path.join(ROOT_DIR, 'data_in/bids')  # path where the bids data is located
output_dir = os.path.join(ROOT_DIR, 'data_out')  # path for the folder with the results of this script
working_dir = os.path.join(ROOT_DIR, 'data_out')  # path for the workflow folder

fetch_atlas('MIST')