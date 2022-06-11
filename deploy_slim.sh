VERSION=$1 #git describe --tags
echo "Current version (full): $VERSION"
#VER=`echo $VERSION | cut -d '.' -f 1,2` # major.minor only
VER=`echo $VERSION | awk -F'[.-]' '{print $1 "." $2 "." $3}'`
echo "Current version (major.minor.patch): $VER"
V=`echo $VERSION | awk -F'[.]' '{print $1 "." $2}'`
echo "Current version (major.minor): $V"

echo "* Pull and run the full container..."
echo "If fails: major and/or minor version number might have been incremented."
echo "In this case, make sure you run ./deploy_full.sh locally and re-run the github action."
docker run --rm -itd --name pumi-container pnilab/pumi:$V

echo "* Minify container by running all tests..."

# put fresh pumi code into the container
docker exec mkdir /PUMI/data_in
docker cp . pumi-container:/PUMI/.
docker exec pumi-container cd PUMI; poetry install

# back up fsldata
docker exec pumi-container mv /opt/fsl-6.0.4/data/standard /tmp/standard

# cmd="python3 /PUMI/tests/test_afni.py; python3 /PUMI/tests/test_fsl.py; python3 /PUMI/tests/test_ants.py"
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
docker tag pnilab/pumi-slim:latest pnilab/pumi-slim:$VER  #minor.major.patch



