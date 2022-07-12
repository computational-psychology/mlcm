# -*- coding: utf-8 -*-
"""
Plots matrices of responses from MLCM experiment


@author: G. Aguilar, March 2022
"""


import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pylab as plt

sns.set_style("white", {'xtick.direction': 'in', 'ytick.direction': 'in',
                        "xtick.major.size": 4, "ytick.major.size": 4 })
sns.set_context('talk')

name = 'ga6'

# %% MLCM results
### loading raw file.
d = pd.read_csv("../data/parsed_results/%s_reindexed_full.csv" % name)

# luminances
lums = pd.concat((d['lum1'], d['lum2'])).unique()
lums.sort()
    
# contexts
carriers = [0, 1]

stimlist = [(l,c) for c in carriers for l in lums ]


data = np.zeros((20, 20))
mask = np.zeros((20, 20))
Ns = np.zeros((20, 20))

for i in range(20):
    for j in range(20):
        
        s_row = stimlist[i]
        s_col = stimlist[j]
        
        set1 = d[(d['lum1']==s_row[0]) &( d['carrier1']==s_row[1]) & (d['lum2']==s_col[0]) &( d['carrier2']==s_col[1])]
        
        
        set2 = d[(d['lum1']==s_col[0]) &( d['carrier1']==s_col[1]) & (d['lum2']==s_row[0]) &( d['carrier2']==s_row[1])]
        
        N = len(set1) + len(set2)
        
        if N>0:
            n = np.sum(set2['Resp'].values) + np.sum(np.logical_not(set1['Resp'].values).astype(int))
            data[i,j] = n / N
            Ns[i,j] = N
            
        else:
            data[i,j] = np.nan
        
        if s_row[1] == s_col[1] and s_row[0] > s_col[0]:
            mask[i,j] = 1
        elif s_row[1] > s_col[1]:
            mask[i,j] = 1

# %%
plt.figure(figsize=(25, 20))
sns.heatmap(data, mask=mask, annot=True, xticklabels=stimlist, yticklabels=stimlist)
plt.title('%s - N per cell = %d' % (name, Ns.max()))
plt.savefig('../figs/%s_resp_matrix.pdf' % name)



# EOF
