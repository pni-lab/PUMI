echo "* Pull and run latest container..."
docker run --rm -itd --name pumi-container pnilab/pumi:latest

echo "* Minify container by running all tests..."
# cmd="python3 /PUMI/tests/test_afni.py; python3 /PUMI/tests/test_fsl.py; python3 /PUMI/tests/test_ants.py, ls  /opt/fsl-*/data/standard/"

# back up fsldata
docker exec pumi-container mv /opt/fsl-6.0.4/data/standard /tmp/standard

cmd="python3 /PUMI/tests/test_afni.py; python3 /PUMI/tests/test_fsl.py done"
neurodocker minify \
    --container pumi-container \
    --yes \
    --dir /opt \
    "$cmd"

# put back FSL data
docker exec pumi-container mv /tmp/standard /opt/fsl-6.0.4/data/standard
# create a new Docker image using the pruned container.
docker export pumi-container | docker import - pnilab/pumi-slim:latest


