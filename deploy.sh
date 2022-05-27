#docker run --rm repronim/neurodocker:0.7.0 generate docker \
#--base debian:stretch --pkg-manager apt \
#--install git nano graphviz \
#--fsl version=6.0.3 \
#--miniconda conda_install="python=3.8 pytest sphinx sphinxcontrib-napoleon" \
#pip_install="nipype pybids sphinx-rtd-theme dicom pydicom versioneer" \
#use_env="base" \
#activate=true \
#--run-bash "source activate base" \
#--user=neuro \
#--workdir /home/neuro > Dockerfile

# todo:
# - make it slimmer
# - add templateflow and nilearn

#docker run --rm repronim/neurodocker:latest generate docker \
#    --pkg-manager apt \
#    --base-image debian:buster-slim \
#    --fsl version=6.0.4 \
#    --afni method=binaries version=latest \
#    --ants version=2.3.4 \
#    > fsl604.Dockerfile

# create AFNI minified docker container
docker run --rm repronim/neurodocker:latest generate docker \
    --pkg-manager apt \
    --base-image debian:buster-slim \
    --afni method=binaries version=latest \
    > afni.Dockerfile

docker run --rm -itd --name afni-container ants:latest
# run all AFNI tests to minify