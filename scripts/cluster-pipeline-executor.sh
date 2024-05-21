#!/bin/bash
#SBATCH --time=336:00:00

### DEFAULT VALUES (MIGHT GET OVERRIDDEN BY USER CLI INPUT) ###
PIPELINE="rcpl.py"
RESOURCES="--plugin MultiProc --memory_gb 50 --n_procs 10"
MAX_JOBS=16
NICE=5
BRANCH='main'
SUBMIT_DELAY=72
CPUS_PER_TASK=15
################################################################


while getopts 'i:o:t:l:p:r:m:n:b:d:c:s:h' opt; do
  case "$opt" in
    i) INDIR="$OPTARG";;
    o) OUTDIR="$OPTARG";;
    t) TMP_PUMI="$OPTARG";;
    l) LOG_PATH="$OPTARG";;
    p) PIPELINE="$OPTARG";;
    r) RESOURCES="$OPTARG";;
    m) MAX_JOBS="$OPTARG";;
    n) NICE="$OPTARG";;
    b) BRANCH="$OPTARG";;
    d) SUBMIT_DELAY="$OPTARG";;
    c) CPUS_PER_TASK="$OPTARG";;
    s) SIF_PATH="$OPTARG";;

    ?|h)
      echo "-i      Input BIDS dataset"
      echo "-o      Derivatives dir (i.e., where to store the results)"
      echo "-t      Where to store temporary PUMI workflow files on the worker nodes (MUST BE an absolute path somewhere in /local/)"
      echo "-l      NFS directory that should be used to store the Slurm log files (+ Apptainer SIF file)"
      echo "-p      PUMI pipeline you want to run (default: '${PIPELINE}')"
      echo "-r      Nipype plugin params to limit resource usage (default: '${RESOURCES}')"
      echo "-m      Maximum amount of jobs that you want to have running at a time (default: '${MAX_JOBS}')"
      echo "-n      Slurm nice value. The higher the nice value, the lower the priority! (default: '${NICE}')"
      echo "-b      Which PUMI GitHub branch to install (default: '${BRANCH}')"
      echo "-d      Minimum delay between submission of jobs in seconds (default: '${SUBMIT_DELAY}')"
      echo "-c      CPU's per task (default: '${CPUS_PER_TASK}')"
      echo "-s      Path to Image SIF file. If not provided, pull and convert latest docker image."
      exit 1
      ;;
  esac
done
shift "$(($OPTIND -1))"

echo "--------------------------------------------------------------------"
echo "Input  (-i): ${INDIR}"
echo "Derivatives output (-o): ${OUTDIR}"
echo "Temporary PUMI path (-t): ${TMP_PUMI}"
echo "NFS log directory (-l): ${LOG_PATH}"
echo "Selected pipeline (-p): ${PIPELINE}"
echo "Resource parameters (-r): ${RESOURCES}"
echo "Max Slurm jobs of user (-m): ${MAX_JOBS}"
echo "Slurm nice value (-n): ${NICE}"
echo "PUMI branch to use (-b): ${BRANCH}"
echo "Minimum delay between submission of jobs in seconds (-d): ${SUBMIT_DELAY}"
echo "Path to Image SIF file (-s): ${SIF_PATH}"
echo "--------------------------------------------------------------------"

# Validation to ensure mandatory options are provided.
# If not, the script exits with an error message.
if [ -z "${INDIR}" ] || [ -z "${OUTDIR}" ] || [ -z "${TMP_PUMI}" ] || [ -z "${LOG_PATH}" ]; then
  echo "Error: Options -i, -o, -t and -l must be provided!"
  echo "You can call this software with the -h option to get information regarding the available options."
  exit 1
fi

if [[ "${TMP_PUMI}" == /local/* ]];
then
  echo "-t was specified to a sub-directory in /local. Great!"
else
  echo "Error: -t must be set to a sub-directory in /local/"
  exit 1

fi

############################# Main script begins here #########################################

dataset_name=$(basename "$INDIR")
mkdir -p "jobs_scripts/${dataset_name}"  # Create directory which will contain the slurm job batch scripts

mkdir -p "${LOG_PATH}"  # Create directory where the jobs will store the slurm outputs in

if [ -z "${SIF_PATH}" ]; then
  rm -rf ${TMP_PUMI}/apptainer_cache/
  mkdir -p ${TMP_PUMI}/apptainer_cache/
  # Pull (and convert) PUMI image locally and then copy to NFS share where all the jobs can copy it from
  APPTAINER_CACHEDIR=${TMP_PUMI}/apptainer_cache/ apptainer pull ${TMP_PUMI}/PUMI.sif docker://pnilab/pumi:latest
  cp ${TMP_PUMI}/PUMI.sif ${LOG_PATH}/PUMI.sif
  rm -rf ${TMP_PUMI}
  SIF_PATH=${LOG_PATH}/PUMI.sif
else
  echo "SIF was already provided. No pulling and conversion needed."
fi

mkdir -p "${OUTDIR}"

dataset_description_path="${INDIR}/dataset_description.json"  # Every sub-dataset (containing only one subject) still needs a dataset_description.json

# Iterate over each subject in the BIDS dataset
for subject_folder in ${INDIR}/sub-*; do

    subject_id=$(basename "$subject_folder")
    job_path="jobs_scripts/${dataset_name}/job_${subject_id}.sh"

    cat << EOF > "${job_path}"
#!/bin/bash
#SBATCH --job-name=${subject_id}_${dataset_name}
#SBATCH --time=3:00:00
#SBATCH --nice=${NICE}
#SBATCH --output="${LOG_PATH}/${subject_id}.out"
#SBATCH --cpus-per-task ${CPUS_PER_TASK}

echo "*************************************************************"
echo "Starting on \$(hostname) at \$(date +"%T")"
echo "*************************************************************"

subject_dir="${TMP_PUMI}/${subject_id}"

subject_data_in="\${subject_dir}/input/" # Create temporary directory which stores BIDS data for one subject
rm -rf "\${subject_data_in}"
mkdir -p "\${subject_data_in}"

subject_data_out="\${subject_dir}/output/" # Create temporary directory which stores derivatives for one subject
rm -rf "\${subject_data_out}"
mkdir -p "\${subject_data_out}"

subject_tmp="\${subject_dir}/tmp/" # Create temporary directory which stores derivatives for one subject
rm -rf "\${subject_tmp}"
mkdir -p "\${subject_tmp}"

rsync -a --copy-links "${subject_folder}" "\${subject_data_in}"
rsync -a --copy-links "${dataset_description_path}" "\${subject_data_in}"  # Every valid BIDS dataset must contain description (otherwise Nipype raises BIDSValidationError)

pumi_dir="\${subject_dir}/PUMI/"
rm -rf \${pumi_dir}
mkdir -p \${pumi_dir}  # Create folder in which we clone PUMI into (and parent folders if necessary)

apptainer_image_dir="\${subject_dir}/apptainer_image/"
apptainer_image="\${apptainer_image_dir}/PUMI.sif"
mkdir -p "\${apptainer_image_dir}"
cp ${SIF_PATH} "\${apptainer_image}"

subject_apptainer_cache_dir="\${subject_dir}/apptainer_app_cache/"
rm -rf \${subject_apptainer_cache_dir}
mkdir -p \${subject_apptainer_cache_dir}

APPTAINER_CACHEDIR=\${subject_apptainer_cache_dir} \
apptainer exec \
--writable-tmpfs \
\${apptainer_image} \
bash -c " \
set -x; \
git clone -b ${BRANCH} https://github.com/pni-lab/PUMI \${pumi_dir}; \
source activate base;
pip install -e \${pumi_dir} --no-cache-dir; \
python3 \${pumi_dir}/pipelines/${PIPELINE} \
${RESOURCES} \
--working_dir \${subject_tmp} \
--bids_dir=\${subject_data_in} \
--output_dir=\${subject_data_out} "

echo "******************** SUBJECT TMP TREE ****************************"
tree \${subject_tmp}
echo "***************************************************************"
echo ""
echo "******************** SUBJECT DATA OUT TREE ****************************"
tree \${subject_data_out}
echo "***********************************************************************"

# Move results to the output directory
cp -vr \${subject_data_out}/* ${OUTDIR}/


# Remove (most) files from cluster
rm -rf "\${subject_dir}"

echo "*************************************************************"
echo "Ended on \$(hostname) at \$(date +"%T")"
echo "*************************************************************"

EOF

    while true; do
        job_count=$(squeue -u "$USER" -h | wc -l)

        if [ ${job_count} -lt ${MAX_JOBS} ]; then
            echo "Number of jobs (${job_count}) is below the limit (${MAX_JOBS}). Submitting job..."
            break
        else
            echo "Waiting. Current job count: ${job_count}. Limit is ${MAX_JOBS}."
            sleep 80  # Wait some time before checking again
        fi
    done

    sbatch ${job_path}
    sleep ${SUBMIT_DELAY}  # Do not spawn jobs very fast, even if the amount of jobs is not exceeding the limit

done

echo "--------------------------------------------------------------------"
echo "Last job script was submitted..."
echo "--------------------------------------------------------------------"
