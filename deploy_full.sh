#!/bin/bash
# Deploy pumi in case of incrementing the major or minor version number.
# First, increment version with
# git tag <MAJOR>.<MINOR>.<PATCH>
# git push --tag
#
# Next the new full docker image must be created.
# This deploy step can't be run in CI due to insufficient cloud resources and must be run locally.
# Creates a new full docker image:
echo "* Creating docker container with ALL dependencies.."
INSTALL="`cat requirements.txt` tensorflow graphviz numpydoc nbsphinx dot2tex git+https://github.com/MIC-DKFZ/HD-BET"
neurodocker generate docker \
    --pkg-manager apt \
    --base-image debian:buster-slim \
    --install git \
    --afni method=binaries version=latest \
    --fsl version=6.0.4 \
    --ants version=2.3.4 \
    --miniconda version=latest pip_install='seaborn'\
    --yes \
    > Dockerfile

# dot2tex>=2.11.3 templateflow>=0.8.0 graphviz>=0.17 matplotlib==3.5.2 numpy>=1.21.1 scipy>=1.7.1 numpydoc>=1.1.0 nbsphinx>=0.8.6 pytest==7.1.2 nipype>=1.8.1 neurodocker==0.8.0 nilearn==0.9.1 pybids>=0.15.1 poetry>=1.1.13 poetry-dynamic-versioning>=0.17.1 pydeface>=2.0.0 seaborn>=0.11.2 scikit-learn==1.1.2 tensorflow graphviz numpydoc nbsphinx dot2tex git+https://github.com/MIC-DKFZ/HD-BET

VERSION=`git describe --tags`
VER=`git describe --tags | cut -d '.' -f 1,2` # major.minor
docker build --tag pnilab/pumi:latest --file Dockerfile .
#docker tag pnilab/pumi:latest pnilab/pumi:$VERSION
docker tag pnilab/pumi:latest pnilab/pumi:$VER

# This will log in based on already stored credentials
docker login
# This will prompt for password
#docker login -u pnilab --password-stdin

docker push pnilab/pumi:$VERSION
docker push pnilab/pumi:$VER
docker push pnilab/pumi:latest

echo "Full container successfully deployed."
echo "Re-run github action, if needed."

