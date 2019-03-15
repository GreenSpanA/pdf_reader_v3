import yaml
from pathlib import Path
import filePDF
import os
from datetime import datetime, date, time
import msSQL
import pyodbc
import pandas as pd

# Connection string
connStr = pyodbc.connect("DRIVER={ODBC Driver 13 for SQL Server};"
						 "SERVER=DESKTOP-I46RHJS;"
						 "DATABASE=Menus;"
						 "Trusted_Connection=yes")

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
	file_size = os.path.getsize(path) / 1024.0 #in kB

	# Download pdf into object
	file = filePDF.PdfFile(path_in_str)
	start_time = datetime.now()
	# Start work with files
	try:
		items = file.get_items()
		time_file_down = (datetime.now() - start_time).total_seconds()
		print("Pdf file %s downloaded for %s seconds" % (file_name, str(time_file_down)))
		print("File contain %s of elements" % len(items))

		if len(items) < min_cat_count + 2 * min_dish_count:
			print("Pdf file %s is not text" % file_name)
			cursor = connStr.cursor()
			cursor = connStr.cursor()
			time_log = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			page_num_max = max(items['page_num'])
			query = "INSERT INTO dbo.pdf_convert_log([time], [file_path], [file_name], " \
					"[is_picture], [file_size], [page_count], [download_file_time], [is_parsed]) " \
					"values (convert(smalldatetime, '%s', 121), '%s', '%s', %s, %s, %s, %s, %s)"\
					% (time_log, path_in_str, file_name, 1, file_size, page_num_max, time_file_down, 0)
			cursor.execute(query)
			connStr.commit()
			cursor.close()
			connStr.close()
			continue
	except Exception as e:
		print("Exeption. Pdf file %s is not downloaded" % file_name)



