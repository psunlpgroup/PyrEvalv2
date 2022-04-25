import numpy as np
import pandas as pd
import os
import shutil

homedir = '/home/nlp/pxs288/SU21/PyrEval/PyrEval_0615/'
resdir = homedir+'Results'
baselinedir = homedir + 'Baseline'
data = 'av-abcd'


for dataset in os.listdir(baselinedir):
	if dataset != data:
		continue
	df_corr = pd.DataFrame(columns = ['TopK', 'SortingMetric', 'WeightingMetric', 'WeightingScheme', 'CorrelationQuality', 'CorrelationCoverage','CorrelationComprehensive'])
	f = os.listdir(os.path.join(baselinedir, dataset))[0]
	df_baseline = pd.read_csv(os.path.join(baselinedir, dataset, f))
	df_baseline.sort_values(by=['filename'], inplace=True, ignore_index=True)
	# print(df_baseline)

	for config in os.listdir(os.path.join(resdir, dataset)):
		if not os.path.isdir(os.path.join(resdir, dataset, config)):
			continue
		f = os.path.join(resdir, dataset, config, 'results.csv')
		df_conf = pd.read_csv(f, skiprows = 1)
		df_conf.sort_values(by=['Summary'], inplace=True, ignore_index=True)
		# print(df_conf)
		# exit()

		topk, sort, weight, scheme = config.split('_')
		con_ql = df_conf['quality']
		con_co = df_conf['coverage']
		con_comp = df_conf['Comprehensive']

		if data in ['av', 'cc', 'plb', 'aied', 'plb-abcd', 'cc-abcd', 'av-abcd']:
			bl_ql = df_baseline['qualityScore']
			bl_co = df_baseline['coverageScore']
			bl_comp = df_baseline['comprehensiveScore']
		if data in ['plbc']:
			bl_ql = df_baseline['R Score']
			bl_co = df_baseline['R Score']
			bl_comp = df_baseline['R Score']
		if data in ['wim', 'wim-abcd']:
			bl_ql = df_baseline['quality']
			bl_co = df_baseline['coverage']
			bl_comp = df_baseline['total']

		corr_ql = bl_ql.corr(con_ql)
		corr_co = bl_co.corr(con_co)
		corr_comp = bl_comp.corr(con_comp)

		df_corr = df_corr.append({'TopK': topk, 'SortingMetric': sort, 'WeightingMetric': weight, 'WeightingScheme': scheme, 'CorrelationQuality': corr_ql, 
			'CorrelationCoverage': corr_co, 'CorrelationComprehensive': corr_comp}, ignore_index = True)
	os.chdir(resdir)
	df_corr.to_csv(data+'_corr.csv' ,index=False)
	# print (df_corr)

	os.chdir(homedir)
