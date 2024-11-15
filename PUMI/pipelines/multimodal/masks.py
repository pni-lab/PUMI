from PUMI.engine import QcPipeline, GroupPipeline
from PUMI.engine import NestedNode as Node
import nipype.interfaces.fsl as fsl
from nipype.interfaces.utility import Function


@QcPipeline(inputspec_fields=['ventricle_mask', 'template'],
            outputspec_fields=['out_file'])
def qc(wf, **kwargs):
    """
    Pipeline for generating QC images for ventricle mask creation.

    Inputs:
        ventricle_mask (str): Path to the ventricle mask file.
        template (str): Path to the template image file.

    Outputs:
        out_file (str): Path to the output QC image.

    Parameters:
        wf (Workflow): The workflow object.
        kwargs (dict): Additional arguments for the workflow.
    """

    def create_image(ventricle_mask, template):
        """
        Create a QC image overlaying the ventricle mask on the template.

        Parameters:
            ventricle_mask (str): Path to the ventricle mask file.
            template (str): Path to the template image file.

        Returns:
            str: Path to the output QC image.
        """
        from PUMI.utils import plot_roi

        _, out_file = plot_roi(roi_img=ventricle_mask, bg_img=template, cmap='winter', save_img=True)
        return out_file

    plot = Node(Function(input_names=['ventricle_mask', 'template'],
                         output_names=['out_file'],
                         function=create_image),
                name='plot')
    wf.connect('inputspec', 'ventricle_mask', plot, 'ventricle_mask')
    wf.connect('inputspec', 'template', plot, 'template')

    # Sinking
    wf.connect(plot, 'out_file', 'sinker', 'qc_ventricle_mask')

    # Output
    wf.connect(plot, 'out_file', 'outputspec', 'out_file')


@GroupPipeline(inputspec_fields=['csf_probseg', 'template'],
               outputspec_fields=['out_file'])
def create_ventricle_mask(wf, fallback_threshold=0.7, **kwargs):
    """
    Pipeline for creating ventricle masks.

    Inputs:
        csf_probseg (str): Path to the CSF probability segmentation file.
        template (str): Path to the template file used as the background for QC images.

    Outputs:
        out_file (str): Path to the generated ventricle mask file.

    Parameters:
        wf (Workflow): The workflow object.
        fallback_threshold (float): Threshold for binarizing the ventricle mask,
            used only if no threshold is set in settings.ini.
        kwargs (dict): Additional arguments for the workflow.
    """
    threshold = float(wf.cfg_parser.get('FSL', 'ImageMaths_ventricle_threshold', fallback=fallback_threshold))

    binary_mask = Node(interface=fsl.ImageMaths(op_string=f'-thr {threshold} -bin'), name='binary_mask')
    binary_mask.inputs.suffix = 'ventricle_mask'
    wf.connect('inputspec', 'csf_probseg', binary_mask, 'in_file')

    # QC
    qc_create_ventricle_mask = qc(name='qc_create_ventricle_mask', qc_dir=wf.qc_dir)
    wf.connect(binary_mask, 'out_file', qc_create_ventricle_mask, 'ventricle_mask')
    wf.connect('inputspec', 'template', qc_create_ventricle_mask, 'template')

    # Sinking
    wf.connect(binary_mask, 'out_file', 'sinker', 'create_ventricle_mask')

    # Output
    wf.connect(binary_mask, 'out_file', 'outputspec', 'out_file')
