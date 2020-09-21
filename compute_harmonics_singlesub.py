#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

@author: patricktaylor
"""
import numpy as np
import input_output as inout
import matrix_methods as mm
import argparse
import decomp as dcp
import utility_functions as uts
#import os

parser=argparse.ArgumentParser()
parser.add_argument('-e', '--endpoints', help='path to streamline endpoints .vtk file')
parser.add_argument('-s','--surface',help='path to surface as vtk or gii with %s for hemisphere')
parser.add_argument('-o','--outputvecs',help='path to output vector/ vals file')
parser.add_argument('-v','--savevis',help='save evecs to surface, if used, give path to output vtk')
parser.add_argument('-p','--parc',help="path to parcellation file as vtk with %s for hem")
parser.add_argument('-n', '--number', help='number of evecs to compute')

args = parser.parse_args()
surfpath=args.surface
if surfpath.endswith('.vtk'):
    sc,si=inout.read_vtk_surface_both_hem(surfpath % 'lh',surfpath % 'rh')
else:
    sc,si=inout.read_gifti_surface_both_hem(surfpath % 'lh', surfpath % 'rh')

ec=inout.read_streamline_endpoints(args.endpoints)

surf_mat=mm.construct_surface_matrix(sc,si)

ihc_mat=mm.construct_inter_hemi_matrix(sc,tol=3)

struc_conn_mat=mm.construct_structural_connectivity_matrix(sc,ec,tol=3,NNnum=45)

mask=inout.generate_mask_from_parc(args.parc % 'lh', args.parc % 'rh')

masked_mat = uts.mask_connectivity_matrix(surf_mat+ihc_mat+struc_conn_mat,mask)

vals,vecs=dcp.lapDecomp(masked_mat,args.number)

np.save(args.outputvecs,[vals,vecs])

if args.savevis:
    inout.save_eigenvector(args.savevis,sc,si,vecs)