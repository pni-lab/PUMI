# PUMI
Laboratory for Predictive Neuroimaging - University Hospital Essen, Germany

#### Status
![GitHub](https://img.shields.io/github/license/pni-lab/pumi?color=green&logo=%23F68212)
![GitHub repo size](https://img.shields.io/github/repo-size/pni-lab/pumi)
![Lines of code](https://img.shields.io/tokei/lines/github/pni-lab/pumi)
![GitHub last commit](https://img.shields.io/github/last-commit/pni-lab/pumi)
![GitHub Workflow Status](https://img.shields.io/github/workflow/status/pni-lab/PUMI/test_and_dockerize?logo=%232088FF)
![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/pni-lab/pumi?label=latest%20tag)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/pni-lab/PUMI)

#### Docker
[![Docker Image Version (latest semver)](https://img.shields.io/docker/v/pnilab/pumi?color=blue&label=pnilab%2Fpumi%3A&logo=docker&sort=semver)](https://hub.docker.com/repository/docker/pnilab/pumi)
![Docker Image Size (latest semver)](https://img.shields.io/docker/image-size/pnilab/pumi?label=%20pnilab%2Fpumi&logo=docker&sort=semver)

[![Docker Image Version (latest semver)](https://img.shields.io/docker/v/pnilab/pumi-slim?color=blue&label=pnilab%2Fpumi-slim%3A&logo=docker&sort=semver)](https://hub.docker.com/repository/docker/pnilab/pumi-slim)
![Docker Image Size (latest semver)](https://img.shields.io/docker/image-size/pnilab/pumi-slim?label=%20pnilab%2Fpumi-slim&logo=docker&sort=semver)

#### Issues
[![GitHub issues](https://img.shields.io/github/issues-raw/pni-lab/pumi?color=red&logo=github)](https://GitHub.com/pni-lab/PUMI/issues/)
[![GitHub closed issues](https://img.shields.io/github/issues-closed-raw/pni-lab/pumi?color=green&logo=github)](https://GitHub.com/pni-lab/PUMI/issues?q=is%3Aissue+is%3Aclosed)

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
- set up your IDe to work within the container

### Option B: Install all non-python dependencies locally
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
Contact the [developers](mailto:tamas.spisak@uk-essen.de) for webdav credentials.

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

# Version incrementing rules

- increment major if:
  - reverse-compatibility is broken
  - a substantial set of new features are added or a grand milestone is reached in the development
- increment minor if:
   - the running environment must be changed, i.e. when the docker image pnilab/pumi has been changed
   - new feature is added (e.g. a new preprocessing step is integrated)
- increment patch for smaller patches, e.g.:  
   - changes in existing behavior (new parameter, params renamed)
   - bugfixes
   - typically after merging a pull request


## Caution:
Reverse compatibility will not be guaranteed until the major version reaches 1


## Incrementing major or minor version:
- commit the changes
- tag the commit, deploy the new full docker image locally, push the tag:
```
git tag <MAJOR>.<MINOR>.<PATCH>
./deploy_full.sh # creates the new full docker image
git push --tag
```
- push to your branch
- open PR 
A github action automatically creates the new slim docker image.

## Incrementing patch version:
- commit the changes
- tag the commit, push the tag
```
git tag <MAJOR>.<MINOR>.<PATCH>
git push --tag
```
- push to your branch
- open PR 
A github action automatically creates the new slim docker image.

# Cite

## Nipype
- Gorgolewski K, Burns CD, Madison C, Clark D, Halchenko YO, Waskom ML, Ghosh SS. (2011). Nipype: a flexible, lightweight and extensible neuroimaging data processing framework in Python. Front. Neuroinform. 5:13.

## FSL
- M.W. Woolrich, S. Jbabdi, B. Patenaude, M. Chappell, S. Makni, T. Behrens, C. Beckmann, M. Jenkinson, S.M. Smith. Bayesian analysis of neuroimaging data in FSL. NeuroImage, 45:S173-86, 2009

- S.M. Smith, M. Jenkinson, M.W. Woolrich, C.F. Beckmann, T.E.J. Behrens, H. Johansen-Berg, P.R. Bannister, M. De Luca, I. Drobnjak, D.E. Flitney, R. Niazy, J. Saunders, J. Vickers, Y. Zhang, N. De Stefano, J.M. Brady, and P.M. Matthews. Advances in functional and structural MR image analysis and implementation as FSL. NeuroImage, 23(S1):208-19, 2004 

- M. Jenkinson, C.F. Beckmann, T.E. Behrens, M.W. Woolrich, S.M. Smith. FSL. NeuroImage, 62:782-90, 2012

## ANTs
- Tustison NJ, Cook PA, Klein A, Song G, Das SR, Duda JT, Kandel BM, van Strien N, Stone JR, Gee JC, Avants BB. Large-scale evaluation of ANTs and FreeSurfer cortical thickness measurements. Neuroimage. 2014 Oct 1;99:166-79. doi: 10.1016/j.neuroimage.2014.05.044. Epub 2014 May 29. PMID: 24879923.

- Avants BB, Tustison NJ, Stauffer M, Song G, Wu B, Gee JC. The Insight ToolKit image registration framework. Front Neuroinform. 2014 Apr 28;8:44. doi: 10.3389/fninf.2014.00044. PMID: 24817849; PMCID: PMC4009425.

- Avants BB, Tustison NJ, Wu J, Cook PA, Gee JC. An open source multivariate framework for n-tissue segmentation with evaluation on public data. Neuroinformatics. 2011 Dec;9(4):381-400. doi: 10.1007/s12021-011-9109-y. PMID: 21373993; PMCID: PMC3297199.

## AFNI
- Cox RW, Jesmanowicz A (1999). Real-time 3D image registration for functional MRI.  Magnetic Resonance in Medicine, 42: 1014-1018.

- Glen DR, Taylor PA, Buchsbaum BR, Cox RW, Reynolds RC (2020). Beware (Surprisingly Common) Left-Right Flips in Your MRI Data: An Efficient and Robust Method to Check MRI Dataset Consistency Using AFNI. Front. Neuroinformatics 14. doi.org/10.3389/fninf.2020.00018

- Taylor PA, Chen G, Glen DR, Rajendra JK, Reynolds RC, Cox RW (2018).  FMRI processing with AFNI: Some comments and corrections on ‘Exploring the Impact of Analysis Software on Task fMRI Results’. bioRxiv 308643; doi:10.1101/308643

- Jo HJ, Saad ZS, Simmons WK, Milbury LA, Cox RW. Mapping sources of correlation in resting state FMRI, with artifact detection and removal. Neuroimage. 2010;52(2):571-582. doi:10.1016/j.neuroimage.2010.04.246

## HD-BET
- Isensee F, Schell M, Tursunova I, Brugnara G, Bonekamp D, Neuberger U, Wick A, Schlemmer HP, Heiland S, Wick W, Bendszus M, Maier-Hein KH, Kickingereder P. Automated brain extraction of multi-sequence MRI using artificial neural networks. Hum Brain Mapp. 2019; 1–13. https://doi.org/10.1002/hbm.24750

## pydeface
- Omer Faruk Gulban, Dylan Nielson, Russ Poldrack, john lee, Chris Gorgolewski, Vanessasaurus, & Satrajit Ghosh. (2019). poldracklab/pydeface: v2.0.0 (v2.0.0). Zenodo. https://doi.org/10.5281/zenodo.3524401

## Templateflow
- TemplateFlow: a community archive of imaging templates and atlases for improved consistency in neuroimaging R Ciric, R Lorenz, WH Thompson, M Goncalves, E MacNicol, CJ Markiewicz, YO Halchenko, SS Ghosh, KJ Gorgolewski, RA Poldrack, O Esteban bioRxiv 2021.02.10.430678; doi:  10.1101/2021.02.10.430678 
=======
