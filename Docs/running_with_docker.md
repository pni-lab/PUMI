# Running PUMI pipelines in a docker container

If you are looking for an easy way to run a PUMI pipeline, using our Docker container is
the recommended solution!

In this tutorial, we will guide you step-by-step through the process of running a PUMI pipeline in a
Docker container on Ubuntu 22.04 LTS. Please note that while we have only tested this on Ubuntu 22.04
LTS, it may work on other operating systems, but we cannot guarantee it.

Now, let's dive into the steps for running a pipeline in a Docker container on Ubuntu:

## Step 0: Preparation

Before starting, you need to make sure that you have Docker and Git installed on your system.

## Step 1: **Get a copy of the PUMI source code**

To get started, you need to obtain the PUMI source code.

You can either clone the PUMI source code from the [official PUMI GitHub page](https://github.com/pni-lab/PUMI)
with the terminal command

```
git clone https://github.com/pni-lab/PUMI.git
```

or you can manually download it from the [official PUMI GitHub page](https://github.com/pni-lab/PUMI). 


## Step 2: Go into the scripts directory:

Next, if not already done, open a terminal. Now, navigate into the directory called '**scripts**'.

If you used the terminal command to get PUMI, you can run the following command in the same terminal to navigate into
the scripts directory: ```cd PUMI/scrips/```

## Step 3: Start pipeline execution

To start running a PUMI pipeline, you need to execute the docker-pipeline-executor with the appropriate parameters.
Depending on your use-case, you can either run the pipeline on local storage or on an NFS share.

### Using local storage

If you want to run the pipeline on locally stored data on all subjects, use the following scheme:

```
./docker-pipeline-executor \
-v <path-to-PUMI-root-directory> \
-i <input-dataset> \
-o <output-directory> \
<pipeline-name>
```

To run the pipeline on specific subjects only, use the 'participant_label' argument after '<pipeline-name>', like this:

```
./docker-pipeline-executor \
-v <path-to-PUMI-root-directory> \
-i <input-dataset> \
-o <output-directory> \
<pipeline-name> \
--participant_label <subject-id-1> <...> <subject-id-n> 
```

Here is an example command that runs the 'example-bids-app.py' pipeline on subject 001 of the 'pumi-unittest'
dataset located in the 'data_in' directory and stores the data in 'data_out/my_pumi_output' (both directories are
inside the PUMI directory):

```
./docker-pipeline-executor \
-v .. \
-i ../data_in/pumi-unittest \
-o ../data_out/my_pumi_output \
example-bids-app.py \
--participant_label 001 
```

### Running on an NFS share

If you want to run calculations on an NFS share (e.g. because you work on a cluster that handles storage like that) you
need to supply the root directory of the NFS share with the -n argument.

**CAUTION: The PUMI source code, the input dataset and the output directory needs to be on the NFS share!**

```
./docker-pipeline-executor \
-n <path-to-NFS-root-directory> \
-v <path-to-PUMI-root-directory> \
-i <input-dataset> \
-o <output-directory> \
<pipeline-name>
```

To run the pipeline on specific subjects, use the following command:

```
./docker-pipeline-executor \
-n <path-to-NFS-root-directory> \
-v <path-to-PUMI-root-directory> \
-i <input-dataset> \
-o <output-directory> \
<pipeline-name>
--participant_label <subject-id-1> <...> <subject-id-n> 
```

If you want to run the 'example-bids-app.py' pipeline on subjects 001, 002, and 003 of a (theoretical) dataset
'/mnt/myNFS/datasets/ds-1' located on a (theoretical) NFS share with the root directory '/mnt/myNFS'.

**Make sure that the PUMI source code, input dataset, and output directory are located on the same NFS share!**

```
./docker-pipeline-executor \
-v .. \
-n /mnt/myNFS \
-i /mnt/myNFS/datasets/ds-1/ \
-o /mnt/myNFS/output/ \
example-bids-app.py \
--participant_label 001 002 003
```
