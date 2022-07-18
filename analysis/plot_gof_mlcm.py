#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plots GoF diagnostics previously calculated by gof_mlcm.R

This script provides the python alternative to plot_gof_mlcm.R


@author: guille

"""

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pylab as plt
import matplotlib
import sys
import rpy2.robjects as robjects
from utils import frs


sns.set_style("ticks", {'xtick.direction': 'in', 'ytick.direction': 'in',
                        "xtick.major.size": 2, "ytick.major.size": 2})
sns.set_context('talk')

#matplotlib.rcParams['pdf.fonttype']=42
#matplotlib.rcParams['font.sans-serif'] = ['Arial']
#matplotlib.rcParams['font.family'] = 'sans-serif'

names = ['ga6', 'dk', 'jxv2', 'lxs', 'mm']
frs = None # None or frs

method = 'glm' # glm method used for fitting in R, either 'glm' (normal method) or 'brglm' (bias reduced glm)

modeltype = 'full'

for s, name in enumerate(names):
  
    
      ### loading R file and loading R objects into python variables
    try:
        f = frs[name]
        loadreduced = True
    except:
        loadreduced = False
        

    if loadreduced:
        fname = "../data/parsed_results/%s_reindexed_%s.fr.%s.diags.MLCM" % (name, modeltype, method)
        suffix = '.fr.'
    else:
        fname = "../data/parsed_results/%s_reindexed_%s.%s.diags.MLCM" % (name, modeltype, method)
        suffix = '.'
    print(fname)
    
    objs = robjects.r['load'](fname)
    
          
    diagnostics = robjects.r['obs.diags']
    
    #prob = list(diagnostics[diagnostics.names.index('p')])[0]
    prob = robjects.r['p'][0]
    per = robjects.r['per'][0]
    
    print('percentage inside envelope: %f' % per)
    print('p-value: %f' % prob)
    
    
    # %% copied from mlds.py module, plotdiags() method
    width=12
    height=5
    
    NumRuns = np.array(diagnostics[diagnostics.names.index('NumRuns')])
    resid = np.array(diagnostics[1])
    Obs_resid = np.array(diagnostics[diagnostics.names.index('Obs.resid')])
    ObsRuns = np.array(diagnostics[diagnostics.names.index('ObsRuns')])[0]
    
    nsim = resid.shape[0]
    n = resid.shape[1]
    
    alpha = 0.025
    
    lowc = resid[int(alpha * nsim), ]
    highc  = resid[int((1 - alpha) * nsim), ]
    
    
    cdfx = (np.arange(1, n + 1, 1) - 0.5) / n
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(width, height))
    
    ax1.set_xlabel("Deviance residual")
    ax1.set_ylabel("Cumulative density function")
    ax1.set_xlim((-3.5, 3.5))
    ax1.plot(np.sort(Obs_resid), cdfx, 'o', markersize=1,
             markeredgecolor='k', markerfacecolor='k')
    ax1.plot(lowc, cdfx, '-', color='#4C72B0', linewidth=1)
    ax1.plot(highc, cdfx, '-', color='#4C72B0', linewidth=1)
    ax1.spines['right'].set_visible(False)
    ax1.spines['top'].set_visible(False)
    ax1.tick_params(right=False, top=False)
    plt.locator_params(axis = 'y', nbins=4)
    
    
    # inset axes....
    axins = ax1.inset_axes([0.6, 0.4, 0.35, 0.35])
    axins.plot(np.sort(Obs_resid), cdfx, 'o', markersize=1,
               markeredgecolor='k', markerfacecolor='k')
    axins.plot(lowc, cdfx, '-', color='#4C72B0', linewidth=2)
    axins.plot(highc, cdfx, '-', color='#4C72B0', linewidth=2)
    
    # sub region of the original image
    x1, x2, y1, y2 = 0, 0.5, 0.85, 0.95
    axins.set_xlim(x1, x2)
    axins.set_ylim(y1, y2)
    axins.set_xticklabels('')
    axins.set_yticklabels('')
    axins.tick_params(left=False, right=False, top=False, bottom=False)
    
    ax1.indicate_inset_zoom(axins)
    
    
    ax2.hist(NumRuns, bins=25, density=True)
    ax2.axvline(ObsRuns, color='k', linewidth=3)
    ax2.set_xlabel("Number of Runs")
    ax2.set_ylabel("Frequency")
    ax2.spines['right'].set_visible(False)
    ax2.spines['top'].set_visible(False)
    ax2.tick_params(right=False, top=False)
    plt.locator_params(axis = 'y', nbins=4)
    
    plt.suptitle('percentage: %.2f // p-value: %.3f' % (per, prob))
    
    plt.savefig("../figs/gof/%s_reindexed%s%s.diags.MLCM.pdf" % (name, suffix, method))
    #plt.close()

            