# Written by: Adithya Tanam
# Last Update: 10/29/22

#Script to populate hrp content to the pyramid collection from the HRP Folder

import mongo_db_functions

db_conn = "mongodb://localhost:27017"
database_name = 'PYREVAL_TEST_DB';
mongodb_operations = mongo_db_functions.MongoDB_Operations(db_conn)

if __name__ == "__main__":

    hrp_location = '/home/adithya/Desktop/NLP_Internship/ProjectCode/PyrEvalv2/MongoDB/HRP_Files/Revised_pyramid_readable_20220302_rjp.pyr'
    pyramid_id = 2
    pyramid_name = 'Pyramid_RJP'

    #Code to connect to the databse
    mongodb_operations.connect(database_name);

    mongodb_operations.populate_pyramids(pyramid_id, pyramid_name, hrp_location)