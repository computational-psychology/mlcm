# -*- coding: utf-8 -*-
"""
Trying to fit parametric functions to perceptual scales... Naka-Rushton..


@author: G. Aguilar, Nov 2021
"""
from read_data import read_data_mlcm
from utils import observers, palette
import pandas as pd
import numpy as np
from scipy import optimize
import seaborn as sns
import matplotlib.pylab as plt

sns.set_style("ticks", {'xtick.direction': 'in', 'ytick.direction': 'in',
                        "xtick.major.size": 2, "ytick.major.size": 2})
sns.set_context('talk')


names = ['jxv', 'ga3', 'ga4', 'ga5', 'dk', 'ga6']
frs = [False]*len(names)


# %%  reading data from all observers
ALL, low_lum_cdm2, high_lum_cdm2 = read_data_mlcm(names, frs=frs)

# %%  fitting parametric function to data


def Naka_Rushton(x, p, q, ssc, rmax):
    return rmax*(x**(p+q) / (ssc + x**p))


#for s, name in enumerate(names):
#    print(name)
name = 'dk'

plt.figure(figsize = (10,5))
for i,c in enumerate(ALL['carrier'].unique()):
    
    plt.subplot(1,2,i+1)
    #c = 'on black'
    #c = 'on white'
    curr = ALL[(ALL['obs_short'] == name) & (ALL['carrier']==c)]
    
    ydata = curr['scale'].values
    xdata = curr['luminance'].values
    yerr = [curr['scale'] - curr['CIl'], curr['CIh'] - curr['scale']]
    
    
    p0 = [1.0, 1.0, 10, 1]
    
    popt, pcov = optimize.curve_fit(Naka_Rushton, xdata, ydata, p0, 
                                    bounds=(0, np.inf), maxfev = 10000)
    
    plt.plot(xdata, ydata, 'o', c=palette[c])
    plt.errorbar(curr['luminance'], curr['scale'], yerr=yerr, fmt='none',
                      ecolor=palette[c], capsize=0)
    plt.plot(xdata, Naka_Rushton(xdata, *popt), '--', c=palette[c])
    plt.title('p=%.2f, q=%.2f, ssc=%2.2f, rmax=%.2f' % tuple(popt), fontsize=12)
    plt.xlabel('luminance')
    plt.ylabel('scale')
    sns.despine()
plt.suptitle(observers[name])
plt.show()


# EOF
