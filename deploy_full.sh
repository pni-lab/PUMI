echo "* Creating docker container with ALL dependencies.."
neurodocker generate docker \
    --pkg-manager apt \
    --base-image debian:buster-slim \
    --install git \
    --afni method=binaries version=latest \
    --fsl version=6.0.4 \
    --ants version=2.3.4 \
#    --copy data_in/pumi-minitest /PUMI/data_in/pumi-minitest \
#    --copy data_in/std /PUMI/data_in/std \
#    --copy PUMI /PUMI/PUMI \
#    --copy tests /PUMI/tests \
#    --copy pipelines /PUMI/pipelines \
#    --copy pyproject.toml /PUMI/. \
#    --copy requirements.txt /PUMI/. \
#    --copy MANIFEST.in /PUMI/. \
#    --copy README.md /PUMI/. \
    --run "mkdir -p /PUMI/data_out" \
    --miniconda version=latest pip_install='tensorflow graphviz numpydoc nbsphinx dot2tex git+https://github.com/MIC-DKFZ/HD-BET' \
    --yes \
    > Dockerfile

docker build --tag pumi:latest --file pumi.Dockerfile .

echo "* Deploy slim container..."
./deploy_slim.py

