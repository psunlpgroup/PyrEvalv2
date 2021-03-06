#   Script for scoring summaries by the pyramid

#    Copyright (C) 2017 Yanjun Gao

#    This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

#Wasih (02-21-20) Add more structure 
from lib_scoring import *
#from lib_scoring import sentencesFromSegmentations, SummaryGraph, buildSCUcandidateList, filename, getsegsCount
#from lib_scoring import getScore, getLayerSizes, processResults, scusBySentences, maxRawScore, readPyramid, new_getlayersize
from scipy.stats import pearsonr as pearson
from scipy.stats import spearmanr as spearman
#from printEsumLog import printEsumLogWrapper 
from printEsumLog import *
from time import time
import optparse
import glob
import copy
import csv
import os
import collections
import sys
import pandas as pd
import pickle
import threading
import json

#Wasih (02-21-20) results.csv not generating
PYTHON_VERSION = 2
if sys.version_info[0] == 2:
    import ConfigParser as configparser
else:
    import configparser
    PYTHON_VERSION = 3

#Wasih (02-21-20) Use termcolor to display colored text; user-friendly
from termcolor import colored

"""
============================ Input==============================
"""
#dir1 = sys.argv[1]

#dataset_ind = sys.argv[1]
#Wasih (02-21-20) results.csv not generating

timer = time()

config = configparser.ConfigParser()
config.read('../parameters.ini')

#Puru (11-03-21) Fixed bugs with -l -t -a 

parser = optparse.OptionParser()
parser.add_option('-a', '--all', action="store_true", dest="a", default=False)
parser.add_option('-t', '--table', action="store_true", dest="t", default=False)
parser.add_option('-p', '--pyramid', action="store", dest="pyramid", default="pyrs/pyramids")
#parser.add_option('-o', '--output', action="store", dest='output', default='../results.csv')
#Wasih (02-21-20) results.csv not generating
parser.add_option('-o', '--output', action="store", dest='output', default=config.get('Paths', 'OutputFile'))

parser.add_option('-l', '--log', action='store', dest='log', default=True)
parser.add_option('-m', '--model', action='store', dest='model', default=1)
parser.add_option('-n', '--numsmodel', action='store', dest='numsmodel', default=False)
#Wasih 04-13-21 Add flag for return type data structure for notebook
parser.add_option('-r', '--returnflag', action='store', dest='returnflag', default=False)

options, args = parser.parse_args()

print_all = options.a
print("Print All booleanb value:", print_all)
print_table = options.t
pyramid_path = options.pyramid
results_file = options.output
log = options.log

#Wasih 04-07-21: If log folder is not there create it
if log or print_all:
    if not os.path.exists('../log'):
        os.makedirs('../log')

model = options.model
#pyramids = list(glob.iglob(pyramid_path + '*.pyr'))
pyramids = list(glob.iglob(pyramid_path + '/*.pyr'))
#pyramids = list(glob.iglob(dir1+"/*.pyr"))
summaries = list(glob.iglob('../Preprocess/peer_summaries/*'))
numsmodel = len(list(glob.iglob('../Preprocess/wise_crowd_summaries/*.xml')))
#Wasih (07-15-21) If ABCD is used, then instead of xml, '.out' files will be there
if numsmodel == 0:
    numsmodel = len(list(glob.iglob('../Preprocess/wise_crowd_summaries/*.out')))

#Wasih 07-04-21 Override numsmodel with parser if present
if options.numsmodel:
    numsmodel = options.numsmodel
    numsmodel = int(numsmodel)

numsmodel = 5
print ("Numbers of contributors: ", numsmodel)
# See pyrmaid from "Scoring/pyrs/pyramids/" folder
#pyramid = sys.argv[1]
#for testing
# pyramids = list(glob.iglob('pyrs/pyramids/*'))
#pyramids = list(glob.iglob('pyrs/pyramids/*'))
# for pyr in pyramids:
    # print (pyr)



"""
================ Scoring Mechanisms ======================
"""
score_tables = ['raw', 'quality', 'coverage', 'Comprehensive']

"""
==== What is Matter Test Data Set ====
"""

"""
Raw scores from scores.csv, a column 
"""

"""
=== DUC Test Data Sets ====
"""


def getName(name):
    num = name.rfind('.')
    name = name[num+1:]
    return name


"""
=== Dictionary data-structure used to return to notebook after evaluating a summary. {Segment-Id:{'text':<Text corresponding to Segment-Id>, 'SCU':SCU-Id},...}
"""

def getDictionary(segList, pyramid, results, scores):
    #closely follows printSegments() in printEsumLog.py
    answer = {}
    for s in segList:
        for seg_index, text in s.text.items():
            if seg_index in s.scu_text_pairs.keys():
                segment_id = str(s.sentence_id) + '&' + str(s.segment_id) + '&' + str(seg_index)
                value = {}
                value['text'] = text.strip()
                value['SCU'] = s.scu_text_pairs[seg_index]
                answer[segment_id] = value
            else:
                segment_id = str(s.sentence_id) + '&' + str(s.segment_id) + '&' + str(seg_index)
                value = {}
                value['text'] = text.strip()
                value['SCU'] = None
                answer[segment_id] = value
    #now put scores in answer
    for (key, value) in scores[0].items():
        answer['raw'] = value
    for (key, value) in scores[1].items():
        answer['quality'] = value
    for (key, value) in scores[2].items():
        answer['coverage'] = value
    for (key, value) in scores[3].items():
        answer['comprehensive'] = value
    return answer

"""
====================== Scoring Pipeline ========================
"""

#Puru (11-03-21) Implemented Threading. Commented out since did not improve performance 

for pyramid in pyramids:
    raw_scores = {}
    quality_scores = {}
    coverage_scores = {}
    comprehension_scores = {}
    pyramid_name = pyramid[pyramid.rfind('/') + 1:pyramid.rfind('.')]
    #print "test"
    scus_og, scu_labels = readPyramid(pyramid)
    x = []
    # threads = []
    # Puru 02/17/22 Extension for Notebook Input generation and descriptive spreadsheets
    cu_matches = {}
    group_matches = {}


    for summary in summaries:
        if os.path.isdir(summary):
            summ = glob.iglob(summary+'/*')
            #fn is the summary name 
            for fn in summ:
                if fn.endswith('.ls'):
                    fn_name = fn.split('/')[-1].rsplit('.', 1)[0]
                    print ("Scoring File: ", fn_name)
                    # if print_all:
                        # print("Printing output is disabled with multithreading")
                        # print_all = False
                    # threads.append(threading.Thread(target = score, args= (copy.deepcopy(scus_og), fn, raw_scores, quality_scores, coverage_scores, comprehension_scores, pyramid, pyramid_name, scu_labels, numsmodel, print_all, log, options.returnflag)))
                    x.append(fn_name)
                    score(copy.deepcopy(scus_og), fn, raw_scores, quality_scores, coverage_scores, comprehension_scores, pyramid, pyramid_name, scu_labels, numsmodel, print_all, log, options.returnflag, cu_matches, group_matches)
                    # threads[-1].start()

    # for i in range(len(threads)):
    #     threads[i].join()
    # if print_table:
        #results_f = 
        ### For DUC05


    # Puru 02/17/22 Extension for Notebook Input generation and descriptive spreadsheets
    with open('cu_vectors.json', 'w') as f:
        json.dump(cu_matches, f)
    with open('groupings_vectors.json', 'w') as f:
        json.dump(group_matches, f)
    # Take input from file for the grouping names once file is decided
    cu_df = pd.DataFrame.from_dict(cu_matches, orient='index')
    cu_df = cu_df.sort_index()
    with open('cu_vectors.csv', 'w') as f:
        cu_df.to_csv(f)
    gp_df = pd.DataFrame.from_dict(group_matches, orient='index', columns = ['A', 'B', 'C', 'D'])
    gp_df = gp_df.sort_index()
    with open('group_vectors.csv', 'w') as f:
        gp_df.to_csv(f)    


    # print(cu_matches)
    # print(group_matches)
    ## FOr Duc 05
    #results_file = "results-raw.csv"
    print ("Will write into results file!! ", results_file)
    f = open(results_file, 'w')
    f.close()
    # 07/05/21 Puru changes to sorting of results
    # x = [summ for summ in summaries if not summ.split('.')[-1] == 'xml']
    x = sorted(x)
    # print(x)
    #Puru (11-03-21) Fixed Output bugs

    with open(results_file, 'a') as f:
        w = csv.writer(f)
        w.writerow([pyramid_name])
        if print_table:
            print (pyramid_name)
        w.writerow(['Summary'] + score_tables)
        if print_table:
            print ('{} | {:^9} | {:^9} | {:^9} | {}'.format("Summary Name", "Raw Rcore", "Quality", "Coverage", "Comprehensive"))
        for summary_name in x:
            #w.writerow([filename(summary)] + [s[n] for s in scores])
            # if os.path.isdir(summary):
            #     summ = glob.iglob(summary+'/*')
            #     for fn in summ:
            #         #if fn[:-5] == '.segs':
            #          if fn.endswith('.ls'):
            # summary_slash= summary.rfind('/') + 1
            # summary_dot = summary.rfind('.')
            # summary_name = summary[summary_slash:summary_dot]
            #             # print ("Raw score for summary ", summary_name, ": ", raw_scores[summary_name])
            output = [summary_name, raw_scores[summary_name],quality_scores[summary_name],coverage_scores[summary_name],comprehension_scores[summary_name]]
            w.writerow(output)
            if print_table:
                print ('{:<12} | {:^9} | {:^9.3f} | {:^9.3f} | {:^13.3f}'.format(summary_name, raw_scores[summary_name], quality_scores[summary_name],coverage_scores[summary_name],comprehension_scores[summary_name]))

print ('\n')
text = colored('Results written to %s' % results_file, 'blue')
print (text)
done = time()
text = colored(('Time: {}'.format(str(done - timer))), 'blue')
print (text)
#print 'Results written to %s' % results_file
print ('\n')
