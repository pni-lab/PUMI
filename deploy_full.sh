echo "* Creating docker container with ALL dependencies.."
neurodocker generate docker \
    --pkg-manager apt \
    --base-image debian:buster-slim \
    --install git \
    --afni method=binaries version=latest \
    --fsl version=6.0.4 \
    --ants version=2.3.4 \
    --run "mkdir -p /PUMI/data_out" \
    --miniconda version=latest pip_install='tensorflow graphviz numpydoc nbsphinx dot2tex git+https://github.com/MIC-DKFZ/HD-BET' \
    --yes \
    > Dockerfile

docker build --tag pumi:latest --file Dockerfile .

echo "* Deploy slim container..."
./deploy_slim.py

