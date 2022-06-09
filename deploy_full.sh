echo "* Creating docker container with ALL dependencies.."
neurodocker generate docker \
    --pkg-manager apt \
    --base-image debian:buster-slim \
    --install git \
    --afni method=binaries version=latest \
    --fsl version=6.0.4 \
    --ants version=2.3.4 \
    --copy data_in/pumi-minitest /PUMI/data_in/pumi-minitest \
    --copy data_in/std /PUMI/data_in/std \
    --copy PUMI /PUMI/PUMI \
    --copy tests /PUMI/tests \
    --copy pipelines /PUMI/pipelines \
    --copy pyproject.toml /PUMI/. \
    --copy requirements.txt /PUMI/. \
    --copy MANIFEST.in /PUMI/. \
    --copy README.md /PUMI/. \
    --run "mkdir /PUMI/data_out" \
    --miniconda version=latest pip_install='/PUMI/. git+https://github.com/MIC-DKFZ/HD-BET' \
    --yes \
    > pumi.Dockerfile

docker build --tag pumi:latest --file pumi.Dockerfile .

echo "* Run container..."
docker run --rm -itd --name pumi-container pumi:latest

echo "* Minify container by running all tests..."
# cmd="python3 /PUMI/tests/test_afni.py; python3 /PUMI/tests/test_fsl.py; python3 /PUMI/tests/test_ants.py, ls  /opt/fsl-*/data/standard/"
cmd="python3 /PUMI/tests/test_afni.py; python3 /PUMI/tests/test_fsl.py; ls  /opt/fsl-*/data/standard/"
neurodocker minify \
    --container pumi-container \
    --yes \
    --dir /opt \
    "$cmd"
# create a new Docker image using the pruned container.
docker export pumi-container | docker import - pumi-slim:latest
