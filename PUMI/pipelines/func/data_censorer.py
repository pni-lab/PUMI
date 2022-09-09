from nipype.interfaces import utility

from PUMI.engine import FuncPipeline, NestedNode as Node, QcPipeline
from PUMI.pipelines.multimodal.image_manipulation import timecourse2png
from PUMI.utils import get_indx, scrub_image, above_threshold


@QcPipeline(inputspec_fields=['scrubbed_image'],
            outputspec_fields=['out_file'])
def qc_datacens(wf, **kwargs):
    censored_timeseries = timecourse2png('censored_timeseries')
    wf.connect('inputspec', 'scrubbed_image', censored_timeseries, 'func')
    wf.connect(censored_timeseries, 'out_file', 'sinker', 'qc_censored_timeseries')


@FuncPipeline(inputspec_fields=['func', 'FD', 'threshold'],
              outputspec_fields=['scrubbed_image', 'FD_scrubbed'])
def datacens_workflow_threshold(wf, ex_before=1, ex_after=2, **kwargs):
    """

    Do the data censoring on the 4D functional data.
    First, it calculates the framewise displacement according to Power's method.
    Second, it indexes the volumes which FD is in the upper part in percent (determined by the threshold variable which
    is 5% by default).
    Thirdly, it excludes those volumes and one volume before and 2 volumes after the indexed volume.
    The workflow returns a 4D scrubbed functional data.

    CAUTION: Name in the old PUMI was datacens_workflow_threshold

    Parameters:

    Inputs:
        func (str): The reoriented,motion occrected, nuissance removed and bandpass filtered functional file.
        FD (str): the frame wise displacement calculated by the MotionCorrecter.py script
        threshold (str): threshold of FD volumes which should be excluded

    Outputs:
        scrubbed_image (str)
        FD_scrubbed (str)

    Sinking
        -

    Acknowledgements:
        Adapted from Balint Kincses (2018).

        Modified version of
        CPAC.scrubbing.scrubbing
        (https://github.com/FCP-INDI/C-PAC/blob/main/CPAC/scrubbing/scrubbing.py),
        CPAC.generate_motion_statistics.generate_motion_statistics
        (https://github.com/FCP-INDI/C-PAC/blob/main/CPAC/generate_motion_statistics/generate_motion_statistics.py),
        CPAC.func_preproc.func_preproc
        (https://github.com/FCP-INDI/C-PAC/blob/main/CPAC/func_preproc/func_preproc.py)

        [1] Power, J. D., Barnes, K. A., Snyder, A. Z., Schlaggar, B. L., & Petersen, S. E. (2012). Spurious
            but systematic correlations in functional connectivity MRI networks arise from subject motion. NeuroImage, 59(3),
            2142-2154. doi:10.1016/j.neuroimage.2011.10.018
        [2] Power, J. D., Barnes, K. A., Snyder, A. Z., Schlaggar, B. L., & Petersen, S. E. (2012). Steps
            toward optimizing motion artifact removal in functional connectivity MRI; a reply to Carp.
            NeuroImage. doi:10.1016/j.neuroimage.2012.03.017
        [3] Jenkinson, M., Bannister, P., Brady, M., Smith, S., 2002. Improved optimization for the robust
            and accurate linear registration and motion correction of brain images. Neuroimage 17, 825-841.

    """

    # todo: test if everything that should be sinked is sinked

    if wf.get_node('inputspec').inputs.threshold is None:
        wf.get_node('inputspec').inputs.threshold = 0.2


    above_thr = Node(
        utility.Function(
            input_names=['in_file', 'threshold', 'frames_before', 'frames_after'],
                        output_names=['frames_in_idx', 'frames_out_idx', 'percentFD', 'percent_scrubbed_file',
                                      'fd_scrubbed_file', 'nvol'],
                        function=above_threshold
        ),
        name='above_threshold'
    )
    above_thr.inputs.frames_before = ex_before
    above_thr.inputs.frames_after = ex_after
    wf.connect('inputspec', 'FD', above_thr, 'in_file')
    wf.connect('inputspec', 'threshold', above_thr, 'threshold')

    # Generate the weird input for the scrubbing procedure which is done in afni
    craft_scrub_input = Node(
        utility.Function(
            input_names=['scrub_input', 'frames_in_1D_file'],
            output_names=['scrub_input_string'],
            function=get_indx
        ),
        name='scrubbing_craft_input_string'
    )
    wf.connect(above_thr, 'frames_in_idx', craft_scrub_input, 'frames_in_1D_file')
    wf.connect('inputspec', 'func', craft_scrub_input, 'scrub_input')

    # Scrub the image
    scrubbed_preprocessed = Node(
        utility.Function(
            input_names=['scrub_input'],
            output_names=['scrubbed_image'],
            function=scrub_image
        ),
        name='scrubbed_preprocessed'
    )

    wf.connect(craft_scrub_input, 'scrub_input_string', scrubbed_preprocessed, 'scrub_input')

    # qc
    myqc = qc_datacens('myqc_datacens')
    wf.connect(scrubbed_preprocessed, 'scrubbed_image', myqc, 'scrubbed_image')

    # Output
    wf.connect(scrubbed_preprocessed, 'scrubbed_image', 'outputspec', 'scrubbed_image')
    wf.connect(above_thr, 'fd_scrubbed_file', 'outputspec', 'FD_scrubbed')

    # Save a few files
    wf.connect(scrubbed_preprocessed, 'scrubbed_image', 'sinker', 'scrubbed_image')
    wf.connect(above_thr, 'fd_scrubbed_file', 'sinker', 'FD_scrubbed')
    wf.connect(above_thr, 'percent_scrubbed_file', 'sinker', 'percentFD')
