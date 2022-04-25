import os
import shutil
import time
import sys
import configparser
import itertools
from pyreval import splitsent, stanford
from splitsent import split
from Stanford.stanford import *
from Pyramid.pyramid import pyramidmain


basedir = "/home/nlp/pxs288/SU21/PyrEval/PyrEval_0615/"
homedir = basedir+"Datasets"
rawdir = basedir+"Raw"
preprocessdir = basedir+"Preprocess"
pyramiddir = basedir+"Pyramid"
scoredir = basedir+"Scoring"
resultdir = basedir+"Results"
stanforddir = basedir+"Stanford"


def cleanup():
    print("Cleaning up previous iteration files")
    shutil.rmtree(rawdir)
    os.mkdir(rawdir)
    # shutil.rmtree(preprocessdir+"/wise_crowd_summaries")
    # os.mkdir(preprocessdir+"/wise_crowd_summaries")
    # shutil.rmtree(preprocessdir+"/peer_summaries")
    # os.mkdir(preprocessdir+"/peer_summaries")
    shutil.rmtree(basedir+"/log")
    os.mkdir(basedir+"/log")
    #shutil.rmtree(resultdir)
    #os.mkdir(resultdir)

start = time.time()
counter = 0

for x in sorted(os.listdir(homedir), reverse=True):
    print(x)
    try:
        cleanup()
    except:
        pass
    res = os.path.join(resultdir,x)
    if x ==".DS_Store":
        continue
    if not os.path.isdir(res):
        os.mkdir(res)
    else:
        pass
    tempdir = os.path.join(homedir, x) 
    print("Working on dataset "+ x)
    for each in os.listdir(tempdir):
        # if os.path.isdir(tempdir+"/"+each):
        #     continue
        shutil.copytree(os.path.join(tempdir,each), os.path.join(rawdir,each))
        if not os.path.exists(os.path.join(rawdir,each,'split'):
            os.mkdir(os.path.join(rawdir,each,'split')


    split(os.path.join(rawdir,'model'), os.path.join(rawdir,'model','split'))
    split(os.path.join(rawdir,'peers'), os.path.join(rawdir,'model','peers'))

    # splitsent('')
    # stanford('')
    print("Stanford")
    os.chdir(stanforddir)
    stanfordmain(os.path.join(rawdir,'model','split'), 1, basedir)
    os.chdir(stanforddir)
    stanfordmain(os.path.join(rawdir,'model','peers'), 2, basedir)

    # sys.exit()
    print("Preprocessing")
    os.chdir(preprocessdir)
    os.system("python preprocess.py 1")
    os.system("python preprocess.py 2")
    
            

    
    os.chdir(basedir)
    parser = configparser.ConfigParser()
    parser.read('parameters.ini')
    parser.set('Paths', 'OutputPyramidName', x)
    
    if not os.path.exists(os.path.join(scoredir, 'scu')):
        os.makedirs(os.path.join(scoredir, 'scu'))
    
    if not os.path.exists(os.path.join(scoredir, 'sizes')):
        os.makedirs(os.path.join(scoredir, 'sizes'))

    if not os.path.exists(os.path.join(scoredir, 'pyrs', 'pyramids')):
        os.makedirs(os.path.join(scoredir, 'pyrs', 'pyramids'))
    
    if not os.path.exists(os.path.join(scoredir,'temp')):
        os.makedirs(os.path.join(scoredir, 'temp'))

    if not os.path.exists(os.path.join(scoredir,'temp')):
        os.makedirs(os.path.join(scoredir, 'temp'))
    
    with open('parameters.ini', 'w') as f:
        parser.write(f)

    os.chdir(pyramiddir)
    # if 'av' not in x:
    pyramidmain(x)

    topk = ['2', '4', '8']
    sorting = ['product', 'stddev', 'cosine', 'normsum']
    weighting = ['product', 'stddev', 'cosine', 'normsum']
    scheme = ["sum", "max", "average"]

    comb = itertools.product(topk, sorting, weighting, scheme)

    for config in comb:
        conf_str = '_'.join(config)

        os.chdir(basedir)
        parser = configparser.ConfigParser()
        parser.read('parameters.ini')
        parser.set('Scoring_Params', 'TopKScus', config[0])
        parser.set('Scoring_Params', 'SortingMetric', config[1])
        parser.set('Scoring_Params', 'WeightingMetric', config[2])
        parser.set('Scoring_Params', 'WeightScheme', config[3])
        with open('parameters.ini', 'w+') as f:
            parser.write(f)
        
        os.chdir(scoredir)
        os.system("python scoring.py -t -l -a")
        
        os.chdir(res)
        os.mkdir(conf_str)

        shutil.copytree(os.path.join(basedir,"log"), os.path.join(res, conf_str,"log"))
        shutil.move(os.path.join(scoredir,"results.csv"), os.path.join(res,conf_str))
        
        counter += 1
        
    os.chdir(scoredir)
    for each in os.listdir("sizes"):
        shutil.move(os.path.join("sizes", each), res)
    
    for each in os.listdir("scu"):
        shutil.move(os.path.join("scu", each), res)
    
    for each in os.listdir(os.path.join("pyrs","pyramids")):
        shutil.move(os.path.join("pyrs","pyramids",each), res)
    
    os.chdir(homedir)           


end = time.time()
print(str(counter)+" configurations processed. Time elapsed = "+ str(end-start))
