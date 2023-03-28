from nipype.interfaces.fsl import Reorient2Std

from PUMI.engine import BidsPipeline, NestedNode as Node
from PUMI.pipelines.anat.anat_proc import anat_proc
from PUMI.pipelines.func.compcor import anat_noise_roi, compcor
from PUMI.pipelines.anat.func_to_anat import func2anat
import os

from PUMI.pipelines.func.temporal_filtering import temporal_filtering

ROOT_DIR = os.path.dirname(os.getcwd())

input_dir = os.path.join(ROOT_DIR, 'data_in/bids')  # path where the bids data is located
output_dir = os.path.join(ROOT_DIR, 'data_out')  # path for the folder with the results of this script
working_dir = os.path.join(ROOT_DIR, 'data_out')  # path for the workflow folder


@BidsPipeline(output_query={
    'bold': dict(
        datatype='func',
        extension=['nii', 'nii.gz']
    )
})
def my_tmpfilt(wf, **kwargs):
    reorient_func_wf = Node(Reorient2Std(output_type='NIFTI_GZ'), name="reorient_func_wf")
    wf.connect('inputspec', 'bold', reorient_func_wf, 'in_file')

    tmpfilt_wf = temporal_filtering('tmpfilt')
    tmpfilt_wf.get_node('inputspec').inputs.lowpass = 0.08
    tmpfilt_wf.get_node('inputspec').inputs.highpass = 0.008
    wf.connect(reorient_func_wf, 'out_file', tmpfilt_wf, 'func')

    wf.write_graph('despike_graph.png')



if __name__ == '__main__':
    my_tmpfilt('my_tmpfilt', base_dir=output_dir, bids_dir=input_dir, subjects=['001'])
