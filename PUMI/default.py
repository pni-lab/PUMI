import os

_FSLDIR_ = os.environ['FSLDIR']

class _RegType_:
    FSL = 1
    ANTS = 2

_regType_ = _RegType_.ANTS

# Reference volume for motion correction
class _RefVolPos_:
    first=1
    middle=2
    last=3

#reference resolution could be changed here
_brainref="/data/standard/MNI152_T1_1mm_brain.nii.gz"
_headref="/data/standard/MNI152_T1_1mm.nii.gz"
_brainref_mask="/data/standard/MNI152_T1_1mm_brain_mask_dil.nii.gz"