#Preprocessing xml files from stanford corenlp 
#Copyright (C) 2017  Yanjun Gao

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import glob
import sys
from time import time
from Preprocess.lib_preprocessing_mongo_min import *

#Wasih (02-21-20) Use termcolor to display colored text; user friendly
from termcolor import colored

PYTHON_VERSION = 2
if sys.version_info[0] == 2:
	import ConfigParser as configparser
else:
	import configparser
	PYTHON_VERSION = 3



def get_sentence_file(summary_name, mode):
	summary_name_only = os.path.split(summary_name)[1]
	summary_name_only = summary_name_only[:-4]
	if mode == '1':
		prepend_path = '../Raw/peers/split'
	else:
		prepend_path = '../Raw/model/split'
	sentence_file = os.path.join(prepend_path, summary_name_only)
	return sentence_file

# mode = sys.argv[1]

#mode = 2

"""
=============== MAIN ===================
"""


#Adithya Tanam - Converting the script into a function
def preprocess_function( mode, preprocess_dynamic_dir, error_operations_obj):
	#Wasih (06-20-21) Read vectorization method from parameters file
	config = configparser.ConfigParser()
	parameter_path = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'parameters.ini'))
	config.read(parameter_path)
	#Wasih (06-25-21) Read segmentation method from parameters file

	segmentation_method = config.get('Segmentation', 'Method')
	vector_method = config.get('Vectorization', 'Method')
	abcd_dir = config.get('StaticPaths', 'ABCDDir')
	glove_dir = config.get('Segmentation', 'GloveDir')

	#summaries = [sys.argv[1]]
	peer_summaries = []
	wise_crowd = []
	test_summaries = []
	timer = time()

	# Changing to dynamic preprocess folder
	# preprocess_dynamic_dir = config.get('DynamicPaths', 'preprocessdynamicdir')
	# preprocess_dynamic_dir = sys.argv[2]


	error_file = os.path.join(preprocess_dynamic_dir, 'errors-file.txt')
	errors = [] 
	#Wasih (02-19-20) Use functions instead of calling script (mode is already integer)
	if int(mode) == 1:
		dir1 = os.path.join(preprocess_dynamic_dir, 'peer_summaries')
	elif int(mode) == 2:
		dir1 = os.path.join(preprocess_dynamic_dir, 'wise_crowd_summaries')
	#elif int(mode) == 3:
		#dir1 = "../Preprocess/test_summaries"
	else:
		dir1 = None
		print ("Option doesn't exist!!!")

	if (dir1):
		if segmentation_method == 'ABCD':
			summaries = sorted(list(glob.iglob(dir1 + '/*.out')))
		else:
			summaries = sorted(list(glob.iglob(dir1 + '/*.xml')))
		for n, summary in enumerate(summaries):
			#try:
			sentence_file = get_sentence_file(summary, mode)
			#Updating summary to only have file name
			DecomposeSummary(summary, n + 1, dir1, segmentation_method, sentence_file, abcd_dir, glove_dir)
			error_operations_obj.seg_file_creation_stage = 'Lib_parser (decomposition parser) has completed creating the seg files'
			#summary, seg_ids = CleanSegmentations(summary, dir1,n+1)
			VectorizeSummary(summary, dir1, n + 1, 'preprocess', vector_method)
			error_operations_obj.ls_file_creation_stage = 'Creation of the ls files completed'
			#except:
			#	print "current file failed: ", n, " ", summary
			#	errors.append(summary)
		
		#with open(error_file,'w') as f:
		#	for each in errors:
		#		f.write(each)
	done = time()

	text = colored(('Time: {}'.format(str(done - timer))), 'blue')
	print (text)
	#print('Time: {}'.format(str(done - timer)))

	#if int(mode) ==2:
	#	command = 'mv ../Preprocess/wise_crowd_summaries ../Pyramid/wise_crowd'
	#	os.system(command)

