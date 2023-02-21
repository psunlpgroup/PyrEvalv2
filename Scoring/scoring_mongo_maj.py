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
#Last updated by Mahsa (02-17-2023)
from MongoDB.mongo_db_functions import MongoDB_Operations
from Scoring.lib_scoring_mongo_min import *
#from lib_scoring import sentencesFromSegmentations, SummaryGraph, buildSCUcandidateList, filename, getsegsCount
#from lib_scoring import getScore, getLayerSizes, processResults, scusBySentences, maxRawScore, readPyramid, new_getlayersize
from scipy.stats import pearsonr as pearson
from scipy.stats import spearmanr as spearman
#from printEsumLog import printEsumLogWrapper 
from Scoring.printEsumLog_mongo_maj import *
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
import main_ideas_dictionary

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

def get_results(elogs_path, result_obj):
    data = ""
    lines = []

    int_results = []
    float_results = []

    pyramid_id = 0

    with open(elogs_path+"/" + os.listdir(elogs_path)[0], "r") as file:
        data = file.read()

    with open(elogs_path + "/" + os.listdir(elogs_path)[0], "r") as file:
        lines = file.readlines()

        pyramid_id = lines[2].split("_")[1].split(".")[0]

        for line in lines[4:7]:
            int_results.append(int(line.split(": ")[1]))

        for line in lines[7:12]:
            float_results.append(float(line.split(": ")[1]))

        content_unit_list = (lines[13].split(": "))[1].replace(" \n","")


    result_obj.no_of_segments = int_results[0]
    result_obj.pyramid_name = int(pyramid_id)
    result_obj.raw = int_results[1]
    result_obj.max_score = int_results[2]
    result_obj.quality = float_results[0]
    result_obj.avg_scu = float_results[1]
    result_obj.max_score_avg_scu = float_results[2]
    result_obj.coverage = float_results[3]
    result_obj.comprehensive = float_results[4]
    result_obj.content_unit_list = content_unit_list
    sentences = data.split("Sentence:")[1:]


    sentence_match_dict = {}
    for sent in sentences:
        segments_dict = {}

        for seg in sent.split("\n\n")[1:-1]:
            seg_index = int(seg.split("| Content Unit:")[0].split("ID:")[1])
            segments_dict['Segment ID: ' + str(seg_index)] = seg.split("| ")[1]

        segment_id = int(sent.split("\n")[0].split("| Segmentation: ")[0])
        segmentation = int(sent.split("\n")[0].split("| Segmentation: ")[1])

        sentence_match_dict['Sentence ' + str(segment_id)+", Segmentation "+str(segmentation)] = segments_dict

    result_obj.sentence_match_dict = sentence_match_dict
    return result_obj





##Adithya:- Rearranging the code to run as  function

def scoring_function(scoring_dir, pyramid_path, results_file, log, scoring_static_dir, config, error_operations_obj, mongodb_operations, student_metadata_obj):

    """
    ============================ Input==============================
    """
    #dir1 = sys.argv[1]

    #dataset_ind = sys.argv[1]
    #Wasih (02-21-20) results.csv not generating
    timer = time()

    # config = configparser.ConfigParser()
    # config.read('../parameters.ini')

    #Changing base directory to student directory
    # scoring_dir = sys.argv[1]
    if not os.path.exists(scoring_dir):
        os.makedirs(scoring_dir)
    os.chdir(scoring_dir)

    #Puru (11-03-21) Fixed bugs with -l -t -a
    #Adithya: As we cant use parse_args() with Gunicorn I changed the options to variables

    parser = optparse.OptionParser()
    parser.add_option('-a', '--all', action="store_true", dest="a", default=False)
    parser.add_option('-t', '--table', action="store_true", dest="t", default=False)
    parser.add_option('-p', '--pyramid', action="store", dest="pyramid", default="pyrs/pyramids")
    #parser.add_option('-o', '--output', action="store", dest='output', default='../results.csv')
    #Wasih (02-21-20) results.csv not generating
    parser.add_option('-o', '--output', action="store", dest='output', default= results_file) #config.get('DynamicPaths', 'OutputFile')

    parser.add_option('-l', '--log', action='store', dest='log', default=True)
    parser.add_option('-m', '--model', action='store', dest='model', default=1)
    parser.add_option('-n', '--numsmodel', action='store', dest='numsmodel', default=False)
    #Wasih 04-13-21 Add flag for return type data structure for notebook
    parser.add_option('-r', '--returnflag', action='store', dest='returnflag', default=False)

    # options, args = parser.parse_args()
    all_store_true, table_store_true, options_numsmodel, options_returnflag = False, False, False, False
    print_all = all_store_true #options.a
    print("Print All booleanb value:", print_all)
    print_table = table_store_true#options.t
    # pyramid_path = options.pyramid
    # pyramid_path = sys.argv[2]

    # results_file = options.output
    # results_file = sys.argv[3]

    # log = options.log
    # log = sys.argv[4]

    # scoring_static_dir = sys.argv[5]

    #Wasih 04-07-21: If log folder is not there create it
    if log or print_all:
        if not os.path.exists('../log'):
            os.makedirs('../log')

    # model = options.model
    #pyramids = list(glob.iglob(pyramid_path + '*.pyr'))
    pyramids = list(glob.iglob(pyramid_path + '/*.pyr'))
    #pyramids = list(glob.iglob(dir1+"/*.pyr"))
    summaries = list(glob.iglob('../Preprocess/peer_summaries/*'))
    numsmodel = len(list(glob.iglob('../Preprocess/wise_crowd_summaries/*.xml')))
    #Wasih (07-15-21) If ABCD is used, then instead of xml, '.out' files will be there
    if numsmodel == 0:
        numsmodel = len(list(glob.iglob('../Preprocess/wise_crowd_summaries/*.out')))

    #Wasih 07-04-21 Override numsmodel with parser if present
    # if options.numsmodel:
    if options_numsmodel:
        numsmodel = options_numsmodel
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
    ====================== Scoring Pipeline ========================
    """

    #Puru (11-03-21) Implemented Threading. Commented out since did not improve performance

    for pyramid in pyramids:
        raw_scores = {}
        quality_scores = {}
        coverage_scores = {}
        comprehension_scores = {}

        #TODO find out why it gets pyramid id
        pyramid_name = pyramid[pyramid.rfind('/') + 1:pyramid.rfind('.')]
        pyramid_id = int(pyramid[pyramid.rfind('Pyramid_')+8:pyramid.rfind('.')-2])

        #print "test"
        dynamic_base_dir = scoring_dir.replace("/Scoring", '')
        scus_og, scu_labels = readPyramid(pyramid, dynamic_base_dir, config, error_operations_obj)
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
                        score(copy.deepcopy(scus_og), fn, raw_scores, quality_scores, coverage_scores, comprehension_scores, pyramid, pyramid_name, scu_labels, numsmodel, print_all, log, options_returnflag, cu_matches, group_matches, mongodb_operations, student_metadata_obj)
                        # threads[-1].start()

        # for i in range(len(threads)):
        #     threads[i].join()
        # if print_table:
            #results_f =
            ### For DUC05


        # Adithya Tanam: Getting notebook input generation and descriptive spreadsheets

        cu_vectors_json_path = scoring_static_dir + "/cu_vectors.json"
        grouping_vectors_path = scoring_static_dir + "/grouping_vectors.json"
        cu_vectors_csv_path = dynamic_base_dir + "/Scoring/cu_vectors.csv"
        enotebook_cu_vectors_csv_path = dynamic_base_dir + "/Scoring/cu_vectors_enotebook.csv"
        grouping_vectors_csv_path = scoring_static_dir + "/group_vectors.csv"
        log_path = dynamic_base_dir+'/log'
        elog_path = log_path + "_enotebook"

        # Puru 02/17/22 Extension for Notebook Input generation and descriptive spreadsheets
        #Commented grouping_vectors.csv& grouping_vectors.json & cu_vectors.json
        # with open(cu_vectors_json_path, 'w') as f:
        #     json.dump(cu_matches, f)
        # with open(grouping_vectors_path, 'w') F f:
        #     json.dump(group_matches, f)
        # Take input from file for the grouping names once file is decided
        cu_df = pd.DataFrame.from_dict(cu_matches, orient='index')
        cu_df = cu_df.sort_index()

        scu_mapping_list = mongodb_operations.get_scu_mapping(pyramid_id)
        essay_main_ideas_list = mongodb_operations.get_essay_main_ideas(pyramid_id)

        main_ideas_dictionary.reorder_cu_vectors(cu_df,enotebook_cu_vectors_csv_path,scu_mapping_list,essay_main_ideas_list,True)
        mongodb_operations.update_cu_vectors(student_metadata_obj,enotebook_cu_vectors_csv_path)
        with open(cu_vectors_csv_path, 'w') as f:
            cu_df.to_csv(f)
        # gp_df = pd.DataFrame.from_dict(group_matches, orient='index', columns = ['A', 'B', 'C', 'D'])
        # gp_df = gp_df.sort_index()
        # with open(grouping_vectors_csv_path, 'w') as f:
        #     gp_df.to_csv(f)
        main_ideas_dictionary.replace_log(log_path,elog_path,scu_mapping_list,essay_main_ideas_list,True)
        result_obj = Result_Model.result_data()
        result_obj = get_results(elog_path,result_obj)
        mongodb_operations.update_result(result_obj, student_metadata_obj)

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
