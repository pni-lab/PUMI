# Running PUMI Pipelines on a SLURM Cluster

This tutorial will guide you through the steps of running PUMI pipelines on a SLURM cluster using the
`cluster-pipeline-executor.sh` script.

## Prerequisites

- Verify that your cluster uses SLURM and that you have access to a node for job submission.
- Ensure Git and Apptainer are available.

## Step 1: Clone PUMI repository

Clone the PUMI repository using the following command:

```bash
git clone https://github.com/pni-lab/PUMI.git
```

## Step 2: Navigate to Scripts Directory

```bash
cd PUMI/scripts
```

## Step 3: Run the Script with sbatch

The cluster-pipeline-executor.sh script will automatically generate and submit a SLURM batch job for each subject in the dataset.
While doing so, it will enforce a delay between submissions, as well as a user-bound job upper-limit, to avoid overloading the cluster.
The script will handle the job submission, resource allocation, and execution of each job.
You just have to run `sbatch cluster-pipeline-executor.sh` with a set of command-line parameters.

### Command-line Parameters

#### Mandatory Parameters

- **`-i`**: **Input Dataset (`-i`)**
  - **Description**: Path to the input dataset in BIDS format.
  - **Example**: `/path/to/input/dataset`
  - **Note**: This dataset will be processed by the pipeline.

- **`-o`**: **Output Directory (`-o`)**
  - **Description**: Path where the processed results will be saved.
  - **Example**: `/path/to/output/directory`
  - **Note**: Ensure that the output directory is writable.

- **`-t`**: **Temporary Directory (`-t`)**
  - **Description**: Path to store temporary files for each subject. This must be an absolute path within `/local/`.
  - **Example**: `/local/tmp/pumi`
  - **Note**: This directory is where temporary data will be stored during processing.

- **`-l`**: **Log Directory (`-l`)**
  - **Description**: Path to an NFS directory where log files will be stored.
  - **Example**: `/nfs/log/directory`
  - **Note**: Log files for each job will be saved in this directory.

#### Optional Parameters

- **`-p`**: **Pipeline to Run (`-p`)**
  - **Description**: Name of the PUMI pipeline to run.
  - **Example**: `rcpl.py`
  - **Default Value**: `rcpl.py`
  - **Note**: Ensure that the pipeline file exists in the `pipelines` folder of the PUMI repository.

- **`-r`**: **Nipype Plugin Params (`-r`)**
  - **Description**: Nipype plugin params.
  - **Example**: `--plugin MultiProc --memory_gb 50 --n_procs 10`
  - **Default Value**: `--plugin MultiProc --memory_gb 50 --n_procs 10`
  - **Note**: Customize this according to the resources available on your cluster.

- **`-m`**: **Maximum Jobs (`-m`)**
  - **Description**: Maximum number of jobs to run simultaneously.
  - **Example**: `10`
  - **Default Value**: `16`
  - **Note**: This ensures that no more than the specified number of jobs are running concurrently.

- **`-n`**: **Nice Value (`-n`)**
  - **Description**: The SLURM nice value for job priority. Higher values lower the job's priority.
  - **Example**: `5`
  - **Default Value**: `5`
  - **Note**: This can be useful for managing resource allocation on the cluster.

- **`-b`**: **Branch (`-b`)**
  - **Description**: The GitHub branch of PUMI to use. If you don’t need a specific branch, you can leave it as `main`.
  - **Example**: `main`
  - **Default Value**: `main`
  - **Note**: Specify the branch of the repository from which to run the pipeline.

- **`-d`**: **Submit Delay (`-d`)**
  - **Description**: Minimum delay between job submissions, in seconds. This is used to avoid submitting jobs too quickly.
  - **Example**: `72`
  - **Default Value**: `72`
  - **Note**: This helps manage job submission rates, ensuring you don’t overload the queue.

- **`-c`**: **CPUs per Task (`-c`)**
  - **Description**: The number of CPUs allocated for each task.
  - **Example**: `15`
  - **Default Value**: `15`
  - **Note**: Adjust this according to the number of CPUs you want each job to use.

- **`-s`**: **Path to Image SIF File (`-s`)**
  - **Description**: Path to the Apptainer Image (SIF file) for running the pipeline. If not provided, the script will pull the latest PUMI image and convert it to a SIF file.
  - **Example**: `/path/to/PUMI.sif`
  - **Default Value**: Not specified. If not provided, the script will pull the latest PUMI image and convert it to a SIF file.
  - **Note**: This is necessary for running the pipeline inside the container.

### Example Command

Here’s an example of how to run the script:

```bash
  sbatch cluster-pipeline-executor.sh \
    -i /path/to/input/dataset \
    -o /path/to/output/directory \
    -t /local/tmp/pumi \
    -l /nfs/log/directory \
    -p rcpl.py \
    -m 10 \
    -d 72 \
    -c 15 
```
