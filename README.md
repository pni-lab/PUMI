```# PUMI
Laboratory for Predictive Neuroimaging - University Hospital Essen, Germany

# Cite
- Isensee F, Schell M, Tursunova I, Brugnara G, Bonekamp D, Neuberger U, Wick A, Schlemmer HP, Heiland S, Wick W, Bendszus M, Maier-Hein KH, Kickingereder P. Automated brain extraction of multi-sequence MRI using artificial neural networks. Hum Brain Mapp. 2019; 1–13. https://doi.org/10.1002/hbm.24750

# First steps for developers

## Clone this repo locally
```
git clone git@github.com:pni-lab/PUMI.git
```

## Set up dependencies
### Option A: Docker
- pull the docker image:
   - `pnilab/pumi-slim:latest`: for a slim image containing only what the current version needs
   - `pnilab/pumi:latest`: for the full image, containing everything (useful when integrating new tools, but takes long to download)
- set up your ide to work within the container

### Option B: Install dependencies locally
- FSL
- AFNI
- ANTs
- Freesurfer

## Get test dataset (optional)
```
cd data_in
export WEBDAV_USERNAME=XXXX
export WEBDAV_PASSWORD=XXXX-XXXX-XXXX-XXXX
datalad install -s git@github.com:pni-data/pumi_test_data.git pumi_test_data
datalad siblings -d pumi_test_data enable -s sciebo.sfb289
datalad get pumi_test_data/*
```
Contact the [developers](mailto:tamas.spisak@uk-essen.de) for webdab credentials.

# Coding Conventions

- name of workflow is the same as the name of the variable that holds it
- name of node is the same as the name of the variable that holds it

- qc nodes's name defines the subdir in qc; it should be: <base_wf>_qc

- avoid "batch-connects" in @PumiPipeline funcions: it is preferred that right after node (or workflow) definition all possible connect statements corresponding to the node are specified 

- for readibility, we use the signature: connect(source_node, source_field, dest_node, dest_field)
- except, in case there are multiple connections between the same pair of nodes, batch-connect should be used


- @PumiPipeline funcions' first connect statement(s) is (are) connecting to the inputspec
- @PumiPipeline funcions' last connect statement(s) is (are) connecting to the outputspec


- @PumiPipeline funcions' are minimalistic and do NO "housekeeping".