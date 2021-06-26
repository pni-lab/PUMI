from nipype.interfaces.base import CommandLineInputSpec, File, TraitedSpec, traits_extension, traits, CommandLine
import os.path


class HDBetInputSpec(CommandLineInputSpec):
    in_file = File(
        desc='file to skull strip',
        mandatory=True,
        exists=True,
        argstr='--input=%s',
        hash_files=False,
        copyfile=False,
        position=0,
    )
    out_file = File(
        desc='filename of the output containing the extracted brain (the skull stripped file)',
        exists=False,
        mandatory=False,
        argstr='--output=%s',
        hash_files=False,
        position=1
    )
    mode = traits.Str(
        desc='mode can be either \'fast\' or \'accurate\'',
        argstr='-mode=%s'
    )
    device = traits.Str(
        desc='Set which device should be used. Can be either \'cpu\' to run on cpu or a GPU ID',
        argstr='-device=%s'
    )
    tta = traits.Int(
        desc='set to \'1\' to use test time data augmentation, otherwise set to \'0\'',
        argstr='-tta=%i'
    )
    postprocessing = traits.Int(
        desc='set to \'1\' to do postprocessing, otherwise set to \'0\'',
        argstr='-pp=%i'
    )
    save_mask = traits.Int(
        desc='set to \'1\' to save the brain mask, otherwise set to \'0\'',
        argstr='-s=%i'
    )
    overwrite_existing = traits.Int(
        desc='set to \'1\' to overwrite existing predictions, otherwise set to \'0\'',
        argstr='--overwrite_existing=%i'
    )


class HDBetOutputSpec(TraitedSpec):
    out_file = File(desc='the skull stripped file')
    mask_file = File(desc='brain mask (if generated)')


class HDBet(CommandLine):
    """
    HD-Bet wrapper.
    For more information about HD-Bet: https://github.com/MIC-DKFZ/HD-BET
    """
    _cmd = 'hd-bet'
    input_spec = HDBetInputSpec
    output_spec = HDBetOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = self._out_file_filename()
        if self.inputs.save_mask == 1:
            outputs['mask_file'] = self._mask_file_filename()
        return outputs

    def _out_file_filename(self):
        """
        Generates the filename for 'out_file' and returns the absolute path to the file.
        The returned path leads to the same folder where the input file is located.

        If an output filename was specified (e.g. 'extracted_brain' or 'extracted_brain.nii.gz') and the input file
        is in the folder '/home/data_in', the filename is simply '/home/data_in/extracted_brain.nii.gz.'

        If no output filename is specified, '_bet' is appended to the input filename.
        Example: If the input was '/home/data_in/sub-001_T1w.nii.gz', the output name would be
                 '/home/data_in/sub-001_T1w_bet.nii.gz'.

        Note: HD-Bet works only with .nii.gz files
        """
        if traits_extension.isdefined(self.inputs.out_file):
            path = self.inputs.out_file
            if not path.endswith('.nii.gz'):
                path += '.nii.gz'
        else:
            path = self.inputs.in_file
            index = self.inputs.in_file.rindex('.nii.gz')
            path = path[:index] + '_bet.nii.gz'
        return os.path.abspath(path)

    def _mask_file_filename(self):
        """
        Generates the filename for 'mask_file' and returns the absolute path to the file.
        The returned path leads to the same folder where the input file is located.

        If 'out_file' was defined, then '_mask' is appended to it.
        Example: If out_file is 'extracted_brain.nii.gz' and the input is in the folder '/home/data_in' the result would
                 be '/home/data_in/extracted_brain_mask.nii.gz'.

        If 'out_file' is not specified, '_mask' is appended to the filename of the extracted brain.
        Example: If the skull stripped file is called 'sub-001_T1w_bet.nii.gz' and is located in the folder
        '/home/data_in, the output filename would be '/home/data_in/sub-001_T1w_bet_mask.nii.gz'.

        Note: HD-Bet works only with .nii.gz files
        """
        if traits_extension.isdefined(self.inputs.out_file):
            path = self.inputs.out_file
            if not path.endswith('.nii.gz'):
                path = path + '_mask.nii.gz'
            else:
                index = path.rindex('.nii.gz')
                path = path[:index] + '_mask.nii.gz'
        else:
            path = self.inputs.in_file
            filename = self._out_file_filename()
            index = filename.rindex('.nii.gz')
            path = filename[:index] + '_mask.nii.gz'
        return os.path.abspath(path)
