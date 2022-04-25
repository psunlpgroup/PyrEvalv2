import xml.etree.ElementTree as gfg
import os
import re
import sys

if len(sys.argv) == 4:
	input_file = sys.argv[1]
	output_xml = sys.argv[2]
	output_size = sys.argv[3]
else:
	input_file = r"Revised_pyramid_readable_20220302_rjp.pyr"
	output_xml = r"Pyramid_v4\Revised_pyramid_readable_20220302_rjp_xml.pyr"
	output_size = r"Pyramid_v4\Revised_pyramid_readable_20220302_rjp_xml.size"
# Program assumes that the Pyramid is made from 5 essays
counts = [0 for i in range(5)]

try:
	with open(input_file, 'r', encoding='UTF-8') as f:
		lines = f.readlines()
except:
	print("Input file is invalid")
	sys.exit()
	pass
# with open(r"Pyramid_v4\Revised_pyramid_readable_220224_rjp.pyr", 'r', encoding='UTF-8') as f:)
		# lines = f.readlines()
root = gfg.Element('Pyramid')

scu_count = -1



for line in lines:
	if line[:2] == '//':
		continue
	try:
		_, scuid, weight, text = line.split('\t')
	except:
		print(line)

	if scu_count != scuid:
		scu = gfg.Element('scu')
		scu.set('uid',scuid)
		root.append(scu)
		scu_count = scuid
		counts[int(weight)-1] +=1


	cont = gfg.SubElement(scu, "contributor")
	cont.set('label', text[:-1])


tree = gfg.ElementTree(root)

with open (output_xml, "wb") as files :
        tree.write(files)

with open (output_size, "w") as f:
	for i in counts:
		f.write(str(i)+'\n')



