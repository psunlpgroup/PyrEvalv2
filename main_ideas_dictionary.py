import pandas as pd
import os

import re

#Written by Mahsa (02-17-2023)
def replace_all(repls, str):
    # return re.sub('|'.join(repls.keys()), lambda k: repls[k.group(0)], str)
    return re.sub('|'.join(re.escape(key) for key in repls.keys()),
                  lambda k: repls[k.group(0)], str)

#Function to create a new cu_vectors.csv with the indexing from the curriculum, not the pyramid indexing
def reorder_cu_vectors(cu_df,enotebook_cu_vectors_path,scu_mapping_list,essay_main_ideas_list,is_essay_one):

    scu_mapping_list_int = [eval(i) for i in scu_mapping_list]
    scu_mapping_list_int_one_added = [i+1 for i in scu_mapping_list_int]
    reordered_cu_df = cu_df
    reordered_cu_df = reordered_cu_df[reordered_cu_df.columns[scu_mapping_list_int ]]

    #This changes the dictionary order
    reordered_cu_df.rename(columns={scu_mapping_list_int[0]: essay_main_ideas_list[0], scu_mapping_list_int[1]: essay_main_ideas_list[1], scu_mapping_list_int[2]: essay_main_ideas_list[2], scu_mapping_list_int[3]: essay_main_ideas_list[3], scu_mapping_list_int[4]: essay_main_ideas_list[4], scu_mapping_list_int[5]: essay_main_ideas_list[5]}, inplace=True)

    reordered_cu_df.to_csv(enotebook_cu_vectors_path)



def replace_log(log_path,elog_path,scu_mapping_list,essay_main_ideas_list,is_essay_one):
    scu_mapping_list_int = [eval(i) for i in scu_mapping_list]
    scu_mapping_list_int_one_added = [i + 1 for i in scu_mapping_list_int]

    for filename in os.listdir(log_path):


        with open(log_path+"/" + filename, "r") as file:
            data = file.read()

            listi = data.split('\n')
            listi_sp = listi[14].split(': ')[1].split('(5)')
            listi2 = []
            listi3 = []
            for l in listi_sp:
                if l[-1] != ' ':
                    listi2.append(int(l[-1]))

            # Change this part to change the dictionary order
            if scu_mapping_list_int[0] in listi2: listi3.append(essay_main_ideas_list[0])
            if scu_mapping_list_int[1] in listi2: listi3.append(essay_main_ideas_list[1])
            if scu_mapping_list_int[2] in listi2: listi3.append(essay_main_ideas_list[2])
            if scu_mapping_list_int[3] in listi2: listi3.append(essay_main_ideas_list[3])
            if scu_mapping_list_int[4] in listi2: listi3.append(essay_main_ideas_list[4])
            if scu_mapping_list_int[5] in listi2: listi3.append(essay_main_ideas_list[5])



            listi3 = sorted(listi3)

            listi4 = []

            for l in listi[0:13]:
                listi4.append(l + '\n')
            # listi4.append(listi[0:13])
            listi4.append(listi[14].split(': ')[0] + ': ')

            for l in listi3:
                listi4.append(str(l) + '(5) ')

            # listi4.append(listi_sp[-1][2:])

            for l in listi[15:]:
                listi4.append('\n' + l)

            listi4 = ''.join(listi4)

            data = listi4

            # This part changes the dictionary order
            search_text1 = "Content Unit: "+ scu_mapping_list[0]+" "
            replace_text1 = "Content Unit: " + essay_main_ideas_list[0]+" "

            search_text2 = "Content Unit: "+ scu_mapping_list[1]+" "
            replace_text2 = "Content Unit: "+ essay_main_ideas_list[1]+" "

            search_text3 = "Content Unit: "+ scu_mapping_list[2]+" "
            replace_text3 = "Content Unit: "+ essay_main_ideas_list[2]+" "

            search_text4 = "Content Unit: "+ scu_mapping_list[3]+" "
            replace_text4 = "Content Unit: "+ essay_main_ideas_list[3]+" "

            search_text5 = "Content Unit: "+ scu_mapping_list[4]+" "
            replace_text5 = "Content Unit: "+ essay_main_ideas_list[4]+" "

            search_text6 = "Content Unit: "+ scu_mapping_list[5]+" "
            replace_text6 = "Content Unit: "+ essay_main_ideas_list[5]+" "

            data = replace_all({search_text1: replace_text1, search_text2: replace_text2, search_text3: replace_text3,
                                search_text4: replace_text4, search_text5: replace_text5, search_text6: replace_text6},
                               data)

        data = data.replace('Sentence:','%Sentence:')
        sp_by_sent = data.split('%')
        sp_by_seg = []
        final = []


        for sp in sp_by_sent:
            sp = sp.replace('Segment ID:','&Segment ID:')
            sp_by_seg.append(sp.split('&'))

        final.append(sp_by_seg[0])
        sp_by_seg.pop(0)
        for sg in sp_by_seg:
            flag = False
            temp2 = ''
            for sg_in in sg:
                if 'Content Unit:' in sg_in and 'None' not in sg_in:
                    temp = sg_in.split(' ')[6]
                    if int(temp) < 6:
                        if flag is False:
                            flag = True
                            final.append(temp2)
                            final.append(sg_in)

                else:
                    temp2 = sg_in


        temp = str(final[0][0])
        final.pop(0)
        # data = ''.join(temp)
        data = ''.join(str(f) for f in final)
        data= temp + data



        write_path =  elog_path
        if not os.path.exists(write_path):
            os.makedirs(write_path)
        with open(write_path+"/" + filename, 'w') as file:
            file.write(data)
