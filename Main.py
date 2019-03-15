import yaml
from pathlib import Path
import filePDF
import os
import pdf_reader
import pandas as pd
import pyodbc
import time

# Read configuration file
with open("config.yaml", 'r') as stream:
	try:
		setting = yaml.safe_load(stream)
	except yaml.YAMLError as exc:
		print(exc)

folder_input = setting['folder_input']
min_cat_count = setting['min_cat_count']
min_dish_count = setting['min_dish_count']

print("Initital settings. Min. number of categories - %s; min. number of dishes -%s" % (min_cat_count, min_dish_count))
print("Initail settings. Read files from folder %s." % folder_input)


# Iterate over pdf files in the folder
pathlist = Path(folder_input).glob('**/*.pdf')
for path in pathlist:
	path_in_str = str(path)
	file_name = os.path.splitext(os.path.basename(path))[0]
	# Download pdf into object
	file = filePDF.PdfFile(path_in_str)
	start_time = time.time()
	# Start work with files
	try:
		items = file.get_items()
		print("Pdf file %s downloaded for %s seconds" % (file_name, str(time.time() - start_time)))
		print("File contain %s of elements" % len(items))

		if len(items) < min_cat_count + 2 * min_dish_count:
			print("Pdf file %s is not text" % file_name)
			continue
	except  Exception as e:
		print("Exeption. Pdf file %s is not downloaded" % file_name)



