#Wasih (02-21-20) Add more structure
#Wasih (02-27-20) Use relative imports for Python3. Doesn't work otherwise?
from .lib_pyramid import *

#from lib_pyramid import readFiles, make_segs, pairwise, power_law, ComposeLayer2
#from lib_pyramid import ComposeSegSets, SortDescendingWAS, BestFit, CheckConstraint1
#from lib_pyramid import localBackTracking, RecursiveSettling, ComposeLayer1, Layer, GLobalBT
#from lib_pyramid import pairwise_test

import warnings
from .sanitycheck import * 
warnings.filterwarnings("ignore", category=DeprecationWarning) 
from time import time
import copy
import glob
import itertools
import xml.etree.cElementTree as ET
import csv
import sys
import pandas as pd 
import pdb 

import ast

#Wasih (02-21-20) Use termcolor for displaying important messages (user-friendly)
from termcolor import colored

#Wasih (02-27-20) Use conditional code according to Python Version

PYTHON_VERSION = 2
if sys.version_info[0] == 3:
	PYTHON_VERSION = 3

"""
=========================== Pipeline =================================
""" 
#Wasih (02-19-20) Use functions instead of calling script
def pyramidmain(pyr_name):
	#fname = sys.argv[1]

	#directories = list(glob.iglob(dir1+'/*'))
	#dataset_path = sys.argv[1]
	#sum_dir = dataset_path + "/Preprocess/wise_crowd_summaries/*"
	### Normal path 
	directories = list(glob.iglob('../Preprocess/wise_crowd_summaries/*'))

	### Paper experiment
	#directories = list(glob.iglob(sum_dir))

	#summ_dir = sys.argv[1]

	#directories = list(glob.iglob(summ_dir+'/Preprocess/wise_crowd_summaries/*'))

	#fname = "RAMDS-Topic-"+ summ_dir[summ_dir.rfind("/")+1:]

	#fname = "RAMDS-Topic-9"
	print (directories)
	segs, vecs, N = readFiles(directories)
	#print("Making Segments")
	segpool = make_segs(segs, vecs)
	print (len(segpool))
	pairwise_test(segpool, N)
	allsegs = [i.id for i in segpool]

	#time_records = str(N)+"-models-time.csv"

	sumlst = [i.id.split(".")[0] for i in segpool]
	sentlst = [i.id.split(".")[1] for i in segpool]
	segmtlst = [i.id.split(".")[2] for i in segpool]
	seglst = [i.id.split(".")[3] for i in segpool]

	data_record = pd.DataFrame(list(zip(sumlst,sentlst,segmtlst,seglst)),columns=['Doc','Sent','Segm','Seg'])

	#time_records = str(N)+"-models-time.csv"


	thresholds = [83]
	#thresholds = [77, 80, 83]
	#thresholds = [63,65,67,70,73,75,77,80,83,85,87]
	"""
	=========== What is Matter Parameters ===================
	"""
	#tups = [(125.0, 1.0), (125.0, 1.5), (125.0, 2.0), (125.0, 2.5), (125.0, 3.0), (150.0, 1.0), (150.0, 1.5), (150.0, 2.0), (150.0, 2.5), (150.0, 3.0), (175.0, 1.0), (175.0, 1.5), (175.0, 2.0), (175.0, 2.5), (175.0, 3.0), (200.0, 1.0), (200.0, 1.5), (200.0, 2.0), (200.0, 2.5), (200.0, 3.0), (225.0, 1.0), (225.0, 1.5), (225.0, 2.0), (225.0, 2.5), (225.0, 3.0), (250.0, 1.0), (250.0, 1.5), (250.0, 2.0), (250.0, 2.5), (250.0, 3.0)]

	#tups = [(200.0, 1.0), (200.0, 1.5), (200.0, 2.0), (200.0, 2.5), (200.0, 3.0), (225.0, 1.0), (225.0, 1.5), (225.0, 2.0), (225.0, 2.5), (225.0, 3.0), (250.0, 1.0), (250.0, 1.5), (250.0, 2.0), (250.0, 2.5), (250.0, 3.0)]

	"""
	=========== DUC Data ==========
	"""

	### Settle down the parameters 

	# tups = [(len(segpool)+10, 2.5), (len(segpool)+10, 3), (len(segpool)+20, 2.5), (len(segpool)+20, 3), (len(segpool)+30, 2.5),(len(segpool)+20, 3)]
	tups = [(len(segpool)+10,2.5)]
	#tups = [(175,2.0)]
	#tups = [(len(segpool)+10,3)]

	for threshold in thresholds:
		for tup in tups:
		#print('Using Threshold {}\n\ta = {} and b = {}'.format(threshold, tup[0], tup[1]))
			# Make Deep Copy of Segment Pool
			segmentpool = copy.deepcopy(segpool)
			segmentpool_length = len(segmentpool)
			
			# Build Pairwise Similarity Set
			BigSet2 = pairwise(segmentpool, N, threshold)			

			# For getting the coefficients combinations 
			#bf_dict = BruteForceLaw(len(segmentpool),5)
			bf_dict = tup
			'''            
			================= Pyramid Building ==================
			'''
			timer = time()

			# N is the number of summaries used, indicates number of layers in pyramid
			# Pyramid is a list of lists and Pyramid_info is a list of Layer() objects
			
			#Wasih (02-27-20) Use lists in python3 instead of range (same thing)
			if PYTHON_VERSION == 2:
				Pyramid = range(N)
				Pyramid_info = range(N)
			else:
				Pyramid = []
				Pyramid_info = []
				for i in range(N):
					Pyramid.append(i)
					Pyramid_info.append(i)	

			# Build the first N -> 2 Layers of the Pyramid
			for n in range(N,1, -1):
				
				#Wasih (02-28-21) Debug prints
				y_n = power_law(n, bf_dict)
				# If we are building the second layer of the Pyramid
				if n == 2:
					layer = ComposeLayer2(BigSet2, segmentpool)
					#for seg in segmentpool:
					#	print(seg.id, ' : ', seg.status, ' : ', seg.commit_invalid)
											
					#f = open('/home/wasih7/PyrEval/car.txt', 'r')
					#st = f.read()
					#st = st.strip()
					#layer = ast.literal_eval(st)
					#print(layer)
				# Else, build pyramid using Clique Algorithm
				else:
					#if n != 3:
					layer = ComposeSegSets(BigSet2, segmentpool, n)
					#else:					
					#	f = open('/home/wasih7/PyrEval/bi.txt', 'r')
					#	st = f.read()
					#	st = st.strip()
					#	layer = ast.literal_eval(st)
					#print(layer)
				# Sorting Algorithm for Segment Sets and Yield Best Fitting Layer
				layer = SortDescendingWAS(layer)	
				layer = BestFit(layer, n, segmentpool, y_n)

				# Set Properties of Layer Object
				length = len(layer)
				obj = Layer(n)
				obj.length = length
				obj.size = length * n
				obj.capacity = y_n

				#Wasih (03-01-21) Debug prints
				#print('----> ', layer)				

				# Assign objects to lists
				Pyramid[n-1] = layer
				Pyramid_info[n-1] = obj

				# Check whether the given layer respects contraints
				constraint = CheckConstraint1(length,n, N,Pyramid_info)
				obj.constraint1 = constraint
				
				# If we are looking at any layer between N-1 and 2 and the contraint is False...
				if (constraint == False) and (n != N):
					#print("\tCalling Local Backtracking")
					status, segmentpool, Pyramid, Pyramid_info, current = localBackTracking(layer, n, segmentpool, Pyramid_info, Pyramid, BigSet2, N, bf_dict)
					if status: # Local Backtracking Ran Succesfully
						layer = current
						length = len(layer)
						obj = Pyramid_info[n-1]
						obj.length = length
						obj.size = length * n
						obj.constraint1 = True
						Pyramid_info[n-1] = obj
						Pyramid[n-1] = layer
						
				# Settle Nodes Recursively because some layers were changed in Local Backtracking
				segmentpool = RecursiveSettling(Pyramid, segmentpool)
				
			# Build Layer 1
			#print "Building Layer 1"
			bs1, segmentpool = ComposeLayer1(segmentpool)
			Pyramid[0] = bs1
			bottom = Layer(0)
			bottom.length = len(bs1)
			bottom.size = bottom.length
			bottom.constraint1 = True
			bottom.capacity = power_law(1, bf_dict)
			Pyramid_info[0] = bottom
			
			#Wasih (02-28-21) Debug prints
			#print('Wasih!')
			
			# print('Active Segments: %d' % len([segment for segment in segmentpool if # segment.status == False]))
			# Global Backtracking settles contraints problems in all Layers
			t = time()
			#print(bf_dict, '$')
			#print(Pyramid, '$')			


			segmentpool, Pyramid_info, Pyramid = GLobalBT(Pyramid_info, Pyramid, N, segmentpool, bf_dict, BigSet2)
			
			#Wasih (02-28-21) Debug prints
			flag, problem, belongs = check_problem(segmentpool, Pyramid)

			#Wasih (02-28-21) Debug prints
			
			if flag:
				print ("======Trigger Sanity Check =======")
				new = detail_check(problem,belongs, Pyramid)
				Pyramid, Pyramid_info = Final_Solutions(new, Pyramid, Pyramid_info)

		### Constraints Check:
		### Check if there is any segment that is not supposed to be used but gets adopted
		
		segshouldbeused_df = Build_All_Record(segmentpool, Pyramid)
		Pyramid[0] = Iterate_Clean_Record(segshouldbeused_df,Pyramid)  
		#print(Pyramid[0])		

		alls = Pickup_used(Pyramid)
		# Here is 
		missings = Update_Record(data_record,alls)
		#Wasih (02-28-21) Debug prints
		
		if len(missings) >0:
			print ("Found missing segments: ", missings) 
			for each in missings:
				#Wasih (06-17-21) Remove duplicate SCUs of weight 1
				is_used = False
				for alpha in alls:
					if each == alpha:
						is_used = True
						break
				if is_used == False:
					segtext = [s.seg for s in segmentpool if s.id == each][0]
					item = {'seg1id': each,'WAS': 1,'seg1':segtext}
					Pyramid[0].append(item)

		# Update pyramid information for the cleaned layer1 
		Pyramid_info[0].length = len(Pyramid[0]) 
		# DONE!
		done = time()
		
		'''
		================= Format Output =================
		'''
		
		# Get total Number of Segments used in the Pyramid
		length = 0
		for p in Pyramid:
			length += len(p)

		# lists and variables to be used for readable output of pyramid
		cu_ids = []
		weights = []
		labels = []
		all_seg_ids = []
		count = 0
		was = 0
		cost = 0
		scu_vecs = {}

		score = 0
		
		# Iterate through Pyramid, make list assignments, update variables
		for n, p in enumerate(reversed(Pyramid)):
			cost += float(len(Pyramid[n])) * (1 / float(n+1))
			for j, scu in enumerate(p):
				was += scu['WAS']
				l = len(Pyramid) - n
				if l > 1:
					l = l * (l - 1)
					l = l / 2
				score += scu['WAS']/l
				for _ in range(len(Pyramid) - n):
					cu_ids.append(count)
					weights.append(str(len(Pyramid)-n))
				segs = [scu['seg%d' % (p + 1)] for p in range(len(Pyramid) - n)]
				seg_ids = [scu['seg%did' % (p + 1)] for p in range(len(Pyramid) - n)]
				all_seg_ids += seg_ids
				for j, seg in enumerate(segs):
					labels.append(str(seg))
				seg_ids = [scu['seg%did' % (p + 1)] for p in range(len(Pyramid) - n)]
				vectors_to_find = []
				for seg_id in seg_ids:
					vectors_to_find.append(seg_id)
				scu_vecs[count] = vectors_to_find
				count += 1
		
		# Writing Readable version of Pyramid
		fname = 'pyramid_t{}_a{}_b{}'.format(threshold, tup[0], tup[1])
		#Wasih (06-13-21) Create user specified pyramid file. Readable file is by the name, user_read.pyr
		fname = pyr_name
		lines = []
		if cu_ids:
			for j, i in enumerate(cu_ids):
				line = 'SCU' + '\t' + str(i) + '\t' + str(weights[j]) + '\t' + labels[j]
				print (line)
				#print(line)
				lines.append(line)
		with open('../Scoring/scu/' + fname + '_read.pyr', 'w') as f:
			for line in lines:
				#print(line)
				f.write(line + '\n')
		f.close()

		root = ET.Element('Pyramid')
		p = 0
		scu = ET.SubElement(root,'scu', uid=str(p))
		for j, i in enumerate(cu_ids):
			if i > p:
				p = i
				scu = ET.SubElement(root,'scu', uid=str(p))
			ET.SubElement(scu, 'contributor', label = labels[j])
		tree = ET.ElementTree(root)
		### Normal Path 
		tree.write("../Scoring/pyrs/pyramids/" + fname + ".pyr")
		#tree.write("../Scoring/EDUAG/"+fname+".pyr")
		#tree.write('../Scoring/311-4-2/pyramids/' + fname + '.pyr')
			  
		# Console Output
		# print('With Threshold {}%'.format(threshold))
		# print('a: {} | b: {}').format(tup[0], tup[1])  
		# print('cost: %.2f' % cost)
		# print('was: %.2f' % was)
		
		text = colored(('Pyramid: %s' % fname), 'blue')
		print (text)
		#print('Pyramid: %s' % fname)
		text = colored(('Time: {}'.format(str(done - timer))), 'blue')
		print (text)
		#print('Time: {}'.format(str(done - timer)))
		# with open(time_records,"a") as f:
		#     wr = csv.writer(f)
		#     wr.writerow([str(done-timer)])
		text = colored('Pyramid .pyr file stored in PyrEval/Scoring/pyrs/pyramids/', 'blue')
		print (text)
		#print('Pyramid .pyr file stored in PyrEval/Scoring/pyrs/pyramids/')
		text = colored('Pyramid .size file stored in PyrEval/Scoring/sizes/', 'blue')
		print (text)
		#print('Pyramid .size file stored in PyrEval/Scoring/sizes/')
		text = colored('Readable pyramid file stored in PyrEval/Scoring/scu/', 'blue')
		print (text)
		#print('Readable pyramid file stored in PyrEval/Scoring/scu/')
		with open('../Scoring/sizes/' + fname + '.size', 'w') as f:
			for n,pyr in enumerate(Pyramid_info):
				f.write(str(pyr.length) + "\n")
		f.close()
		# for n, pyr in enumerate(Pyramid_info):
		#     print('Layer {} has size {} | Upperbound {}'.format(n+1, pyr.length, pyr.capacity))
		# if len(all_seg_ids) == len(set(all_seg_ids)):
		#     print('Length of Segment Pool as Beginning: {} vs Length at End {}'.format(segmentpool_length,
		#                                                                               len(segmentpool)))
		#     print('Number of Segments Used: %d' % len(all_seg_ids))
		#     print('All Segment IDs are Unique')

