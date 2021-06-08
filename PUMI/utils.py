import os
from nipype import Function

def get_reference(wf, ref):
    # ref should be either 'head', 'brain' or 'brain_mask'
    if ref.lower() in ['brain', 'brain_mask', 'head']:
        path = wf.cfg_parser.get('REFERENCES', ref.lower())
        if path.startswith('/'):
            return path
        else:
            return os.path.join(os.environ['FSLDIR'], path)
    else:
        raise ValueError("Can only provide references for 'head', 'brain', 'brain_mask'")


def vol_id(in_file, ref_vol='last', raise_exception=False):
    # todo: really just for func??
    import nibabel
    image = nibabel.load(in_file)
    header = image.get_header()
    shape = header.get_data_shape()

    if len(shape) != 4 and raise_exception:
        raise TypeError('Input nifti file: %s is not a 4D file' % in_file)
    elif len(shape) != 4:
        print('''Input nifti file %s is not a 4D file, but raise_exception=False.
                 Return last slice of the func run''' % in_file)
        return 0

    numb_of_volumes = int(header.get_data_shape()[3])
    if ref_vol == 'first':
        vol_id = numb_of_volumes - 1
    elif ref_vol == 'middle':
        vol_id = int(round(numb_of_volumes/2))
    elif ref_vol == 'last':
        vol_id = 0  # todo: why is 0 the last slice??
    else:
        raise ValueError('''Can only provide the ID for the first, middle and last image.
                         %s is not a valid parameter for ref_vol''', ref_vol)
    return vol_id
