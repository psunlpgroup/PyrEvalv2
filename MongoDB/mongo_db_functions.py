# Written by: Adithya Tanam
# Adithya Last Update: 10/29/22
# Script to handle MongoDB Operations
#Last updated by Mahsa (02-17-2023)

from distutils.log import error
from pymongo import MongoClient
from pymongo import errors
from sys import exit
from datetime import datetime
import pandas as pd


class MongoDB_Operations:
    __dbconn__ = ""
    __client__ = None
    __db__ = None

    def __init__(self, dbconnection_string):
        self.__dbconn__ = dbconnection_string

    # To open the connection
    def connect(self, database_name):
        try:
            self.__client__ = MongoClient(self.__dbconn__)
            self.__db__ = self.__client__[database_name]
            print("Connection Established")
        except errors.ConnectionFailure as e:
            print("Error connecting to the database %s" % e)
        except Exception as e:
            print("MongoDB Error %s" % e)

    def get_document_field(self, collection_name, search_term, search_term_value, field_to_return):
        try:
            collection = self.__db__[collection_name]
            search_string = ''' {' ''' + search_term + ''' ': ' ''' + search_term_value + ''' '} '''
            projection_string = ''' { _id: 0, ''' + field_to_return + ''': 1 }'''
            return collection.find_one(search_string, projection_string)
        except Exception as e:
            print("MongoDB Error %s" % e)

    def get_document(self, collection_name, search_term, search_term_value):
        try:
            collection = self.__db__[collection_name]
            search_string = ''' {' ''' + search_term + ''' ': ' ''' + search_term_value + ''' '} '''
            return collection.find_one(search_string)
        except Exception as e:
            print("MongoDB Error %s" % e)

    def update_document(self, collection_name, search_term, search_term_value, update_term, update_term_value):
        try:
            collection = self.__db__[collection_name]
            update_string = ''' {' ''' + search_term + ''' ': ' ''' + search_term_value + ''' '} , {
                            '$set': {"''' + update_term + '''": ''' + update_term_value + '''} '''
            return collection.find_one(update_string)
        except Exception as e:
            print("MongoDB Error %s" % e)

    # Function to fetch essay from the STUDENT_ESSAYS_COLLECTION using the Student Metadata
    def get_student_essay(self, student_metadata_obj):
        try:
            query_string = (
                {
                    "student_metadata.student_id": student_metadata_obj.student_id,
                    "student_metadata.class_id": student_metadata_obj.class_id,
                    "student_metadata.teacher_id": student_metadata_obj.teacher_id,
                    "student_metadata.essay_number": student_metadata_obj.essay_number,
                    "student_metadata.essay_version": student_metadata_obj.essay_version
                }
            )

            student_essay_collection = self.__db__['STUDENT_ESSAYS_COLLECTION']

            document = student_essay_collection.find_one(query_string)

            return document['essay_text']

        except Exception as e:
            print("MongoDB Error %s" % e)

    # Function to fetch Pyramid id from the database
    def get_pyramid_id(self, essay_number):
        try:
            essay_pyramid_collection = self.__db__['ESSAY_PYRAMID_COLLECTION']

            # Checking if pyramid id exists for the given essay_id
            query_string = (
                {
                    "essay_number": essay_number
                }
            )
            essay_document = essay_pyramid_collection.find_one(query_string)

            if essay_document is None:
                exit('There is no record for the specified Essay ')
            elif (essay_document['pyramid_id'] == ''):
                exit('Pyramid Not Assigned for the Essay')
            else:
                return essay_document['pyramid_id']

        except Exception as e:
            print("MongoDB Error %s" % e)

    # Function to create Pyramid from the hrp version or return the pyr and size file content
    def get_pyramid(self, pyramid_object):
        try:
            pyramid_collection = self.__db__['PYRAMID_COLLECTION']

            query_string = {'pyramid_id': pyramid_object.pyramid_id}
            pyramid_document = pyramid_collection.find_one(query_string)

            if ((pyramid_document['pyr_file_content'] == '') and (pyramid_document['size_file_content'] == '')):
                pyramid_object.make_pyramid(pyramid_document['human_readable_pyramid_content'])

            else:
                pyramid_object.create_pyramid_files(pyramid_document['pyr_file_content'],
                                                    pyramid_document['size_file_content'])

        except Exception as e:
            print("MongoDB Error %s" % e)

    def update_pyramid(self, pyramid_id, pyr_file_content, size_file_content):
        pyramid_collection = self.__db__['PYRAMID_COLLECTION']
        search_query = {'pyramid_id': pyramid_id}
        update_query = {"$set":
            {
                'pyr_file_content': pyr_file_content,
                'size_file_content': size_file_content
            }
        }
        pyramid_collection.update_one(search_query, update_query)
        print("Pyramid Update Successful")

        return ''

    def update_cu_vectors(self, student_metadata_obj, cu_vectors_path):
        student_essay_collection = self.__db__['STUDENT_ESSAYS_COLLECTION']
        cu_df = pd.read_csv(cu_vectors_path)
        cu_vectors = (cu_df.head(1).values[0][1:]).tolist()

        search_query = (
            {
                "student_metadata.student_id": student_metadata_obj.student_id,
                "student_metadata.class_id": student_metadata_obj.class_id,
                "student_metadata.teacher_id": student_metadata_obj.teacher_id,
                #                "essay_number": student_metadata_obj.essay_number,
                #                "essay_version": student_metadata_obj.essay_version
            }
        )

        update_query = {"$set":
            {
                'cu_vectors': cu_vectors
            }
        }
        student_essay_collection.update_one(search_query, update_query)
        return ''

    # Function to populate the pyramid table
    # hrp -> Human Readeable Pyramid
    def populate_pyramids(self, pyramid_id, pyramid_name, hrp_file_location):
        try:
            with open(hrp_file_location, 'r', encoding='UTF-8') as f:
                hrp_content = f.readlines()

            pyramid_collection = self.__db__['PYRAMID_COLLECTION']
            insert_input_dict = {
                "pyramid_id": pyramid_id,
                "pyramid_name": pyramid_name,
                "pyr_file_content": '',
                "size_file_content": '',
                "human_readable_pyramid_content": hrp_content
            }

            if (pyramid_collection.insert_one(insert_input_dict)):
                return 'Pyramid HRP Content Inserted'

        except Exception as e:
            print('MongoDB Error %s' % e)

    # Added 2/17/23 to ensure that the essay_main_ideas to scu_mapping and the essay number are populated in the db along with the pyramid that is read in
    def populate_essay_pyramid(self, pyramid_id, essay_number, essay_main_ideas, scu_mapping):
        try:
            essay_pyramid_collection = self.__db__['ESSAY_PYRAMID_COLLECTION']
            insert_input_dict = {
                "essay_number": essay_number,
                "pyramid_id": pyramid_id,
                "essay_main_ideas": essay_main_ideas,
                "scu_mapping": scu_mapping,
            }

            if (essay_pyramid_collection.insert_one(insert_input_dict)):
                return 'ESSAY_PYRAMID_COLLECTION Entry Inserted'

        except Exception as e:
            print('MongoDB Error %s' % e)

    # Function to insert the debugging data for step6
    def insert_debug_data(self, student_metadata_obj, error_object):
        try:
            debug_collection = self.__db__['DEBUG_DATA_COLLECTION']
            insert_input_dict = {
                "student_metadata":
                    {
                        "student_id": student_metadata_obj.student_id,
                        "class_id": student_metadata_obj.class_id,
                        "teacher_id": student_metadata_obj.teacher_id,
                        "essay_number": student_metadata_obj.essay_number,
                        "essay_version": student_metadata_obj.essay_version
                    },

                "intermmediate_data":
                    {
                        "split_file_content": error_object.split_file_content,
                        "xml_file_content": error_object.xml_file_content,
                        "segs_file_content": error_object.segs_file_content,
                        "vector_file_content": error_object.vector_file_content,
                        "temp_file_content": error_object.temp_file_content
                    },

                "stage_logs":
                    {
                        "sent_split_stage ": error_object.sent_split_stage,
                        "stanford_core_nlp_stage": error_object.stanford_core_nlp_stage,
                        "seg_file_creation_stage": error_object.seg_file_creation_stage,
                        "ls_file_creation_stage": error_object.ls_file_creation_stage,
                        "pyramid_creation_stage": error_object.pyramid_creation_stage,
                        "temp_segs_creation_stage": error_object.temp_segs_creation_stage,
                        "scoring_stage": error_object.scoring_stage
                    },

                "execution_timestamp": datetime.now()
            }

            if (debug_collection.insert_one(insert_input_dict)):
                return 'Error Object Inserted'
        except Exception as e:
            print('MongoDB Error %s' % e)

    # Function to update result in the student collection
    def update_result(self, result_obj, student_metadata_obj):
        print("update result")
        try:
            student_collection = self.__db__['STUDENT_ESSAYS_COLLECTION']
            search_query = (
                {
                    "student_metadata.student_id": student_metadata_obj.student_id,
                    "student_metadata.class_id": student_metadata_obj.class_id,
                    "student_metadata.teacher_id": student_metadata_obj.teacher_id,

                }
            )
            # TODO change it to addToSet and add fields to result_obj in printEsumLog_mogo_maj
            update_query = {"$set":
                {
                    'result':
                        {
                            'No of segments': result_obj.no_of_segments,
                            'Pyramid Id': result_obj.pyramid_name,
                            'Raw': result_obj.raw,
                            'Maximum possible score with Raw': result_obj.max_score,
                            'Quality': result_obj.quality,
                            'Average No of SCUs': result_obj.avg_scu,
                            'Maximum score with average No of SCUs': result_obj.max_score_avg_scu,
                            'Coverage': result_obj.coverage,
                            'Comprehensive': result_obj.comprehensive,
                            'Content Unit List': result_obj.content_unit_list,
                            'Sentence Matches': result_obj.sentence_match_dict
                        },
                }
            }
            student_collection.update_one(search_query, update_query)
            print("Result Update Successful")
        except Exception as e:
            print('MongoDB Error %s' % e)

    # Function to get scu mappings
    def get_scu_mapping(self, pyramid_id):

        try:
            essay_pyramid_collection = self.__db__['ESSAY_PYRAMID_COLLECTION']

            query_string = (
                {
                    "pyramid_id": pyramid_id
                }
            )
            essay_pyramid_document = essay_pyramid_collection.find_one(query_string)

            if essay_pyramid_document is None:
                exit('There is no record for the specified Pyramid Id ')
            else:
                return essay_pyramid_document['scu_mapping']
        except Exception as e:
            print('MongoDB Error %s' % e)

    # Function to get scu mappings
    def get_essay_main_ideas(self, pyramid_id):
        try:
            essay_pyramid_collection = self.__db__['ESSAY_PYRAMID_COLLECTION']

            query_string = (
                {
                    "pyramid_id": pyramid_id
                }
            )
            essay_pyramid_document = essay_pyramid_collection.find_one(query_string)

            if essay_pyramid_document is None:
                exit('There is no record for the specified Pyramid Id ')
            else:
                return essay_pyramid_document['essay_main_ideas']
        except Exception as e:
            print('MongoDB Error %s' % e)

    # serial simulation operations
    def get_students(self, count):
        try:
            student_essay_collection = self.__db__['STUDENT_ESSAYS_COLLECTION']
            documents = student_essay_collection.aggregate([{'$sample': {'size': count}}])

            # student_essay_collection.find().limit(count)
            return documents
        except Exception as e:
            print('MongoDB Error %s' % e)

    # To close the connection
    def connection_close(self):
        return self.__client__.close()