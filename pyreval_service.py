# Version from WCER (UWisc sciwrite server) data Dec 04, 2023
# Library imports to run flask
# from pyreval_mongo_function import pyreval
# from urllib import request
from flask import Flask
from flask import request
from flask_cors import CORS
from flask import jsonify
from common import cache
from pathlib import Path
app = Flask(__name__)
cache.init_app(app=app, config={"CACHE_TYPE": "filesystem", 'CACHE_DIR': Path('/tmp')})
CORS(app)
app.config.from_pyfile('pyreval_config.py')

#Things to make things easier...
from pymongo import MongoClient
import pandas as pd
import numpy as np

import os
import sys
import shutil
from subprocess import call
#Wasih (02-19-20) Use functions instead of calling script
from splitsent_mongo_min import *
from Stanford.stanford import *
from Pyramid.pyramid import pyramidmain

#for randomly generating list
from random import sample

#Wasih (02-26-20) Make conditional imports depending on Python version
#Wasih (02-27-20) Define a variable for python version & then use it
PYTHON_VERSION = 2
if sys.version_info[0] == 2:
    import ConfigParser as configparser
else:
    import configparser
    PYTHON_VERSION = 3

#Wasih (02-21-20) Use termcolor to display colored text
from termcolor import colored

#Wasih (02-27-20) Use imports of traceback and logging to print any exception
import logging
import traceback

#Adithya Importing preprocess as a function
from Preprocess import preprocess_mongo_min as preprocess_functions

#Adithya Importing scoring as a function
from Scoring import scoring_mongo_maj as scoring_functions

#Importing for MongoDB Operations
from MongoDB import mongo_db_functions
from MongoDB import pyramid_operations_mongo_new

#Importing Error Object for handling Intermmediate Data
from Error_Operations import error_operations_mongo_new

#To maintain globally
from MongoDB.Models import Student_Essay_Model 

#William Goss (03-30-23)
#For submitting essays
from pymongo import MongoClient
#For sending feedback
import requests

#William Goss (03-30-23)
#Analytics
from control.typeSelector import questionType

from helpers.pageQuestionRetrieval import getQuestion
from helpers.dictCombiner import combine
from helpers.timeToList import crunchTime

#William Goss (05-15-23)
#Global Variables
config = configparser.ConfigParser()
config.read('parameters.ini')

#Variables for MongoDB
db_conn = config.get('Database', 'db_conn')
database_name = config.get('Database', 'database_name')
pre_dynamic_base_dir = config.get('DynamicPaths', 'dynamicbasedir')


def splitsent(mongodb_operations, raw_peer_dir, split_peer_dir, split_model_dir, error_operations_obj):
    #Wasih (02-19-21) Use functions instead of calling script
    #Wasih (02-21-21) Add user friendly lines
    try:
        #Wasih (02-21-21) Check for split directory present or not, if not then create it
        if not os.path.exists(split_peer_dir):
            os.makedirs(split_peer_dir)
        
        if not os.path.exists(split_model_dir):
            os.makedirs(split_model_dir)
        
        #changed for mongoDB operations
        split(raw_peer_dir, split_peer_dir, mongodb_operations, student_metadata_obj)
        # split(raw_model_dir, split_model_dir, mongodb_operations, student_metadata_obj)

        text = colored('\n\n********************Splitting of Sentences/normalization completed!********************\n\n', 'green', attrs = ['bold'])
        print (text)
        error_operations_obj.sent_split_stage = 'Sentence Splitting Complete'

    except Exception as e:
        text = colored('\n\n********************Splitting of Sentences/normalization Threw an Error!********************\n\n', 'red', attrs = ['bold'])
        logging.error(traceback.format_exc())
        error_operations_obj.insert_data(student_metadata_obj, mongodb_operations)
        #print(e)
        print (text)
    
def stanford(mongodb_operations, stanford_dir, split_peer_dir, split_model_dir, dynamic_base_dir, seg_method, base_dir, error_operations_obj):
    os.chdir(stanford_dir)
    #call(py_interp + [stanford_script, split_peer_dir, '1', base_dir])
    #call(py_interp + [stanford_script, split_model_dir, '2', base_dir])
    
    #Wasih (02-19-21) Use functions instead of calling script
    try:
        try:
            stanfordmain(split_peer_dir, 1, dynamic_base_dir, seg_method)
            error_operations_obj.stanford_core_nlp_stage = 'Stanford corenlp xml output complete'
        except Exception as e:
            logging.error(traceback.format_exc())
            print(e)
            text = colored('\n\n********************Stanford Pipelining of Sentences threw an Error!********************\n\n', 'red', attrs = ['bold'])
            error_operations_obj.insert_data(student_metadata_obj, mongodb_operations)
            print (text)
    
        os.chdir(stanford_dir)
        try:
            stanfordmain(split_model_dir, 2, dynamic_base_dir, seg_method)
            text = colored('\n\n********************Stanford Pipelining of Sentences completed!********************\n\n', 'green', attrs = ['bold'])
            error_operations_obj.stanford_core_nlp_stage = 'Stanford corenlp xml output complete'
            print (text)
        except Exception as e:
            logging.error(traceback.format_exc())
            print(e)
            text = colored('\n\n********************Stanford Pipelining of Sentences threw an Error!********************\n\n', 'red', attrs = ['bold'])
            error_operations_obj.insert_data(student_metadata_obj, mongodb_operations)
            print (text)    

    except Exception as e:
        logging.error(traceback.format_exc())
        print(e)
        text = colored('\n\n********************Stanford Pipelining of Sentences threw an Error!********************\n\n', 'red', attrs = ['bold'])
        print (text)
        error_operations_obj.insert_data(student_metadata_obj, mongodb_operations)    
    os.chdir(base_dir)

def preprocess(mongodb_operations, preprocess_dynamic_dir, preprocess_dir, base_dir, error_operations_obj):
    if not os.path.exists(preprocess_dynamic_dir):
        os.makedirs(preprocess_dynamic_dir)
    #TODO:Observe and change
    os.chdir(preprocess_dir)
    try:
        try:
            # call(py_interp + [preprocess_script, '1', preprocess_dynamic_dir, ' '.join(py_interp)])
            preprocess_functions.preprocess_function('1', preprocess_dynamic_dir, error_operations_obj)
            #preprocess('1')
        except Exception as e:
            logging.error(traceback.format_exc())
            print(e)
            text = colored('\n\n********************Preprocessing of Sentences threw an Error!********************\n\n', 'red', attrs = ['bold'])
            print (text)
            
        try:
            # call(py_interp + [preprocess_script, '2', preprocess_dynamic_dir, ' '.join(py_interp)])
            preprocess_functions.preprocess_function('2', preprocess_dynamic_dir, error_operations_obj)
            #prepro('2')
            text = colored('\n\n********************Preprocessing of Sentences completed!********************\n\n', 'green', attrs = ['bold'])
            print (text)
        except Exception as e:
            logging.error(traceback.format_exc())
            print(e)
            text = colored('\n\n********************Preprocessing of Sentences threw an Error!********************\n\n', 'red', attrs = ['bold'])
            print (text)

    except Exception as e:
        logging.error(traceback.format_exc())
        print(e)
        text = colored('\n\n********************Preprocessing of Sentences threw an Error!********************\n\n', 'red', attrs = ['bold'])
        print (text)
        error_operations_obj.insert_data(student_metadata_obj, mongodb_operations)
    os.chdir(base_dir)

def score(mongodb_operations, pyramid_dir, scoring_dir, scoring_dynamic_dir, output_filepath, log_dir, config, base_dir, error_operations_obj):

    #Changes to process pyramid from MongoDB
    pyramid_operations_object = pyramid_operations_mongo_new.PyramidOperations(student_metadata_obj.essay_number, pyramid_dir, mongodb_operations)
    pyramid_operations_object.get_pyramid()
    
    error_operations_obj.pyramid_creation_stage = 'Creation of the pyramid xml/size files from the human-readable pyramid (if applicable) complete'
    #Changing the Pyramid Directory as per student
    essay_pyramid_dir = pyramid_operations_object.dynamic_pyr_dir
    #Passing config parser as an argument
    if not os.path.exists(scoring_dir):
        os.makedirs(scoring_dir)

    os.chdir(scoring_dir)
    try:
        scoring_functions.scoring_function(scoring_dynamic_dir, essay_pyramid_dir, output_filepath, log_dir, scoring_dir, config, error_operations_obj, mongodb_operations, student_metadata_obj)
        text = colored('\n\n********************Scoring of summaries completed!********************\n\n', 'green', attrs = ['bold'])
        error_operations_obj.scoring_stage = 'Scoring Results complete'
        #Extract Intermmediate Files
        error_operations_obj.extract_file_data()
        #Push the error object to the db
        error_operations_obj.insert_data(student_metadata_obj, mongodb_operations)
        print("Score Complete")

    except Exception as e:
        logging.error(traceback.format_exc())
        print(e)
        text = colored('\n\n********************Scoring of summaries threw an Error!********************\n\n', 'red', attrs = ['bold'])
        print (text)
        #Extract Intermmediate Files
        error_operations_obj.extract_file_data()
        error_operations_obj.insert_data(student_metadata_obj, mongodb_operations)

    os.chdir(base_dir)
    

def clean(dynamic_base_dir):
    dir = dynamic_base_dir
    for files in os.listdir(dir):
        path = os.path.join(dir, files)
        try:
            shutil.rmtree(path)
        except OSError:
            os.remove(path)
    
    #Wasih (02-21-20) Print colored text for user-friendliness
    text = colored('All temporary data deleted!', 'yellow')
    print (text)    


def change_py_interp(params):
    global py_interp
    py_interp = params

def error_print(e1, e2=None):
    print('ERROR: ' + e1)
    if e2:
        print(e2)

def pyreval(student_metadata_obj_req):
    try:
        #Getting Current Working Directory
        current_dir = os.path.dirname(os.path.realpath(__file__))
        os.chdir(current_dir)

        # global mongodb_operations
        mongodb_operations = mongo_db_functions.MongoDB_Operations(db_conn)

        #Code to connect to the databse
        print(database_name)
        mongodb_operations.connect(database_name)

        #Variables for Handling Intermmediate Data and Errors
        error_operations_obj = error_operations_mongo_new.error_object()



        #TODO:Change to receive from notebook
        global student_metadata_obj
        student_metadata_obj = student_metadata_obj_req
        # student_metadata_obj = Student_Essay_Model.student_metadata('6278bd4430da3ae9a16a4527', "1", "GS", 2, "R")
        
        # base_dir = os.path.dirname(os.path.realpath(__file__))
        base_dir = config.get('DynamicPaths', 'dynamicbasedir')
        #pre_dynamic_base_dir = config.get('DynamicPaths', 'dynamicbasedir')
        # static_base_dir = config.get('StaticPaths', 'staticbasedir')

        #Changing the base dir in parameters to student's temporary folder
        #TODO: get this from parameters.ini
        dynamicbasedir = pre_dynamic_base_dir  + "/Student_" + str(student_metadata_obj.student_id)
        if not os.path.exists(dynamicbasedir):
                    os.makedirs(dynamicbasedir)
        
        config.set('DynamicPaths', 'dynamicbasedir', dynamicbasedir)

        #Student Changes end

        #Wasih (02-20-20) Make ConfigParser
        dynamic_base_dir = config.get('DynamicPaths', 'dynamicbasedir')
        raw_peer_dir = config.get('DynamicPaths', 'RawPeerDir')
        # raw_model_dir = config.get('DynamicPaths', 'RawModelDir')
        split_peer_dir = config.get('DynamicPaths', 'SplitPeerDir')
        split_model_dir = config.get('DynamicPaths', 'SplitModelDir')
        preprocess_dir = config.get('DynamicPaths', 'PreprocessDynamicDir')
        preprocess_dynamic_dir = config.get('DynamicPaths', 'PreprocessDynamicDir')
        # preprocess_peers_dir = config.get('DynamicPaths', 'PreprocessPeersDir')
        # preprocess_model_dir = config.get('DynamicPaths', 'PreprocessModelDir')
        # ext_dir = config.get('DynamicPaths', 'ExtDir')
        log_dir = config.get('DynamicPaths', 'LogDir')
        scoring_dynamic_dir = config.get('DynamicPaths', 'ScoringDynamicDir')
        output_filepath = config.get('DynamicPaths', 'OutputFile')
    
        seg_method = config.get('Segmentation', 'Method')

        # py_interp = [config.get('StaticPaths', 'PythonInterp')]
        # preprocess_script = config.get('StaticPaths', 'PreprocessScript')
        pyramid_dir = config.get('StaticPaths', 'PyramidDir')
        # pyramid_script = config.get('StaticPaths', 'PyramidScript')
        scoring_dir = config.get('StaticPaths', 'ScoringStaticDir')
        # scoring_script = config.get('StaticPaths', 'ScoringScript')
        # pyramid_name = config.get('StaticPaths', 'OutputPyramidName')
        # split_script = config.get('StaticPaths', 'SplitScript')
        stanford_dir = config.get('StaticPaths', 'StanfordDir')
        # stanford_script = config.get('StaticPaths', 'StanfordScript')
        # abcd_dir = config.get('StaticPaths', 'ABCDDir')
        # preprocess_static_dir = config.get('StaticPaths', 'PreprocessStaticDir')

        error_operations_obj.set_dir(dynamic_base_dir)



        client = MongoClient(db_conn)
        db = client[database_name]
        coll = db['PYRAMID_COLLECTION']

        docs1 = coll.find_one({
        "pyramid_id" : float(20221207),
        "pyramid_name": "essay1_pyramid_readable_20221207",
        "essay_number": 1,
        "essay_main_ideas" : ["1", "2", "3", "4", "5", "6"],
        "scu_mapping" : ["5", "0", "4", "2", "1", "3"]
        })

        #docs2 = coll.find_one({
         #    "pyramid_id": float(20231029),
          #   "pyramid_name": "essay2_pyramid_readable_20231029",
           #  "essay_number" : 2,
           #  "essay_main_ideas" : ["1", "2", "3", "4", "5", "6", "7", "8"],
           #  "scu_mapping" : ["5", "7", "4", "0", "2", "6", "3", "1"]  })
        # if the pyramid isn't found, populate the database
        # if not docs1:
        #     populate_pyramid_table_mongo_new.populate_pyramid1()
#        if not docs2:
#            populate_pyramid_table_mongo_new.populate_pyramid2()

    
        splitsent(mongodb_operations, raw_peer_dir, split_peer_dir, split_model_dir, error_operations_obj)
        stanford(mongodb_operations, stanford_dir, split_peer_dir, split_model_dir, dynamic_base_dir, seg_method, base_dir, error_operations_obj)
        preprocess(mongodb_operations, preprocess_dynamic_dir, preprocess_dir, base_dir, error_operations_obj)
        score(mongodb_operations, pyramid_dir, scoring_dir, scoring_dynamic_dir, output_filepath, log_dir, config, base_dir, error_operations_obj)

        # Uncomment the below line if needed to clear the temporary data 
        # clean(dynamic_base_dir)
        #Inserting Debug Data after every stage is affecting performance, TODO: have to work on the error case scenario.

    except Exception as e:
        error_operations_obj.insert_data(student_metadata_obj, mongodb_operations)
        print('Error %s' %e)

'''

    Save a new essay
    @param essay_obj Dictionary object { student_id, class_id, page_id, teacher_id, essay_number, essay_version, essay } 
    Expects global database_name to be set in caller

'''
def save_essay(essay_obj):
    client = MongoClient(db_conn)
    #database_name is global
    db = client[database_name]
    coll = db['STUDENT_ESSAYS_COLLECTION']
    docs = coll.find_one({"student_metadata.student_id": essay_obj['student_id'], "student_metadata.class_id": essay_obj['class_id'],
                          "student_metadata.page_id": essay_obj['page_id'], "student_metadata.teacher_id": essay_obj['teacher_id'],
                          "student_metadata.essay_number": essay_obj['essay_number'], "student_metadata.essay_version": essay_obj['essay_version']})
    #if the essay isn't found, check again without "page_id" (backwards compatible with records prior to "page_id" addition)
    if not docs:
        docs = coll.find_one({"student_metadata.student_id": essay_obj['student_id'], "student_metadata.class_id": essay_obj['class_id'],
                              "student_metadata.teacher_id": essay_obj['teacher_id'], "student_metadata.essay_number": essay_obj['essay_number'], 
                              "student_metadata.essay_version": essay_obj['essay_version']})
    #the essay doesn't exist yet, so insert it into the database
    if not docs:
        student_metadata = {'student_id': essay_obj['student_id'], 'class_id': essay_obj['class_id'], 'page_id': essay_obj['page_id'], 'teacher_id': essay_obj['teacher_id'], 'essay_number': essay_obj['essay_number'], 'essay_version': essay_obj['essay_version'] }
        coll.insert_one({"student_metadata": student_metadata, "essay_text": essay_obj['essay']})

'''
    
    Process all unprocessed essays with PyrEval and post results to the Notebook
    Expects global database_name to be set in caller

'''
def process_submitted_essays():
    client = MongoClient(db_conn)
    #database_name is global
    db = client[database_name]
    collection = db['STUDENT_ESSAYS_COLLECTION']
    #get all documents with no results (if there is no result, then it means it has not been processed)
    docs = collection.find({'result': None})
    for doc in docs:
        #for each doc (essay), get the student's metadata
        student_id = doc['student_metadata']['student_id']
        class_id = doc['student_metadata']['class_id']
        page_id = doc['student_metadata']['page_id']
        teacher_id = doc['student_metadata']['teacher_id']
        essay_number = doc['student_metadata']['essay_number']
        essay_version = doc['student_metadata']['essay_version']
        student_metadata_obj_req = Student_Essay_Model.student_metadata(student_id, class_id, teacher_id, essay_number, essay_version)
        #process the essay with PyrEval
        pyreval(student_metadata_obj_req)
        student_metadata = {'student_id': student_id, 'class_id': class_id, 'page_id': page_id, 'teacher_id': teacher_id, 'essay_number': essay_number, 'essay_version': essay_version }
        doc = collection.find_one({"student_metadata": student_metadata})
        #get the cu_vector and essay_text after the essay is processed
        cu_vector = doc['cu_vectors']
        essay_text = doc['essay_text']
        #local server
        #notebook_url = 'http://localhost:3000/api/pyreval/receive_feedback'
        #real server
        notebook_url = 'https://sciwrite.wcer.wisc.edu/api/pyreval/receive_feedback'
        #create a feedback object to send back to the notebook, which knows how to parse it to give the students feedback
        feedback_obj = {'feedback': cu_vector, 'essay_version': essay_version, 'student_id': student_id, 'class_id': class_id, 'page_id': page_id, 'essay_text': essay_text}
        x = requests.post(notebook_url, json = feedback_obj)

'''

    The route "/" is useful for checking if the flask server is
    up and running.

'''

#Code to run flask
@app.route("/")
def Initial_Page():
    # pyreval()
    return "<h1>Gunicorn Deployed and Running</h1>"

'''

    /flask_with_request is the initial submission logic that Adithya implemented.
    Due to memory limitations on the server, this API is no longer used. I'm
    keeping it here since it could still theorhetically be used.


'''    

@app.route("/flask_with_request", methods=['POST'])
def pyreval_request():
    request_data = request.get_json()
    student_id = request_data["student_id"]
    class_id = request_data["class_id"]
    teacher_id = request_data["teacher_id"]
    essay_number = int(request_data["essay_number"])
    essay_version = request_data["essay_version"]
    student_metadata_obj_req = Student_Essay_Model.student_metadata(student_id, class_id, teacher_id, essay_number, essay_version)
    #database_name is global here since it is changed for production and guests.
    global database_name
    database_name = config.get('Database', 'database_name')
    pyreval(student_metadata_obj_req)
    return "<h1>" "Processing done for" + student_id + "</h1>"

'''

    /submit_essay is the current (11-29-23) used method in production for
    students or teachers to submit essays.

'''

@app.route("/submit_essay", methods=['POST'])
def submit_essay():
    #get relevant attributes
    request_data = request.get_json()
    essay_obj = {
        "student_id": request_data["student_id"],
        "class_id": request_data["class_id"],
        "page_id": request_data["page_id"],
        "teacher_id": request_data["teacher_id"],
        "essay_number": int(request_data["essay_number"]),
        "essay_version": request_data["essay_version"],
        "essay": request_data["essay"]
    }
    #database_name is global to switch the database for production and guests
    global database_name
    database_name = config.get('Database', 'database_name')
    save_essay(essay_obj)
    return "Essay Received"

'''

    /process_essays is the current (11-29-23) API for processing
    all the production (students/teachers from an implementation).

'''

@app.route("/process_essays", methods=['GET'])
def process_essays():
    process_lock = cache.get("lock")
    if process_lock == None:
        process_lock = False
    if process_lock:
        return "PyrEval is already running."
    else:
        cache.set("lock", True)
    #database_name is global to switch between production/guests
    global database_name
    database_name = config.get('Database', 'database_name')
    #find and process unprocessed essays
    process_submitted_essays()
    cache.set("lock", False)
    return "Processed!"

'''

    /guest_submit_essay is the current (11-29-23) API for submitting
    guest essays to the database. The logic is the same as the above API
    named /submit_essay, just the database_name is changed to 'Guests'
    to access the correct database.

'''

#Guest submission functionality
@app.route("/guest_submit_essay", methods=['POST'])
def guest_submit_essay():
    #get relevant attributes
    request_data = request.get_json()
    essay_obj = {
        "student_id": request_data["student_id"],
        "class_id": request_data["class_id"],
        "page_id": request_data["page_id"],
        "teacher_id": request_data["teacher_id"],
        "essay_number": int(request_data["essay_number"]),
        "essay_version": request_data["essay_version"],
        "essay": request_data["essay"]
    }
    #database_name is global to switch between production/guests
    global database_name
    database_name = 'Guests'
    save_essay(essay_obj)
    return "Essay Received"

'''

    /process_guests is the current (11-29-23) API for processing
    guest essays with PyrEval. The API is almost the same as the above
    API, /process_essays, other than the global variable 'database_name'
    being changed to 'Guests' to process the guest essays.

'''

#Guest processing functionality
@app.route("/process_guests", methods=['GET'])
def process_guests():
    process_lock = cache.get("lock")
    if process_lock == None:
        process_lock = False
    if process_lock:
        return "PyrEval is already running."
    else:
        cache.set("lock", True)
    #database_name is global to switch between production/guests
    global database_name
    database_name = 'Guests'
    #find and process unprocessed essays
    process_submitted_essays()
    cache.set("lock", False)
    return "Processed!"


'''

Guest deleted logic

If there are essays submitted but havent been processed, they need to be removed
since there is no student answer document to receive them on the notebook

'''

@app.route("/guest_deleted", methods=['POST'])
def guest_deleted():
    request_data = request.get_json()
    student_id = request_data["student_id"]
    client = MongoClient(db_conn)
    #Changing database_name to direct it at 'Guests'
    global database_name
    database_name = 'Guests'
    db = client[database_name]
    coll = db['STUDENT_ESSAYS_COLLECTION']
    coll.delete_many({'student_metadata.student_id': student_id, 'result': None})
    return "Deleted"

@app.route("/status", methods=['GET'])
def pyreval_status():
    client = MongoClient(db_conn)
    global database_name
    database_name = 'Guests'
    guest_db = client[database_name]
    guest_collection = guest_db['STUDENT_ESSAYS_COLLECTION']
    guest_docs = guest_collection.find({'result': None})
    guest_count = 0
    for doc in guest_docs:
        guest_count = guest_count + 1
    database_name = config.get('Database', 'database_name')
    db = client[database_name]
    collection = db['STUDENT_ESSAYS_COLLECTION']
    docs = collection.find({'result': None})
    prod_count = 0
    for doc in docs:
        prod_count = prod_count + 1
    process_lock = cache.get("lock")
    if process_lock == None:
        process_lock = False
    data = {"production": prod_count, "guest": guest_count, "lock": process_lock}
    return jsonify(data)


'''

    /analyze is used for the teacher dashboard summary information.
    Python is better at parsing data and generating summaries than
    JavaScript, so it is handled here.

'''

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json(silent=True)
    # Solutions and page should always have data
    if 'classAnswers' not in data:
        return "No Data"
    classAnswers = data['classAnswers']
    solutions = data['solutions']
    pageData = data['page']
    results = questionType(solutions, classAnswers)
    timeData = crunchTime(data['time'])
    questions = getQuestion(results, pageData)
    returnData = combine(results, questions, timeData)
    return returnData

@app.route('/unlock', methods=['GET'])
def unlock():
	cache.set("lock", False)
	return "Unlocked"

if __name__ == "__main__":
    app.run(debug = True, port = 5000)


'''

    Storing historical APIs below this.
    None of these are being used, but they were used in the past.

'''
'''

    /guest_resubmit_essay was used when resubmission was possible.
    Handled the resubmission logic for Guest accounts.

#Guest resubmission logic
@app.route("/guest_resubmit_essay", methods=['POST'])
def guest_resubmit():
    request_data = request.get_json()
    student_id = request_data["student_id"]
    class_id = request_data["class_id"]
    teacher_id = request_data["teacher_id"]
    essay_number = int(request_data["essay_number"])
    essay_version = request_data["essay_version"]
    essay = request_data["essay"]
    client = MongoClient(db_conn)
    global database_name
    database_name = 'Guests'
    db = client[database_name]
    coll = db['STUDENT_ESSAYS_COLLECTION']
    docs = coll.find({"student_metadata.student_id": student_id, "student_metadata.class_id": class_id,
                      "student_metadata.teacher_id": teacher_id, "student_metadata.essay_number": essay_number,
                      "student_metadata.essay_version": essay_version})
    count = 0
    for x in docs:
        count = count + 1
    #if count is greater than 0, it means the submission is there and has not been run yet
    if count > 0:
        #update the essay for resubmission
        coll.update_one({"student_metadata.student_id": student_id, "student_metadata.essay_version": essay_version, "student_metadata.essay_number": essay_number}, {"$set": { "essay_text": essay}})
    elif count == 0:
        #somehow the student submitted, but their essay didn't save and now they are resubmitting
        student_metadata = {'student_id': student_id, 'class_id': class_id, 'teacher_id': teacher_id, 'essay_number': essay_number, 'essay_version': essay_version }
        coll.insert_one({"student_metadata": student_metadata, "essay_text": essay})
    return "Resubmission Complete"

'''

'''

    /resubmit_essay was used when resubmission was possible.
    Handled the resubmission logic for production (Students/Teachers from implementation) accounts.

@app.route("/resubmit_essay", methods=['POST'])
def resubmit():
    request_data = request.get_json()
    student_id = request_data["student_id"]
    class_id = request_data["class_id"]
    teacher_id = request_data["teacher_id"]
    essay_number = int(request_data["essay_number"])
    essay_version = request_data["essay_version"]
    essay = request_data["essay"]
    client = MongoClient(db_conn)
    global database_name
    database_name = config.get('Database', 'database_name')
    db = client[database_name]
    coll = db['STUDENT_ESSAYS_COLLECTION']
    docs = coll.find({"student_metadata.student_id": student_id, "student_metadata.class_id": class_id,
                      "student_metadata.teacher_id": teacher_id, "student_metadata.essay_number": essay_number,
                      "student_metadata.essay_version": essay_version})
    count = 0
    for x in docs:
        count = count + 1
    #if count is greater than 0, it means the submission is there and has not been run yet
    if count > 0:
        #update the essay for resubmission
        coll.update_one({"student_metadata.student_id": student_id, "student_metadata.essay_version": essay_version, "student_metadata.essay_number": essay_number}, {"$set": { "essay_text": essay}})
    elif count == 0:
        #somehow the student submitted, but their essay didn't save and now they are resubmitting
        student_metadata = {'student_id': student_id, 'class_id': class_id, 'teacher_id': teacher_id, 'essay_number': essay_number, 'essay_version': essay_version }
        coll.insert_one({"student_metadata": student_metadata, "essay_text": essay})
    return "Resubmission Complete"

'''
'''

    /check_gs was a custom API for comparing the ground truth essays
    to the Truth_Cases.csv file in the testsuite folder. It would
    show the studentId, PyrEval result, and Truth_Cases.csv result
    in the browser. 

    **This won't work if there are more documents than the initial
    forty. It could be updated to work when additional essays are in
    the database, but does not work that way now.**

@app.route("/check_gs", methods=['GET'])
def gs_check():
    client = MongoClient(db_conn)
    global database_name
    database_name = config.get('Database', 'database_name')
    db = client[database_name]
    collection = db['STUDENT_ESSAYS_COLLECTION']
    #Should only run if there are 40 documents
    if collection.count_documents({}) != 40:
        return "Too many documents"
    docs = collection.find()
    results = []
    cwd = os.path.dirname(os.path.realpath(__file__))
    gs_results = cwd + "/testsuite/Truth_Cases.csv"
    df = pd.read_csv(gs_results)
    for doc in docs:
        if 'cu_vectors' in doc:
            student_id = doc['student_metadata']['student_id']
            original_student_id = student_id
            essay_version = doc['student_metadata']['essay_version']
            cu_vec = doc['cu_vectors']
            #.txt has to be added to any student_id with essay in it
            if 'essay' in student_id:
                #edge case
                if student_id in ['essay_energy.mass.3.190@test.com', 'essay_energy.mass.3.235@test.com']:
                    segStudent = student_id.split('_')
                    segStudent[0] = 'essay1'
                    newStudentId = '_'.join(segStudent)
                    student_id = newStudentId + '.txt'
                    selRow = df.loc[(df['Id']  == student_id) & (df['Essay Version'] == essay_version)]
                else:
                    student_id = student_id + '.txt'
                    selRow = df.loc[(df['Id']  == student_id) & (df['Essay Version'] == essay_version)]
            else:
                selRow = df.loc[(df['Id']  == student_id) & (df['Essay Version'] == essay_version)]
            selVal = selRow.values.tolist()
            gs_cu_vec = selVal[0][2:-1]
            check = np.array_equal(np.array(cu_vec), np.array(gs_cu_vec))
            results.append(original_student_id + ' -- ' + ', '.join(map(str, cu_vec)) + ' -- ' + ', '.join(map(str, gs_cu_vec)) + ' -- ' + str(check))
    return results

'''

'''

    /batch_process was used original when running the ground truth
    essays. It is also the original logic for how process_essays
    and process_guests function now.

@app.route("/batch_process", methods=['GET'])
def batch_pyreval():
    #config = configparser.ConfigParser()
    #config.read('parameters.ini')
    #db_conn = config.get('Database', 'db_conn')
    #database_name = config.get('Database', 'database_name')
    client = MongoClient(db_conn)
    global database_name
    database_name = config.get('Database', 'database_name')
    db = client[database_name]
    collection = db['STUDENT_ESSAYS_COLLECTION']
    docs = collection.find({'result': None})
    for doc in docs:
        student_id = doc['student_metadata']['student_id']
        class_id = doc['student_metadata']['class_id']
        teacher_id = doc['student_metadata']['teacher_id']
        essay_number = doc['student_metadata']['essay_number']
        essay_version = doc['student_metadata']['essay_version']
        student_metadata_obj_req = Student_Essay_Model.student_metadata(student_id, class_id, teacher_id, essay_number, essay_version)
        print(student_metadata_obj_req)
        pyreval(student_metadata_obj_req)
    return "Done"

'''
