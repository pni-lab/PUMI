from PUMI.engine import FuncPipeline, QcPipeline, NestedNode as Node
from PUMI.pipelines.func.info.get_info import get_repetition_time
from nipype.interfaces import afni, utility
from PUMI.pipelines.multimodal.image_manipulation import timecourse2png


@QcPipeline(inputspec_fields=['in_file'],
            outputspec_fields=['out_file'])
def qc_temporal_filtering(wf, **kwargs):
    """

    Create quality check images for temporal filtering.

    Inputs
    ----------
    in_file (str): Temporal filtered data (e. g. result of afni 3dBandpass)

    Outputs
    ----------
    out_file (str): Path to quality check image

    Sinking
    ----------
    - quality check image

    """
    tc2png_tmpfilt = timecourse2png("tc2png_tmpfilt")
    wf.connect('inputspec', 'in_file', tc2png_tmpfilt, 'func')

    # sinking
    wf.connect(tc2png_tmpfilt, 'out_file', 'sinker', 'qc_temporal_filtering')

    # output
    wf.connect(tc2png_tmpfilt, 'out_file', 'outputspec', 'out_file')


@FuncPipeline(inputspec_fields=['func', 'highpass', 'lowpass'],
              outputspec_fields=['out_file'])
def temporal_filtering(wf, **kwargs):
    """

    Creates a slice time corrected functional image.

    Inputs
    ----------
    func (str): The reoriented functional file.
    highpass (str): The highpass filter in Hz (e. g. 0.008)
    lowpass (str): The lowpass filter in Hz (e. g. 0.08)

    Outputs
    ----------
    out_file (str): Temporal filtered data

    Acknowledgements
    ----------
    Adapted from Balint Kincses (2018)
    Modified version of porcupine generated temporal filtering code.

    """

    time_repetition = Node(
        interface=utility.Function(
            input_names=['in_file'],
            output_names=['tr'],
            function=get_repetition_time
        ),
        name='time_repetition'
    )
    wf.connect('inputspec', 'func', time_repetition, 'in_file')

    tmpfilt = Node(interface=afni.Bandpass(), name='tmpfilt')
    tmpfilt.inputs.despike = False
    tmpfilt.inputs.no_detrend = False
    tmpfilt.inputs.notrans = True
    tmpfilt.inputs.outputtype = 'NIFTI_GZ'
    wf.connect('inputspec', 'func', tmpfilt, 'in_file')
    wf.connect(time_repetition, 'tr', tmpfilt, 'tr')
    wf.connect('inputspec', 'highpass', tmpfilt, 'highpass')
    wf.connect('inputspec', 'lowpass', tmpfilt, 'lowpass')

    # qc
    myqc = qc_temporal_filtering('myqc')
    wf.connect(tmpfilt, 'out_file', myqc, 'in_file')

    # sinking
    wf.connect(tmpfilt, 'out_file', 'sinker', 'tmpfilt')

    # output
    wf.connect(tmpfilt, 'out_file', 'outputspec', 'out_file')
