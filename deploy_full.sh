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
neurodocker generate docker \
    --pkg-manager apt \
    --base-image debian:buster-slim \
    --install git \
    --afni method=binaries version=latest \
    --fsl version=6.0.4 \
    --ants version=2.3.4 \
    --run "mkdir -p /PUMI/data_out" \
    --miniconda version=latest pip_install='poetry tensorflow graphviz numpydoc nbsphinx dot2tex git+https://github.com/MIC-DKFZ/HD-BET' \
    --yes \
    > Dockerfile

VERSION=`git describe --tags`
VER=`git describe --tags | cut -d '.' -f 1,2` # major.minor
docker build --tag pnilab/pumi:latest --file Dockerfile .
docker tag pnilab/pumi:latest pnilab/pumi:$VERSION
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

