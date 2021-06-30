#!/bin/bash

dMRIdatapath=$1
bvals=$2
bvecs=$3
T1path=$4
brainmask=$5
intermediary_output_path=$6
num_streamlines=$7

mkdir ${intermediary_output_path}
cd ${intermediary_output_path}

5ttgen fsl ${T1path} 5TT.mif -premasked
#how does qsiprep get this?

mrconvert ${dMRIdatapath} DWI.mif -fslgrad ${bvecs} ${bvals} -datatype float32 -stride 0,0,0,1
#whats dis

dwi2response dhollander DWI.mif RF_WM.txt RF_GM.txt RF_CSF.txt -force
#txt files are outputs

dwi2fod msmt_csd DWI.mif RF_WM.txt WM_FODs.mif RF_GM.txt GM.mif RF_CSF.txt CSF.mif -mask ${brainmask}
#takes outputs of dwi2response

tckgen WM_FODs.mif ${num_streamlines}.tck -act 5TT.mif -backtrack -crop_at_gmwmi -seed_dynamic WM_FODs.mif -maxlength 250 -minlength 30 -select ${num_streamlines} -cutoff 0.33
#input and output are first two arguments

#tcksift2 ${num_streamlines}.tck WM_FODs.mif -act 5TT.mif -out_mu out_mu.txt -out_weights sift_weights.txt
#are all the other options part of default qsi?

tckresample -endpoints ${num_streamlines}.tck ${num_streamlines}_endpoints.tck

tckconvert ${num_streamlines}_endpoints.tck ${num_streamlines}_endpoints.vtk