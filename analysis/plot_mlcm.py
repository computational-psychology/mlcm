# -*- coding: utf-8 -*-
"""
Plots MLCM scales estimated by analysis_mlcm.R

@author: G. Aguilar, Oct 2021
"""
from read_data import read_data_mlcm
from utils import palette, frs
#import pandas as pd
#import numpy as np
import seaborn as sns
import matplotlib.pylab as plt
import matplotlib

sns.set_style("ticks", {'xtick.direction': 'in', 'ytick.direction': 'in',
                        "xtick.major.size": 2, "ytick.major.size": 2})
sns.set_context('talk')

matplotlib.rcParams['pdf.fonttype']=42
matplotlib.rcParams['font.sans-serif'] = ['Arial']
matplotlib.rcParams['font.family'] = 'sans-serif'


plotCI = True
method = 'glm' # glm method used for fitting in R, either 'glm' (normal method) or 'brglm' (bias reduced glm)

# Partiicpants reported in manuscript 
#names = ['ga6', 'jxv2', 'lxs', 'mm', 'pe', 'aa', 'js', 'sz']

# participants who also came afterwards
names = ['lys']
#frs = {n:False for n in names} # None (all data), or uncomment for data with outliers removed

modeltype = 'full'
meansamples = True
normalized = True

plotnewlum = False
#newluminances = np.array([0.01, 0.035, 0.07, 0.131, 0.26, 0.39, 0.52, 0.64, 0.77, 0.9])

# %%  reading data from all observers
ALL, low_lum_cdm2, high_lum_cdm2 = read_data_mlcm(names, 
                                                  frs, 
                                                  meansamples=meansamples, 
                                                  method=method, 
                                                  modeltype=modeltype,
                                                  normalized=normalized,
                                                  boot=False)

#newluminances = [graytolum(l) for l in newluminances]

# %% 
if len(names)>1:
    savename = 'all'
    col_wrap = 4
else:
    savename = '%s' % names[0]
    col_wrap = 1


# %%
ylim= (-0.1,1.1) if normalized else None

g = sns.FacetGrid(ALL, col='observer', hue='carrier', sharey=True,
                  margin_titles=True, col_wrap=1, legend_out=True, 
                  height=5, palette=palette, xlim=(-25, 525), ylim=ylim)
g.map(plt.scatter, 'luminance_cdm2', 'scale')


if plotCI:
    for i, col in enumerate(g.col_names):
        #print(col)
        for z, c in enumerate(['in white', 'in black']):
            
            # gets and plots errorbars
            curr = ALL[(ALL['observer']==col) & (ALL['carrier']==c)]
            #print(curr['scale'].values[-2])
            yerr = [curr['scale'] - curr['CIl'], curr['CIh'] - curr['scale']]
            
            g.axes[i].errorbar(curr['luminance_cdm2'], curr['scale'], yerr=yerr, 
                               fmt='none', ecolor=palette[c], capsize=0)
            
            yl = g.axes[i].get_ylim()
            # plots vertical lines for carriers' luminance
            g.axes[i].vlines(x=low_lum_cdm2, 
                                ymin=yl[0], 
                                ymax=yl[1],  
                                color='#636363',
                                linestyles='dotted')
            
            g.axes[i].vlines(x=high_lum_cdm2, 
                                ymin=yl[0], 
                                ymax=yl[1],  
                                color='#636363',
                                linestyles='dotted')
            # if plotnewlum:
            #     for l in newluminances:
            #         g.axes[0][i].vlines(x=l, 
            #                             ymin=yl[0], 
            #                             ymax=yl[1],  
            #                             color='#000000')
        
g.add_legend()
g.set_titles(col_template='{col_name}')
g.set_ylabels('Perceptual scale')
g.set_xlabels('Luminance [cd/m²]')


labelnorm = 'normalized' if normalized else 'unnormalized'
labelfr = 'wo_outliers' if any(list(frs.values())) else 'alltrials'
g.savefig('../figs/%s_%s_%s_%s_%s.pdf' % (savename, modeltype, method, labelnorm, labelfr))




# EOF
