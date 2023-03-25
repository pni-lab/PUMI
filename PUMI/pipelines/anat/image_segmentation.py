import subprocess
import os


# Performes segmentation for the subjects (1, 2, 3)
for i in range(1, 4):
    # Rmember to correct paths if needed
    ROOT_DIR   = os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd())))
    input_dir  = os.path.join(ROOT_DIR, "data_in/dw_dataset")
    input_img  = os.path.join(input_dir, "sub-000{}/anat/sub-000{}_T1w.nii.gz".format(i, i))
    output_dir = os.path.join(ROOT_DIR, "data_out/derivatives/ImgSegmentation")


    # Set FreeSurfer Path (It is needed by FastSurfer
    FreeSurfer_dir = "/home/mo/freesurfer"
    setFrSPath_cmd = "export FREESURFER_HOME=" + FreeSurfer_dir

    # Executes commands/functions from a file in the current shell enviroment so that it can be used by next commands
    source_Fs = "$source $FREESURFER_HOME/SetUpFreeSurfer.sh"




    # Set FastSurfer Path
    FastSurfer_dir = "/home/mo/FastSurfer"
    setFsPath_cmd  = "export FASTSURFER_HOME=" + FastSurfer_dir




    # run_fastsurfer includes all commands needed for the segmentation
    pathToRunFile = FastSurfer_dir + "/run_fastsurfer.sh"


    command =  setFrSPath_cmd + ";" + source_Fs + ";" \
               + setFsPath_cmd + ";" + pathToRunFile  \
               + " --t1 " + input_img \
               + " --sd " + output_dir \
               + " --sid " + str(i)


    # run the command
    output = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)

    # Print output
    print(output.stdout)


    # Print Error Message
    print(output.stderr)


