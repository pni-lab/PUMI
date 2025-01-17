from PUMI.engine import QcPipeline, GroupPipeline
from PUMI.engine import NestedNode as Node
import nipype.interfaces.fsl as fsl
from nipype.interfaces.utility import Function
from PUMI.utils import get_reference


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
def create_ventricle_mask(wf, fallback_threshold=0, fallback_dilate_mask=0, **kwargs):
    """
    Pipeline for generating a ventricle mask based on CSF probability segmentation and an atlas.

    This pipeline generates a ventricle mask by thresholding the CSF probability map,
    combining it with atlas-defined ventricle labels, and optionally dilating the resulting mask.

    Inputs:
        csf_probseg (str): Path to the CSF probability segmentation file.
        template (str): Path to the template image file used for QC.

    Outputs:
        out_file (str): Path to the generated ventricle mask file.

    Parameters:
        wf (Workflow): The workflow object.
        fallback_threshold (float, optional): Default threshold for the CSF probability map thresholding.
            Used if not defined in the settings file (default: 0).
        fallback_dilate_mask (int, optional): Default dilation value for the ventricle mask.
            Used if not defined in the settings file (default: 0).
        kwargs (dict): Additional arguments for the workflow.

    Raises:
        ValueError: If ventricle labels are not defined in the configuration file.
    """

    # Load ventricle labels from settings.ini
    ventricle_labels = wf.cfg_parser.get('TEMPLATES', 'ventricle_labels', fallback='')
    ventricle_labels = [int(label) for label in ventricle_labels.replace(' ', '').split(',')]
    if len(ventricle_labels) == 0:
        raise ValueError('You need to define ventricle labels in settings.ini!')

    # Threshold ventricle labels individually
    threshold_nodes = []
    atlas = get_reference(wf, 'atlas')

    for label in ventricle_labels:
        node = Node(fsl.ImageMaths(op_string=f"-thr {label} -uthr {label} -bin"), name=f'threshold_ventricle_{label}')
        node.inputs.in_file = atlas
        wf.add_nodes([node])
        threshold_nodes.append(node)

    # Use MultiImageMaths to combine all ventricle masks using -max
    combine_ventricles_op_string = " ".join(["-add %s"] * (len(threshold_nodes) - 1))
    combine_ventricles = Node(fsl.MultiImageMaths(op_string=combine_ventricles_op_string), name='combine_ventricles')
    wf.connect(threshold_nodes[0], 'out_file', combine_ventricles, 'in_file')
    for n in threshold_nodes[1:]:
        wf.connect(n, 'out_file', combine_ventricles, 'operand_files')

    # Dilate ventricle mask
    dilate_mask_value = int(wf.cfg_parser.get('FSL', 'ImageMaths_dilate_ventricle_mask', fallback=fallback_dilate_mask))
    dilate_mask_op_string = '-dilM ' * dilate_mask_value + '-bin'
    dilate_ventricle_mask = Node(fsl.ImageMaths(op_string=dilate_mask_op_string), name='dilate_ventricle_mask')
    wf.connect(combine_ventricles, 'out_file', dilate_ventricle_mask, 'in_file')

    # Threshold CSF probability map
    threshold = float(wf.cfg_parser.get('FSL', 'ImageMaths_ventricle_threshold', fallback=fallback_threshold))
    threshold_csf = Node(fsl.ImageMaths(op_string=f'-thr {threshold} -bin'), name='threshold_csf')
    wf.connect('inputspec', 'csf_probseg', threshold_csf, 'in_file')

    # Multiply the combined ventricle mask with the CSF mask
    combine_csf_ventricles = Node(fsl.MultiImageMaths(op_string='-mul %s'), name='combine_csf_ventricles')
    wf.connect(threshold_csf, 'out_file', combine_csf_ventricles, 'in_file')
    wf.connect(dilate_ventricle_mask, 'out_file', combine_csf_ventricles, 'operand_files')

    # QC
    qc_create_ventricle_mask = qc(name='qc_create_ventricle_mask', qc_dir=wf.qc_dir)
    wf.connect(combine_csf_ventricles, 'out_file', qc_create_ventricle_mask, 'ventricle_mask')
    wf.connect('inputspec', 'template', qc_create_ventricle_mask, 'template')

    # Sinking
    wf.connect(combine_csf_ventricles, 'out_file', 'sinker', 'create_ventricle_mask')

    # Outputspec
    wf.connect(combine_csf_ventricles, 'out_file', 'outputspec', 'out_file')
