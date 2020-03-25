#!/usr/bin/env python
# coding: utf-8

# In[1]:

#
# get_ipython().magic('load_ext autoreload')
# get_ipython().magic('autoreload 2')
#
# get_ipython().magic('matplotlib inline')


# In[2]:


import itertools
import sys
sys.path.insert(0, '..')
import warnings
warnings.filterwarnings('ignore')

import matplotlib.pyplot as plt
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 16
import numpy as np
import pandas as pd
import requests
import seaborn as sns
# sns.set_style('whitegrid')

import covid19


# ## data

# In[3]:


# date_italy_regions_path = 'dpc-covid19-ita-regioni.csv'
date_italy_regions_path = covid19.data.download('regioni')


# In[4]:


data_italy_regions = pd.read_csv(date_italy_regions_path, parse_dates=['data'], index_col=['data'])
data_italy_regions['totale_terapia_intensiva'] = data_italy_regions['terapia_intensiva'] + data_italy_regions['deceduti']
data_italy_regions['totale_ricoverati'] = data_italy_regions['ricoverati_con_sintomi'] + data_italy_regions['totale_terapia_intensiva']

data_italy_regions.index = data_italy_regions.index.normalize()

print(sorted(data_italy_regions['denominazione_regione'].unique().tolist()))

data_italy_regions.loc[data_italy_regions.index.max()].sort_values('ricoverati_con_sintomi', ascending=False)[['denominazione_regione', 'ricoverati_con_sintomi', 'terapia_intensiva', 'deceduti']]


# ## situation report

# In[5]:


DAY = np.timedelta64(24 * 60 * 60,'s')

START_FIT = None
CHANGE_FIT_1 = np.datetime64('2020-03-05')
CHANGE_FIT_2 = np.datetime64('2020-03-11')
CHANGE_FIT_3 = np.datetime64('2020-03-15')
STOP_FIT = None

EXTRAPOLTATE = ('2020-02-23', '2020-03-24')

REGIONS_FIT_PARAMS = {
    'Lombardia': {
        'exponential_fits': [(None, '2020-03-06'), ('2020-03-09', '2020-03-17'), ('2020-03-19', None)],
        # 'exponential_fits': [(None, '2020-03-11'), ('2020-03-12', None)],
    },
    # 'Emilia Romagna': {
    #     'exponential_fits': [(None, '2020-03-01'), ('2020-03-02', '2020-03-06'), ('2020-03-07', '2020-03-18'), ('2020-03-19', None)]
    # },
    # 'Piemonte': {
    #     'exponential_fits': [(None, '2020-03-10'), ('2020-03-11', '2020-03-19'), ('2020-03-20', None)]
    # },
    # 'Veneto': {
    #     'exponential_fits': [(None, '2020-03-12'), ('2020-03-13', None)],
    # },
    # 'Marche': {
    #     'exponential_fits': [(None, '2020-03-06'), ('2020-03-07', '2020-03-15'), ('2020-03-16', None)]
    # },
    # 'Toscana': {
    #     'exponential_fits': [(None, '2020-03-08'), ('2020-03-10', '2020-03-16'), ('2020-03-17', None)]
    # },
    # 'Liguria': {
    #     'exponential_fits': [('2020-03-04', '2020-03-15'), ('2020-03-16', '2020-03-20'), ('2020-03-21', None)]
    # },
    # 'Lazio':  {
    #     'exponential_fits': [(None, '2020-03-13'), ('2020-03-14', '2020-03-20'), ('2020-03-21', None)]
    # },
    # 'P.A. Trento': {
    #     'exponential_fits': [(None, None)]
    #
    # },
    # 'Puglia': {
    #     'exponential_fits': [(None, '2020-03-15'), ('2020-03-16', None)]
    # },
    # 'Abbruzzo': {},
    # 'Sicilia': {
    #     'exponential_fits': [('2020-03-08', None)]
    # },
    # 'Friuli Venezia Giulia': {
    #     'exponential_fits': [(None, '2020-03-15'), ('2020-03-16', None)]
    # },
    # 'Campania': {
    #     'exponential_fits': [(None, None)]
    # },
    # 'P.A. Bolzano': {},
    # 'Basilicata': {},
    # 'Calabria': {
    #     'exponential_fits': [('2020-03-08', None)]
    # },
    # 'Molise': {},
    # 'Sardegna': {},
    #
    # 'Umbria': {
    #     'exponential_fits': [(None, None)]
    # },
    # "Valle d'Aosta": {},
}
    
DELAY = 12 * DAY
PALETTE_ONE = list(sns.color_palette())
PALETTE = itertools.cycle(PALETTE_ONE)


# In[6]:


fits = {}
for region, params in REGIONS_FIT_PARAMS.items():
    for kind in ['ricoverati_con_sintomi', 'deceduti']:
        exponential_fits = params.get('exponential_fits', [(START_FIT, CHANGE_FIT_1), (CHANGE_FIT_1 + DAY, CHANGE_FIT_2), (CHANGE_FIT_2 + DAY, CHANGE_FIT_3), (CHANGE_FIT_3 + DAY, STOP_FIT)])
        fits[region, kind] = []
        for start, stop in exponential_fits:
            try:
                select = (data_italy_regions['denominazione_regione'] == region) & (data_italy_regions[kind] >= 8)
                fits[region, kind] += [covid19.fit.ExponentialFit.from_frame(kind, data_italy_regions[select], start=start, stop=stop)]
            except:
                print('skipping:', region, start, stop)


# In[7]:


for region in REGIONS_FIT_PARAMS:
    select = (data_italy_regions['denominazione_regione'] == region)
    for kind in ['ricoverati_con_sintomi', 'deceduti']:
        _, ax = plt.subplots(subplot_kw={'yscale': 'log', 'ylim': (9, 15000)}, figsize=(14, 8))
        _ = ax.yaxis.grid(color='lightgrey', linewidth=0.5)
        _ = covid19.plot.add_events(ax, linestyle=':', offset=11, color='grey')
        if len(fits[region, kind]) == 0:
            print('No data for', region)
            continue
        try:
            for fit, color in zip(fits[region, kind], PALETTE_ONE[1:]):
                covid19.plot.plot_fit(ax, fit, label=kind.split('_')[0].title(), extrapolate=EXTRAPOLTATE, color=color)
            covid19.plot.plot_data(ax, data_italy_regions[select][kind], label=kind.split('_')[0].title(), color=PALETTE_ONE[0], date_interval=3)
            ax.set_title(f'{region}')
            _ = ax.yaxis.grid(color='lightgrey', linewidth=0.5)
            _ = ax.yaxis.tick_right()
        except:
            pass

#_ = ax.set(title=r'COVID-19 "severe" cases in Italy. Fit is $f(t) = 2 ^ \frac{t - t_0}{T_d}$, with $T_d$ doubling time and $t_0$ reference date')


# ## Estimate of the initial / uncontined doubling time

# In[8]:


for key, value in list(fits.items()):
    if len(value):
        print(f'{key[0]}:{" " * (14 - len(key[0]))} {str(value[0])}')


# In[9]:


for key, value in list(fits.items()):
    if len(value):
        print(f'{key[0]}:{" " * (14 - len(key[0]))} {str(value[-1])}')


# In[10]:


data_italy_regions[data_italy_regions['denominazione_regione'] == 'Lombardia']


# In[ ]:

plt.show()


