from PUMI.pipelines.multimodal.atlas import atlas_selection

atlas_selection_wf = atlas_selection('atlas_selection_wf',modularize=True, module_threshold=0.0)
atlas_selection_wf.get_node('inputspec').inputs.atlas = 'allen'
atlas_selection_wf.get_node('inputspec').inputs.atlas_params = {}
atlas_selection_wf.get_node('inputspec').inputs.labelmap_params = ()
atlas_selection_wf.get_node('inputspec').inputs.modules_atlas = 'basc'
atlas_selection_wf.get_node('inputspec').inputs.modules_params = {}
atlas_selection_wf.get_node('inputspec').inputs.modules_labelmap_params = ('7',)

atlas_selection_wf.run()