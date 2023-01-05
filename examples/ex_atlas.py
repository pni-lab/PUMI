from PUMI.pipelines.multimodal.atlas import *

atlas_nilearn = ['aal','destrieux','difumo','harvard_oxford','juelich','msdl','pauli','schaefer','talairach','yeo']
for name in atlas_nilearn:
    print(name)
    if name == 'harvard_oxford':
        params = {'atlas_name':'cort-maxprob-thr0-2mm'}
    elif name == 'juelich':
        params = {'atlas_name':'maxprob-thr0-2mm'}
    elif name == 'MIST':
        params = {'resolution':'122'}
    elif name == 'talairach':
        params = {'level_name':'ba'}
    elif name == 'yeo':
        params = {'key':'thin_17'}
    else:
        params = []

    if params:
        fetch_atlas(name,**params)
    else:
        fetch_atlas(name)