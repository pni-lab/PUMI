from PUMI.engine import BidsPipeline, BidsApp
from PUMI.pipelines.anat.segmentation import bet_fsl

@BidsPipeline(output_query={
    'T1w': dict(
        datatype='anat',
        extension=['nii', 'nii.gz']
    )
})
def bet_wf(wf, fmri=True, **kwargs):
    brain_extraction = bet_fsl('brain_extraction', fmri=fmri)
    wf.connect('inputspec', 'T1w', brain_extraction, 'in_file')
    #wf.write_graph('bet_wf.png')

"""

# You could also use it like this:

brain_extraction_app = BidsApp(
    pipeline=bet_wf,  # bet_wf is not an object! It's the name of the workflow-creating-method
    name='brain_extraction',  # Node-name of the workflow-object of specified pipeline that will be internally created
    bids_dir='../data_in/pumi-unittest/',  # Root directory of the BIDS-compliant input dataset
    output_dir='../data_out/example-bids-app/',  # Directory where the results will be stored
    analysis_level='participant',  # Level of the analysis that will be performed
    participant_label=None,  # List of participant-label(s) (e.g. "001 002 003") on which pipeline is done (None -> all)
    version=True,  # Activate/Deactivate print of PUMI-version
    working_dir='.',  # Directory where temporary data will be stored
).run()
"""

brain_extraction_app = BidsApp(
    pipeline=bet_wf,  # bet_wf is not an object! It's the name of the workflow-creating-method
    name='brain_extraction',  # Node-name of the workflow-object of specified pipeline that will be internally created
    bids_dir='../data_in/pumi-unittest/'  # Root directory of the BIDS-compliant input dataset
)
brain_extraction_app.parser.add_argument('--fmri', choices=[True, False], default=False)
brain_extraction_app.run()

