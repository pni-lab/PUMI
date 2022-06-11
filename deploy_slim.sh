echo "* Pull and run latest container..."
docker run --rm -itd --name pumi-container pnilab/pumi:latest

echo "* Minify container by running all tests..."
# cmd="python3 /PUMI/tests/test_afni.py; python3 /PUMI/tests/test_fsl.py; python3 /PUMI/tests/test_ants.py, ls  /opt/fsl-*/data/standard/"

# put fresh pumi code into the container
docker cp data_in/std pumi-container:/PUMI/data_in/std
docker cp PUMI pumi-container:/PUMI/PUMI
docker cp tests pumi-container:/PUMI/tests
docker cp examples pumi-container:/PUMI/examples
docker cp pipelines pumi-container:/PUMI/pipelines
docker cp pyproject.toml pumi-container:/PUMI/pyproject.toml
docker cp requirements.txt pumi-container:/PUMI/requirements.txt
docker cp MANIFEST.in pumi-container:/PUMI/MANIFEST.in
docker cp README.md  pumi-container:/PUMI/README.md
docker exec pumi-container pip install PUMI

# back up fsldata
docker exec pumi-container mv /opt/fsl-6.0.4/data/standard /tmp/standard

cmd="python3 /PUMI/tests/test_afni.py; python3 /PUMI/tests/test_fsl.py"
neurodocker minify \
    --container pumi-container \
    --yes \
    --dir /opt \
    "$cmd"

# put back FSL data
docker exec pumi-container mv /tmp/standard /opt/fsl-6.0.4/data/standard
# create a new Docker image using the pruned container.
docker export pumi-container | docker import - pnilab/pumi-slim:latest


