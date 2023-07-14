import pandas as pd
import os

import re

#Updated by Mahsa (06-21-2023)
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
    # reordered_cu_df.rename(columns={scu_mapping_list_int[0]: essay_main_ideas_list[0], scu_mapping_list_int[1]: essay_main_ideas_list[1], scu_mapping_list_int[2]: essay_main_ideas_list[2], scu_mapping_list_int[3]: essay_main_ideas_list[3], scu_mapping_list_int[4]: essay_main_ideas_list[4], scu_mapping_list_int[5]: essay_main_ideas_list[5]}, inplace=True)
    for col in reordered_cu_df.columns:
        i = 0
        reordered_cu_df = reordered_cu_df.rename(columns={col:str(col).replace(str(scu_mapping_list_int[i]),str(essay_main_ideas_list[i]))})
        i = i+1

    reordered_cu_df.to_csv(enotebook_cu_vectors_path)


def write_logs_to_file(data, write_path, filename):
    if not os.path.exists(write_path):
        os.makedirs(write_path)
    with open(write_path + "/" + filename, 'w') as file:
        file.write(data)


def replace_log(log_path,elog_path,scu_mapping_list,essay_main_ideas_list,is_essay_one):
    scu_mapping_list_int = [eval(i) for i in scu_mapping_list]
    if is_essay_one:
        number_of_cus = 6
    else:
        number_of_cus = 8

    for filename in os.listdir(log_path):


        with open(log_path+"/" + filename, "r") as file:
            data = file.read()
            write_path = elog_path

            listi = data.split('\n')


            for i in range(0,len(listi)):
                if "==================" in listi[i]:
                    listi[i]=listi[i].replace(listi[i],"\n")

            content_unit_list_split = listi[14].split(': ')

            #Has no content units
            if (len( content_unit_list_split) == 1):
                listi[14] = content_unit_list_split[0] + ":"
                data = ''.join(str(f)+"\n" for f in listi[0:15])
                write_logs_to_file(data, write_path, filename)
                return

            listi_sp = content_unit_list_split[1].split('(5)')

            #Has no content unit of weight five
            if(len(listi_sp) == 1):
                listi[14] = content_unit_list_split[0]+ ":"
                data = ''.join(str(f)+"\n" for f in listi[0:15])
                write_logs_to_file(data, write_path, filename)
                return

            listi2 = []
            listi3 = []
            for l in listi_sp:
                if l[-1] != ' ':
                    listi2.append(int(l[-1]))


            for i in range(0,number_of_cus):
                if scu_mapping_list_int[i] in listi2: listi3.append(essay_main_ideas_list[i])




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

            if is_essay_one:
                if "Content Unit: 6" in data:
                    data = replace_all({"Content Unit: 6":"Content Unit: 20"},data)
                data = replace_all({search_text1: replace_text1, search_text2: replace_text2, search_text3: replace_text3,
                                search_text4: replace_text4, search_text5: replace_text5, search_text6: replace_text6},
                               data)
            else:
                if "Content Unit: 8" in data:
                    data = replace_all({"Content Unit: 8": "Content Unit: 20"},data)
                search_text7 = "Content Unit: " + scu_mapping_list[6] + " "
                replace_text7 = "Content Unit: " + essay_main_ideas_list[6] + " "

                search_text8 = "Content Unit: " + scu_mapping_list[7] + " "
                replace_text8 = "Content Unit: " + essay_main_ideas_list[7] + " "
                data = replace_all({search_text1: replace_text1, search_text2: replace_text2, search_text3: replace_text3,
                                search_text4: replace_text4, search_text5: replace_text5, search_text6: replace_text6,search_text7: replace_text7,search_text8: replace_text8},
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

                    if int(temp) <= number_of_cus:

                        if flag is False:
                            flag = True
                            final.append(temp2)
                        final.append(sg_in)
                        # print(sg_in)
                        # print("@@")

                elif 'Content Unit:' in sg_in and 'None' in sg_in:
                    pass
                else:
                    temp2 = sg_in
                    # print(sg_in)
                    # print("^^")


        temp = str(final[0][0])
        final.pop(0)
        # print(final)

        # data = ''.join(temp)
        data = ''.join(str(f) for f in final)
        data= temp + data

        write_logs_to_file(data,write_path,filename)
        return

