from PUMI.pipelines.multimodal.atlas import *

atlas_nilearn = ['aal','destrieux','difumo','harvard_oxford','juelich','msdl','pauli','schaefer','talairach','yeo']
for name in atlas_nilearn:
    print(name)
    if name == 'harvard_oxford':
        name = [name, 'cort-maxprob-thr0-2mm']
    elif name == 'juelich':
        name = [name, 'maxprob-thr0-2mm']
    elif name == 'MIST':
        name = [name,'122']
    elif name == 'talairach':
        name = [name,'lobe']
    elif name == 'yeo':
        name = [name,'thin_17']
    else:
        name = [name]
    fetch_atlas(name)
print ('nilearn atlases: Done')

fetch_atlas(['MIST'])
print ('MIST atlas: Done')