from PUMI.pipelines.multimodal.atlas import *

atlas_nilearn = ['aal','allen','basc','destrieux','difumo','harvard_oxford','juelich','msdl','pauli','schaefer','surf_destrieux','talairach','yeo']

for name in atlas_nilearn:
    #print(name)
    params = {}
    args = []
    if name == 'basc':
        args = ('122',)
    elif name == 'harvard_oxford':
        params = {'atlas_name':'sub-maxprob-thr0-2mm','symmetric_split':'True'}
    elif name == 'juelich':
        params = {'atlas_name':'maxprob-thr0-2mm'}
    elif name == 'talairach':
        params = {'level_name':'ba'}
    elif name == 'pauli':
        params = {'version': 'det'}
    elif name == 'surf_destrieux':
        args = ('left',)
    elif name == 'yeo':
        args = ('thin_17',)

    #fetch_atlas(name,*args,**params)

from PUMI.pipelines.func.timeseries_extractor import fetch_atlas_module

#fetch_atlas_wf = fetch_atlas_module('fetch_atlas_wf')
#fetch_atlas_wf.get_node('inputspec').inputs.name_atlas = 'harvard_oxford'
#fetch_atlas_wf.get_node('inputspec').inputs.atlas_params = {'atlas_name':'sub-maxprob-thr0-2mm','symmetric_split':'True'}

#fetch_atlas_wf.run()

fetch_atlas_wf = fetch_atlas_module('fetch_atlas_wf')
fetch_atlas_wf.get_node('inputspec').inputs.name_atlas = 'yeo'
fetch_atlas_wf.get_node('inputspec').inputs.atlas_args = ('thin_7',)
fetch_atlas_wf.get_node('inputspec').inputs.atlas_params = {}


fetch_atlas_wf.run()