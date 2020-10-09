#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 15 11:56:47 2020

@author: bwinston

see https://github.com/BIDS-Apps/example/blob/master/run.py 
https://docs.python.org/3/library/argparse.html
for reference
test
"""

import argparse
import os
from glob import glob
import numpy as np
import subprocess
import numpy as np
import input_output as inout
import argparse
import decomp as dcp
import utility_functions as uts
import construct_harmonics as cs
#user inputs cl arguments separated by spaces
parser = argparse.ArgumentParser(description='Connectome Harmonic Analysis Pipeline (CHAP)')
parser.add_argument('qsi_dir', type = str, help = 'qsirecon input directory')
parser.add_argument('surf_dir', type = str, help = 'please input BIDS-organized Freesurfer output dir here')
parser.add_argument('output_dir', type = str, help = 'Output directory')
parser.add_argument('analysis_level', type = str, help = 'participant or group')
parser.add_argument('--participant_label', type = str, help = 'Participant label(s) (not including sub-). If this parameter is not provided all subjects will be analyzed. Multiple participants can be specified with a space separated list')
parser.add_argument('--fprep_dir', type = str, help = 'please input BIDS-organized fMRIprep output dir here. Functional images should be in fsnative space')
parser.add_argument('--parc', type = str, help = "path to parcellation file as vtk with %s for hem")
parser.add_argument('--number', type = str, help = 'number of evecs to compute')

args = parser.parse_args()     
#set empty dict and list
user_info = {}
subs = []
if not os.path.exists(f'{args.output_dir}/chap'):
    os.mkdir(f'{args.output_dir}/chap') #create output directory

#populate dicts with tck output files of reconstruction for each session, and {hem}.white
if args.participant_label: #user input subjects
    subs = args.participant_label.split(" ")
else: #for all subjects
    subject_dirs = glob(os.path.join(args.qsi_dir, "sub-*"))
    subs = [subject_dir.split("-")[-1] for subject_dir in subject_dirs]               
for sub in subs:
    user_info[f'{sub}_info'] = {}  #create dict in user_info for each subjs info
    os.mkdir(f'{args.output_dir}/chap/sub-{sub}') #create output subject folder
    #surface files locations
    for hem in ['rh','lh']:
            user_info[f'{sub}_info'][f'{hem}_surf'] = []
            user_info[f'{sub}_info'][f'{hem}_surf'].append(f'{args.surf_dir}/sub-{sub}/surf/{hem}.white') 
    user_info[f'{sub}_info']['streamlines'] = [] #streamlines file locations
    if args.fprep_dir:
        user_info[f'{sub}_info']['func'] = [] #functional file locations
    if 'ses' in os.listdir(f'{args.qsi_dir}/sub-{sub}')[0]: #if multiple sessions
        for ses in os.listdir(f'{args.qsi_dir}/sub-{sub}'): 
            if 'ses' in ses:
                os.mkdir(f'{args.output_dir}/chap/sub-{sub}/{ses}') #create output session folders
                for file in os.listdir(f'{args.qsi_dir}/sub-{sub}/{ses}/dwi'):
                    if 'tck' in file:
                        user_info[f'{sub}_info']['streamlines'].append([ses, file]) #streamlines list with each session's .tck
                if args.fprep_dir:
                    for file in os.listdir(f'{args.fprep_dir}/sub-{sub}/{ses}/func'):
                        for hem in ['L','R']:
                            if f'space-fsnative_hemi-{hem}_bold.func.gii' in file:
                                user_info[f'{sub}_info']['func'].append([ses, file]) #functional file locations               
    else: #if sub has just one session
        #os.mkdir(f'{args.output_dir}/chap/sub-{sub}/ses')
        for file in os.listdir(f'{args.qsi_dir}/sub-{sub}/dwi'):
            if 'tck' in file:
                user_info[f'{sub}_info']['streamlines'].append([file])
        if args.fprep_dir:
            for file in os.listdir(f'{args.fprep_dir}/sub-{sub}/func'):
                        for hem in ['L','R']:
                            if f'space-fsnative_hemi-{hem}_bold.func.gii' in file:
                                user_info[f'{sub}_info']['func'].append(file) #functional file locations
  #NEED TO MAKE ALL OF BELOW WORK FOR PEOPLE WITH JUST ONE SESSION (I.E. NO SES FOLDER)  
    multises = any('ses' in x for x in user_info[f'{sub}_info']['streamlines']) #check whether multiple sessions, set output var
    if multises:
        for ses, file in user_info[f'{sub}_info']['streamlines']:
            #convert streamlines to .vtk using mrtrix
            cs.construct_harmonics_calculate_spectra(args.output_dir, file, ses+'/')      
    else: 
        file =  user_info[f'{sub}_info']['streamlines'][0]
        cs.construct_harmonics_calculate_spectra(args.output_dir, file)
        





'''
run config
/Users/bwinston/Documents/fMRI/BIDS/test/qsirecon /Users/bwinston/Documents/fMRI/BIDS/test/freesurfer /Users/bwinston/Documents/fMRI/BIDS/test/output/ participant

'''


















