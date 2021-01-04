#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec  7 09:46:54 2020

@author: bwinston
"""
import numpy as np
import os
from glob import glob
import matrix_methods as mm
import input_output as inout
import decomp as dcp
from scipy import sparse
import numpy as np
import utility_functions as ut
from sklearn.metrics import pairwise_distances_chunked
import time
from scipy.sparse import csgraph
import matplotlib.pylab as plt
from scipy.stats.stats import pearsonr
import statistics as stats     
         
'''
standard deviation and error, all harms with .8, .7, sequentially 
components across subjects (get set of reliable harmonics, look across subjects) 

average two sessions components? maybe
do both average of two sessions and just first session and compare to group average connectome harmonics
get rid of noise components--those not reliable within a subject or across subjects. interesting will be something
that's reliable within a subject but not across subjects. (that's where individual differences lie)
so how do we find reliable harmonics across subjects?
then we'll find test retest reliability of that, which is a more accurate depiction of test retest rel
PCA would be on set of all harmonics 


WITHIN SUBJECT TEST-RETEST RELIABILITY:
'''
test_retest_rel('/Users/bwinston/Documents/connectome_harmonics/chap_output/chap', 200) 
test_retest_rel('/Users/bwinston/Downloads/chap_out_test', 50) 
test_retest_rel('/data2/Brian/connectome_harmonics/three_chap_subjs', 50)   

hi = hp[1]['ret_used']

def get_key(my_dict, val):
    for key, value in my_dict.items():
         if val == value:
             return key

#looking at test retest reliability STILL ORDERING EFFECTS IN THIS
def test_retest_rel(chap_dir, n_evecs):
    n_evecs = n_evecs-1
    global cd 
    cd = {} #for chap_data
    all_bcorrs, bcorr_plot = [], []
    subject_dirs = glob(os.path.join(chap_dir, "sub-*")) #get subs
    subs = [subject_dir.split("-")[-1] for subject_dir in subject_dirs] 
    for sub in subs:
        cd[sub] = {}
        cd[sub]['bcorrs'] = []
        for ses in ['test','retest']:
           cd[sub][ses] = {}
           cd[sub][ses]['vecs'] = np.load(f'{chap_dir}/sub-{sub}/ses-{ses}/vecs.npy') 
           cd[sub][ses]['vecs'] = np.delete(cd[sub][ses]['vecs'], 0, axis=1)
        global hp
        hp, hp['holy'] = {}, {} #dict for within these fxns
        hp['corr_orig'] = np.empty((n_evecs,n_evecs))
        for evec_test in range(0,n_evecs): 
            for evec_retest in range(0,n_evecs): #n_evecs x n_evecs correlation matrix
                hp['corr_orig'][evec_retest,evec_test] = abs(pearsonr(cd[sub]['test']['vecs'][:,evec_test], cd[sub]['retest']['vecs'][:,evec_retest])[0]) #comparing column with column (ev with ev)
        hp['corr_all'] = hp['corr_orig'].swapaxes(0,1) #prepare to turn into dicts
        hp['corr_all'] = {index:{i:j for i,j in enumerate(k) if j} for index,k in enumerate(hp['corr_all'])} #turn into dicts
        find_bcorrs(sub, hp, 0, n_evecs) #run find bcorrs function, get best pairs
        for ev in range(n_evecs):
            cd[sub]['bcorrs'].append(cd[sub]['pairs'][ev]['bcorr']) #all ideal corrs (w/ no repeats)
    for sub in subs:        
        all_bcorrs.append(cd[sub]['bcorrs']) #list of lists of bcorrs
    cd['bcorr_avg'] = np.average(np.array(all_bcorrs), axis=0) #average of each spot in bcorrs
    for avg in range(1,n_evecs):
        bcorr_plot.append(stats.mean(cd['bcorr_avg'][1:avg])) 
    plt.plot(bcorr_plot)

def find_bcorrs(sub, hp, run, n_evecs): 
    while len(hp['corr_all']) > 0:
        hp[run] = {}
        hp[run]['maxes'] = {}
        for ev in hp['corr_all']: #for each test session evec, which retest session evec is the best match?
            hp[run]['maxes'][ev] = {} #test session ev's dict
            hp[run]['maxes'][ev]['bcorr'] = max(hp['corr_all'][ev].values()) #best correlation w/ any retest ev
            hp[run]['maxes'][ev]['ret_ind'] = get_key(hp['corr_all'][ev], max(hp['corr_all'][ev].values())) #which retest ev was above?
        hp[run]['ret_used'], hp[run]['win_ind'], hp[run]['good_boys'] = [], [], []
        for ev in hp['corr_all']:
            hp[run]['ret_used'].append(hp[run]['maxes'][ev]['ret_ind']) #tally retest indices used above
        ret_dups = set([x for x in hp[run]['ret_used'] if hp[run]['ret_used'].count(x) > 1]) #retest evs that were used multiple times
        if ret_dups == 0:
            break
        hp[run]['ret_used'] = set(hp[run]['ret_used']) #take out duplicates from ret_used
        for ret_dup in ret_dups: #for each retest ev in demand by multiple
            competition = [] #competition is within the retest ev
            for ev in hp[run]['maxes']: 
                if ret_dup == hp[run]['maxes'][ev]['ret_ind']: #if a test evec is involved in a dispute
                    competition.append(hp[run]['maxes'][ev]['bcorr']) #add its correlation to retest ev's competition 
            competition = max(competition) 
            for ev in hp[run]['maxes']:
                if hp[run]['maxes'][ev]['bcorr'] == competition: #if its correlation was a winner, leave as is
                    hp[run]['win_ind'].append(ev) #add test ev that won to win_ind
        for ev in hp['corr_all']:
            if hp[run]['maxes'][ev]['ret_ind'] not in ret_dups: #if test ev not involved in any disputes, add to good_boys
               hp[run]['good_boys'].append(ev) 
        for ev in list(hp['corr_all']):
            if ev in (set(hp[run]['good_boys']) | set(hp[run]['win_ind'])):
               hp['holy'][ev] = hp[run]['maxes'][ev] #add good boys and winners to holy
               del hp['corr_all'][ev] #delete them from corr_all
        for ev in hp['corr_all']:
            for r_ev in hp[run]['ret_used']:
                del hp['corr_all'][ev][r_ev] #idk what this is doing
        run = run + 1
        find_bcorrs(sub, hp, run, len(hp['corr_all'])) #rerun function on smaller corr_all (leftovers)
    cd[sub]['pairs'] = hp['holy']
    
'''
average connectome/across subjects shit:
'''

def get_key(my_dict, val):
    for key, value in my_dict.items():
         if val == value:
             return key

#generate average-connectome harmonics
def avg_harms(chap_dir):
    subject_dirs = glob(os.path.join(chap_dir, "sub-*"))
    subs = [subject_dir.split("-")[-1] for subject_dir in subject_dirs]
    global avg
    avg = {}
    avg['connectomes_test'], avg['connectomes_retest'], avg['connectomes_all']= 0,0,0
    for sub in subs:
       avg['connectomes_test'] = avg['connectomes_test'] + sparse.load_npz(f'{chap_dir}/sub-{sub}/ses-test/connectome.npz') #sum all test connectomes
       avg['connectomes_retest'] = avg['connectomes_retest'] + sparse.load_npz(f'{chap_dir}/sub-{sub}/ses-retest/connectome.npz')
       avg['connectomes_all'] = avg['connectomes_all'] + sparse.load_npz(f'{chap_dir}/sub-{sub}/ses-test/connectome.npz') + sparse.load_npz(f'{chap_dir}/sub-{sub}/ses-retest/connectome.npz')
    avg['connectomes_test'] = avg['connectomes_test'] / len(subs) #take average
    avg['connectomes_retest'] = avg['connectomes_retest'] / len(subs)
    avg['connectomes_all'] = avg['connectomes_all'] / (len(subs)*2)
    inout.if_not_exist_make(f'{chap_dir}/sub-test_avg')
    inout.if_not_exist_make(f'{chap_dir}/sub-retest_avg')
    inout.if_not_exist_make(f'{chap_dir}/sub-total_avg')
    avg_test_vals,avg_test_vecs = dcp.lapDecomp(avg['connectomes_test'], 200) 
    avg_retest_vals,avg_retest_vecs = dcp.lapDecomp(avg['connectomes_retest'], 200) 
    avg_total_vals,avg_total_vecs = dcp.lapDecomp(avg['connectomes_all'], 200) 
    np.save(f'{chap_dir}/sub-test_avg/vecs', avg_test_vecs)
    np.save(f'{chap_dir}/sub-retest_avg/vecs', avg_retest_vecs)
    np.save(f'{chap_dir}/sub-total_avg/vecs', avg_total_vecs)

#average connectome harmonics as components compare to individuals
def ind_vs_avg(chap_dir, n_evecs):
    global iva
    iva = {} 
    subject_dirs = glob(os.path.join(chap_dir, "sub-*"))
    subs = [subject_dir.split("-")[-1] for subject_dir in subject_dirs]
    for sub in ['test_avg', 'retest_avg', 'total_avg']:
        subs.remove(sub)
    for sub in subs:
        iva[sub] = {}    
        for ses in ['test','retest']:
           iva[sub][ses],iva[f'{ses}_avg'] = {}, {}
           iva[sub][ses]['bcorrs'] = []
           iva[sub][ses]['vecs'] = np.load(f'{chap_dir}/sub-{sub}/ses-{ses}/vecs.npy')
           iva[f'{ses}_avg']['vecs'] = np.load(f'{chap_dir}/sub-{ses}_avg/vecs.npy')
        global hp
        hp = {}
        for ses in ['test','retest']:
            hp[ses], hp[ses]['holy'] = {}, {}  
            hp[ses]['corr_orig'] = np.empty((n_evecs,n_evecs)) #init comparison matrix 
            for evec_avg in range(0,n_evecs): 
                for evec_ses in range(0,n_evecs): #n_evecs x n_evecs correlation matrix
                    hp[ses]['corr_orig'][evec_ses,evec_avg] = abs(pearsonr(iva[f'{ses}_avg']['vecs'][:,evec_avg], iva[sub][ses]['vecs'][:,evec_ses])[0])
            hp[ses]['corr_all'] = hp[ses]['corr_orig'].swapaxes(0,1)
            hp[ses]['corr_all'] = {index:{i:j for i,j in enumerate(k) if j} for index,k in enumerate(hp[ses]['corr_all'])}
            find_bcorrs_iva(sub, ses, hp, 0, hp[ses]['corr_all'], n_evecs)
    for sub in subs:
        for ses in ['test','retest']:
            for ev in range(n_evecs):
                iva[sub][ses]['bcorrs'].append(iva[sub][ses]['pairs'][ev]['bcorr'])
    iva['all_test_bcorrs'],iva['all_retest_bcorrs'] = [],[]
    for sub in subs:
        for ses in ['test','retest']:
            iva[f'all_{ses}_bcorrs'].append(iva[sub][ses]['bcorrs'])
    iva['bcorr_test_avg'] = np.average(np.array(iva['all_test_bcorrs']), axis = 0)
    iva['bcorr_retest_avg'] = np.average(np.array(iva['all_retest_bcorrs']), axis = 0)
        
#finds best correlations btwn avg and ind
def find_bcorrs_iva(sub, ses, hp, run, corr_mat, n_evecs): 
    while len(hp[ses]['corr_all']) > 0:
        hp[ses][run] = {}
        hp[ses][run]['maxes'] = {}
        for ev in hp[ses]['corr_all']: #for each test session evec, which retest session evec is the best match?
            hp[ses][run]['maxes'][ev] = {}
            hp[ses][run]['maxes'][ev]['bcorr'] = max(hp[ses]['corr_all'][ev].values())
            hp[ses][run]['maxes'][ev][f'{ses}_ind'] = get_key(hp[ses]['corr_all'][ev], max(hp[ses]['corr_all'][ev].values()))
        hp[ses][run][f'{ses}_used'], hp[ses][run]['win_ind'], hp[ses][run]['good_boys'] = [], [], []
        for ev in hp[ses]['corr_all']:
            hp[ses][run][f'{ses}_used'].append(hp[ses][run]['maxes'][ev][f'{ses}_ind'])
        ses_dups = set([x for x in hp[ses][run][f'{ses}_used'] if hp[ses][run][f'{ses}_used'].count(x) > 1])
        if ses_dups == 0:
            break
        hp[ses][run][f'{ses}_used'] = set(hp[ses][run][f'{ses}_used'])
        for ses_dup in ses_dups:
            competition = []
            for ev in hp[ses][run]['maxes']:
                if ses_dup == hp[ses][run]['maxes'][ev][f'{ses}_ind']:
                    competition.append(hp[ses][run]['maxes'][ev]['bcorr'])
            competition = max(competition)
            for ev in hp[ses][run]['maxes']:
                if hp[ses][run]['maxes'][ev]['bcorr'] == competition:
                    hp[ses][run]['win_ind'].append(ev)
        for ev in hp[ses]['corr_all']:
            if hp[ses][run]['maxes'][ev][f'{ses}_ind'] not in ses_dups:
               hp[ses][run]['good_boys'].append(ev) 
        for ev in list(hp[ses]['corr_all']):
            if ev in (set(hp[ses][run]['good_boys']) | set(hp[ses][run]['win_ind'])):
               hp[ses]['holy'][ev] = hp[ses][run]['maxes'][ev]
               del hp[ses]['corr_all'][ev]
        for ev in hp[ses]['corr_all']:
            for s_ev in hp[ses][run][f'{ses}_used']:
                del hp[ses]['corr_all'][ev][s_ev]
        run = run + 1
        find_bcorrs_iva(sub, ses, hp, run, hp[ses]['corr_all'], len(hp[ses]['corr_all']))
    iva[sub][ses]['pairs'] = hp[ses]['holy']


hi = iva['105923']['test']['pairs']

po = iva['bcorr_test_avg']
op = iva['bcorr_retest_avg']

hcp_fem_ids = [103818, 105923, 111312, 114823, 115320, 125525, 130518, 135528, 137128, 143325, 144226, 158035, 169343, 172332, 175439, 177746, 187547, 192439, 194140, 195041, 200109, 200614, 204521, 250427, 287248, 562345,627549, 660951, 859671,861456, 877168]
hcp_male_ids = [122317, 139839, 146129, 149337, 149741, 151526, 185442, 341834, 433839, 599671, 601127, 783462, 917255]

avg_harms('/Users/bwinston/Documents/connectome_harmonics/chap_output/chap')
ind_vs_avg('/Users/bwinston/Documents/connectome_harmonics/chap_output/chap', 100)
'''
Take everyone from test session, generate 100 pca harmonics. for each subject, find the best test session pairs with 
those 100 pca harmonics. 

Then, find the average correlation btwn each pca harmonic and its best pair across all subjects--this shows the most reliable components across subjects (maybe). Pick 20.

Then, for each subject, find test-retest reliability of those particular harmonics (the ones that paired w/ the 20 best pcas) with their best pair from the retest session.
'''
def ind_vs_pca(chap_dir, n_evecs, n_pca):
    n_evecs = n_evecs-1
    global ivp
    ivp, ivp['test'], ivp['retest'] = {}, {}, {}
    subject_dirs = glob(os.path.join(chap_dir, "sub-*"))
    subs = [subject_dir.split("-")[-1] for subject_dir in subject_dirs]
    for sub in ['test_avg', 'retest_avg', 'total_avg']:
        if os.path.exists(f'{chap_dir}/{sub}'):
            subs.remove(sub)
    ivp['test']['evlist'], ivp['retest']['evlist'] = [], []
    for sub in subs:
        ivp[sub] = {}    
        for ses in ['test','retest']:
           ivp[sub][ses],ivp[f'{ses}_avg'] = {}, {}
           ivp[sub][ses]['bcorrs'] = []
           ivp[sub][ses]['vecs'] = np.load(f'{chap_dir}/sub-{sub}/ses-{ses}/vecs.npy')
           ivp[sub][ses]['vecs'] = np.delete(ivp[sub][ses]['vecs'], 0, axis=1)
           ivp[ses]['evlist'].append(ivp[sub][ses]['vecs'][:,0:n_evecs])
    for ses in ['test','retest']:
        ivp[ses]['pca_harms'] = dcp.get_group_pca_comp_b(ivp[ses]['evlist'], 100)
    for sub in subs:
        global hp
        hp = {}
        for ses in ['test','retest']:
            hp[ses], hp[ses]['holy'] = {}, {}  
            hp[ses]['corr_orig'] = np.empty((n_evecs,n_pca)) #init comparison matrix 
            for evec_pca in range(0,n_pca): 
                for evec_ses in range(0,n_evecs): #n_evecs x n_evecs correlation matrix
                    hp[ses]['corr_orig'][evec_ses,evec_pca] = abs(pearsonr(ivp[ses]['pca_harms'][:,evec_pca], ivp[sub][ses]['vecs'][:,evec_ses])[0])
            hp[ses]['corr_all'] = hp[ses]['corr_orig'].swapaxes(0,1)
            hp[ses]['corr_all'] = {index:{i:j for i,j in enumerate(k) if j} for index,k in enumerate(hp[ses]['corr_all'])}           
            find_bcorrs_ivp(sub, ses, hp, 0, hp[ses]['corr_all'], n_evecs)  
    for sub in subs:
        for ses in ['test','retest']:
            for ev in range(n_pca):
                ivp[sub][ses]['bcorrs'].append(ivp[sub][ses]['pairs'][ev]['bcorr'])
    ivp['all_test_bcorrs'],ivp['all_retest_bcorrs'] = [],[]
    for sub in subs:
        for ses in ['test','retest']:
            ivp[f'all_{ses}_bcorrs'].append(ivp[sub][ses]['bcorrs']) #list of lists
    ivp['bcorr_test_avg'] = np.average(np.array(ivp['all_test_bcorrs']), axis = 0)
    ivp['bcorr_retest_avg'] = np.average(np.array(ivp['all_retest_bcorrs']), axis = 0)
    bcorr_t_sort = -np.sort(-ivp['bcorr_test_avg'])[::1]
    bcorr_r_sort = -np.sort(-ivp['bcorr_retest_avg'])[::1]
    bcorr_t_sort = bcorr_t_sort[:20]
    bcorr_r_sort = bcorr_r_sort[:20]
    ivp['pca_t_harms'], ivp['pca_r_harms'] = [], []
    for c in bcorr_t_sort:
        ivp['pca_t_harms'].append(np.where(ivp['bcorr_test_avg'] == c)[0][0]) #best pca harmonics
    for c in bcorr_r_sort:
        ivp['pca_r_harms'].append(np.where(ivp['bcorr_retest_avg'] == c)[0][0]) 
    for sub in subs:
        ivp[sub]['enchilada'] = {} #enchilada is test-retest but with the test ones we care about bc they were similar to PCAs
        ivp[sub]['enzymatique'] = []
        ivp[sub]['ti_2_check'] = []
        for pca_harm in ivp['pca_t_harms']:
            ivp[sub]['ti_2_check'].append(ivp[sub]['test']['pairs'][pca_harm]['test_ind'])
    test_retest_rel(chap_dir, n_evecs)
    all_enzymatiques = []
    for sub in subs:
        for ti in ivp[sub]['ti_2_check']:
            ivp[sub]['enchilada'][ti] = cd[sub]['pairs'][ti]
            ivp[sub]['enzymatique'].append(ivp[sub]['enchilada'][ti]['bcorr'])
        all_enzymatiques.append(ivp[sub]['enzymatique'])
    ivp['test_retest_reliabilty_avg'] = np.average(np.array(all_enzymatiques), axis = 0)

    
def find_bcorrs_ivp(sub, ses, hp, run, corr_mat, n_evecs): 
    while len(hp[ses]['corr_all']) > 0:
        hp[ses][run] = {}
        hp[ses][run]['maxes'] = {}
        for ev in hp[ses]['corr_all']: #for each pca evec, which {ses} evec is the best match?
            hp[ses][run]['maxes'][ev] = {}
            hp[ses][run]['maxes'][ev]['bcorr'] = max(hp[ses]['corr_all'][ev].values())
            hp[ses][run]['maxes'][ev][f'{ses}_ind'] = get_key(hp[ses]['corr_all'][ev], max(hp[ses]['corr_all'][ev].values()))
        hp[ses][run][f'{ses}_used'], hp[ses][run]['win_ind'], hp[ses][run]['good_boys'] = [], [], []
        for ev in hp[ses]['corr_all']:
            hp[ses][run][f'{ses}_used'].append(hp[ses][run]['maxes'][ev][f'{ses}_ind'])
        ses_dups = set([x for x in hp[ses][run][f'{ses}_used'] if hp[ses][run][f'{ses}_used'].count(x) > 1])
        if ses_dups == 0:
            break
        hp[ses][run][f'{ses}_used'] = set(hp[ses][run][f'{ses}_used'])
        for ses_dup in ses_dups:
            competition = []
            for ev in hp[ses][run]['maxes']:
                if ses_dup == hp[ses][run]['maxes'][ev][f'{ses}_ind']:
                    competition.append(hp[ses][run]['maxes'][ev]['bcorr'])
            competition = max(competition)
            for ev in hp[ses][run]['maxes']:
                if hp[ses][run]['maxes'][ev]['bcorr'] == competition:
                    hp[ses][run]['win_ind'].append(ev)
        for ev in hp[ses]['corr_all']:
            if hp[ses][run]['maxes'][ev][f'{ses}_ind'] not in ses_dups:
               hp[ses][run]['good_boys'].append(ev) 
        for ev in list(hp[ses]['corr_all']):
            if ev in (set(hp[ses][run]['good_boys']) | set(hp[ses][run]['win_ind'])):
               hp[ses]['holy'][ev] = hp[ses][run]['maxes'][ev]
               del hp[ses]['corr_all'][ev]
        for ev in hp[ses]['corr_all']:
            for s_ev in hp[ses][run][f'{ses}_used']:
                del hp[ses]['corr_all'][ev][s_ev]
        run = run + 1
        find_bcorrs_ivp(sub, ses, hp, run, hp[ses]['corr_all'], len(hp[ses]['corr_all']))
    ivp[sub][ses]['pairs'] = hp[ses]['holy']

   
ind_vs_pca('/Users/bwinston/Downloads/chap_out_test', 200, 100)    
test_retest_rel('/Users/bwinston/Downloads/chap_out_test', 200)    
    
'''notes for what to do b-ri - just run test_retest_rel and save the columns of 
the output for the test evs that we care about from the pca thing mmmkay?'''
    
  
    
    
    
    
    
    



