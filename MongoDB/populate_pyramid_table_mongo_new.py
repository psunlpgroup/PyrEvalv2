# Written by: Adithya Tanam
# Last Update: 10/29/22

# Script to populate hrp content to the pyramid collection from the HRP Folder

import mongo_db_functions

db_conn = "mongodb://localhost:27017"
database_name = 'TEST_FEB2023';
mongodb_operations = mongo_db_functions.MongoDB_Operations(db_conn)

if __name__ == "__main__":
    hrp_location = '/Users/la-mfs6614/PycharmProjects/PyrEvalv2_Mongo_PD/MongoDB/HRP_Files/essay1_pyramid_readable_20221207.pyr'
    # must cast the pyramid_id as float 
    pyramid_id = float(20221207)             
    pyramid_name = "essay1_pyramid_readable_20221207"
    essay_number = 1
    essay_main_ideas = ["1", "2", "3", "4", "5", "6"]
    scu_mapping = ["5", "0", "4", "2", "1", "3"]

    # Code to connect to the databse
    mongodb_operations.connect(database_name);

    mongodb_operations.populate_pyramids(pyramid_id, pyramid_name, hrp_location)

    # Added 2/17/23 to ensure that the essay_main_ideas to scu_mapping and the essay number are populated in the db along with the pyramid that is read in
    mongodb_operations.populate_essay_pyramid(pyramid_id, essay_number, essay_main_ideas, scu_mapping)
