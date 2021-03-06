import yaml
from pathlib import Path
import filePDF
import os
from datetime import datetime, date, time
import pyodbc
import pandas as pd
import tqdm

from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LAParams, LTTextBox
from pdfminer.converter import PDFPageAggregator
import pdf_rectangle

import msSQL
from pdf_reader import find_cat_h, delete_empty_names, collapse_rows, union_items
from pdf_reader import find_closest_right, round3
from menu_entity import is_separate_price, is_dish_then_price, is_dish_with_price
from menu_entity import	get_description_dish_price, get_prices_dish_price
from menu_entity import cut_prices_form_df, get_items_dish_price, collapse_prices, get_post_prices_dish_price
from result_DF import get_Result
from result_DF2 import get_Result_dish_with_price

# Connection string
connStr = pyodbc.connect("DRIVER={ODBC Driver 13 for SQL Server};"
						 "SERVER=DESKTOP-I46RHJS;"
						 "DATABASE=Menus;"
						 "Trusted_Connection=yes")


# Read Vegans combinations
Vegans = pd.read_csv('F:\\100nuts\\Vegans_comment.csv', sep=";")

# Read configuration file
with open("config.yaml", 'r') as stream:
	try:
		setting = yaml.safe_load(stream)
	except yaml.YAMLError as exc:
		print(exc)

Rest_id = setting['Rest_id']
#folder = setting['folder_initial']
folder = setting['folder_input']
#folder = setting['folder']
folder_input_short = [dI for dI in os.listdir(folder) if os.path.isdir(os.path.join(folder, dI))]

# print("Initital settings. Min. number of categories - %s; min. number of dishes -%s" % (min_cat_count, min_dish_count))

if len(folder_input_short) == 0:
	print("Empry folder %s" % folder)

# Iterate over subdirectorys in the folder
for folder_input_short in tqdm.tqdm(folder_input_short):
	Rest_id = Rest_id + 1
	folder_input = r'%s\%s' % (folder, folder_input_short)
	#print("Start with folder %s" % folder_input)

	# folder_input = setting['folder_input']
	folder_input_name = os.path.splitext(os.path.basename(folder_input))[0]
	min_cat_count = setting['min_cat_count']
	min_dish_count = setting['min_dish_count']
	#print("Initail settings. Read files from folder %s." % folder_input)

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
		time_log = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		try:
			items = file.get_items()
			time_file_down = (datetime.now() - start_time).total_seconds()
			#print("Pdf file %s downloaded for %s seconds" % (file_name, str(time_file_down)))
			#print("File contain %s of elements" % len(items))

			if len(items) == 0:
				query = "INSERT INTO dbo.pdf_convert_log([time], [file_path], [file_folder], [file_name], " \
						"[file_size], [is_parsed], [items_count]) " \
						"values (convert(smalldatetime, '%s', 121), '%s', '%s', '%s', %s, %s, %s)" % (
						time_log, path_in_str, folder_input_name,
						file_name, file_size,  0, len(items))
				sql_log = msSQL.msSQL(connStr)
				sql_log.insert_to_log(query)
				continue

			page_num_max = max(items['page_num'])
			# If picture
			if len(items) > 0 and (len(items) < min_cat_count + 2 * min_dish_count):
				#print("Pdf file %s is not text" % file_name)
				#time_log = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

				query = "INSERT INTO dbo.pdf_convert_log([time], [file_path], [file_folder], [file_name], " \
							"[is_picture], [file_size], [page_count], [download_file_time], [is_parsed], [items_count]) " \
							"values (convert(smalldatetime, '%s', 121), '%s', '%s', '%s', %s, %s, %s, %s, %s, %s)" % (time_log, path_in_str, folder_input_name,
							 file_name, 1, file_size, page_num_max, time_file_down, 0, len(items))
				sql_log = msSQL.msSQL(connStr)
				sql_log.insert_to_log(query)
				continue
			# If picture end

			items = items.sort_values(['page_num', 'x0', 'y1'], ascending=[True, True, False])

			# Distribution of all heights
			Heights = pd.crosstab(index=items["height"], columns="count")

			# Find height of category's box
			try:
				cat_h = find_cat_h(Heights, items, min_cat_count, min_dish_count)
				#print("Category heigth is: %s" % cat_h)
			except Exception:
				cat_h = 0

			# Find df of categories
			cat_list = items[items['height'].between(0.99 * cat_h, 1.01 * cat_h)]
			cat_list = delete_empty_names(cat_list)
			cat_list = collapse_rows(cat_list, sense=1.03)
			cat_list = cat_list.sort_values(['page_num', 'y1', 'x0'], ascending=[True, False, True])
			#print("Categories count is: %s" % len(cat_list))
			cat_list = union_items(cat_list, items)

			# Parse from pdf_miner
			fp = open(path_in_str, 'rb')
			rsrcmgr = PDFResourceManager()
			laparams = LAParams()
			device = PDFPageAggregator(rsrcmgr, laparams=laparams)
			interpreter = PDFPageInterpreter(rsrcmgr, device)
			pages = PDFPage.get_pages(fp)

			cat_n = pd.DataFrame(columns=['name', 'x0', 'x1', 'y0', 'y1', 'height', 'width', 'page_num'])

			num = 0
			for page in pages:
				num = num + 1
				interpreter.process_page(page)
				layout = device.get_result()
				for lobj in layout:
					if isinstance(lobj, LTTextBox):
						x0, y1, text = lobj.bbox[0], lobj.bbox[3], lobj.get_text().split('\n')[0]
						x1, y0 = lobj.bbox[2], lobj.bbox[1]
						tmp = cat_list[cat_list['page_num'] == num].copy()
						tmp = tmp[cat_list['y1'].between(0.97 * y1, 1.03 * y1)]
						tmp = tmp[tmp['x0'].between(0.97 * x0, 1.03 * x1)]
						tmp['name'] = text
						if len(cat_list[cat_list['y1'].between(0.97 * y1, 1.03 * y1)]['name']) > 0:
							if (text != cat_list[cat_list['y1'].between(0.97 * y1, 1.03 * y1)]['name'].values[0]):
								tmp['x0'] = x0

					cat_n = cat_n.append(tmp, ignore_index=True)

			# End parse from pdf_miner
			cat_n = cat_n[cat_n['name'].apply(lambda x: sum(c.isdigit() for c in x) / len(x) < 0.5)]

			try:
				cat_n = delete_empty_names(cat_n)
			except Exception as e:
				cat_n = cat_n

			if len(cat_n) >= len(cat_list):
				Categories = cat_n
			else:
				Categories = cat_list

			 # Finding {dishes + prices}
			items = items.sort_values(['page_num', 'x0', 'y1'], ascending=[True, True, False])
			items.reset_index(inplace=True, drop=True)
			dishes_prices_flag = pd.DataFrame(columns=['name', 'x0', 'x1', 'y0', 'y1', 'height', 'width', 'page_num'])
			for i in items.index.values:
				tmp_e = items.iloc[[i]]
				e_right = find_closest_right(tmp_e, items, is_same_level=False)
				if len(e_right) > 0:
					if is_separate_price(list(e_right['name'])[0]):
						dishes_prices_flag = dishes_prices_flag.append(tmp_e, ignore_index=True)

			try:
				Heights_items = pd.crosstab(index=dishes_prices_flag["height"], columns="count")
				Heights_items = Heights_items[Heights_items['count'] > min_cat_count]
				tmp_h = Heights_items[Heights_items['count'] == max(Heights_items['count'])].index.values[0]
				dishes_prices = items[items['height'].between(0.99 * tmp_h, 1.01 * tmp_h)]
			except:
				Heights_items = Heights

			try:
				dishes_prices = delete_empty_names(dishes_prices)
				dishes_prices = cut_prices_form_df(dishes_prices)
			except Exception as e:
				print("Error! Without with dishes_prices")

			# Finding {dishes} + {prices}
			items = items.sort_values(['page_num', 'x0', 'y1'], ascending=[True, True, False])
			items.reset_index(inplace=True, drop=True)

			dishes_and_prices = pd.DataFrame(columns=['name', 'x0', 'x1', 'y0', 'y1', 'height', 'width', 'page_num'])
			for i in items.index.values:
				tmp_e = items.iloc[[i]]
				if is_dish_with_price(tmp_e):
					dishes_and_prices = dishes_and_prices.append(tmp_e, ignore_index=True)

			try:
				Heights_items_prices = pd.crosstab(index=dishes_and_prices["height"], columns="count")
				Heights_items_prices = Heights_items_prices[Heights_items_prices['count'] > min_cat_count]
			except:
				Heights_items_prices = Heights

			# Finding {dishes} or {dishes + prices}

			Is_Dish_With_Price = False
			if len(dishes_prices_flag) >= len(dishes_and_prices):
				Dishes = dishes_prices
			else:
				Dishes = dishes_and_prices
				Is_Dish_With_Price = True

			#Dishes.to_csv(r'F:\100nuts\Dishes.txt', header=True, index=True, sep=';', mode='a')

			# CASE: {dish} + {price}
			#print("Go in CASE:  {dish} + {price}")
			if (Is_Dish_With_Price == False):
				print("File %s go to GASE 1" % file_name)
				tmp_dishes = get_items_dish_price(items)
				Dishes = tmp_dishes
				Dishes = cut_prices_form_df(Dishes)

			# Define categoty's H {dish} + {price}
				try:
					cat_tmp_h = round3(max(Heights_items[Heights_items['count'] >= min_cat_count].index.values))
				except:
					cat_tmp_h = 0

				Is_Current_Cat = True
				if abs(cat_h - cat_tmp_h) / cat_h > 0.05:
					Is_Current_Cat = False
					Categories = items[items['height'] == cat_tmp_h]
					Categories = delete_empty_names(Categories)
					Categories = cut_prices_form_df(Categories)

				#print("The cats are %s" % Is_Current_Cat)


				# Define Prices CASE: {dish} + {price}
				Prices = get_prices_dish_price(Dishes, items)
				Prices = get_post_prices_dish_price(Prices, Prices['height'].median())
				Prices = collapse_prices(Prices)

				# Define Descriptions CASE: {dish} + {price}
				Descriptions = get_description_dish_price(_Dishes=Dishes, _items=items, _Prices=Prices)

				# Result for CASE: {dish} + {price}
				tmp_Result = get_Result(_Dish=Dishes, _Categories=Categories, _Prices=Prices, _Description=Descriptions,
									_filename=file_name, _Vegans=Vegans)

				tmp_Result['rest_id'] = Rest_id
				tmp_Result['file_name'] = file_name
				tmp_Result['menu_link'] = None
				tmp_Result['rest_name'] = folder_input_short
				tmp_Result['update_time'] = time_log
				tmp_Result['menu_type'] = file_name

				parsed_items_count = len(Dishes) + len(Categories) + len(Prices) + len(Descriptions)

				query = "INSERT INTO dbo.pdf_convert_log([time], [file_path], [file_folder], [file_name], " \
						"[is_picture], [file_size], [page_count],[download_file_time], [algo_number]," \
						"[is_parsed], [items_count], [parsed_items_count]) " \
						"values (convert(smalldatetime, '%s', 121), '%s', '%s', '%s', %s,%s,%s,%s,%s,%s,%s,%s)" % (
							time_log, path_in_str, folder_input_name, file_name, 0, file_size,
							page_num_max, time_file_down, 1, 1, len(items), parsed_items_count)
				sql_log1 = msSQL.msSQL(connStr)
				sql_log1.insert_to_log(query)

				for i in range(0, len(tmp_Result)):
					query = "INSERT INTO dbo.menues([item_name], [description],[veg_comment],[price] ,[category], " \
							"[file_name],[restaurant_name], [menu_type], [int_id] ,[update_time] ) " \
							"values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', " \
							"'%s', %s, convert(smalldatetime, '%s', 121))" % (tmp_Result.iloc[i]['item_name'],
																			  tmp_Result.iloc[i]['description'],
																			  tmp_Result.iloc[i]['veg_comment'],
																			  tmp_Result.iloc[i]['price'],
																			  tmp_Result.iloc[i]['category'],
																			  tmp_Result.iloc[i]['file_name'],
																			  tmp_Result.iloc[i]['rest_name'],
																			  tmp_Result.iloc[i]['menu_type'],
																			  tmp_Result.iloc[i]['rest_id'],
																			  tmp_Result.iloc[i]['update_time'])
					sql_add_items = msSQL.msSQL(connStr)
					sql_add_items.insert_to_log(query)

			# Result for CASE {dish + price}
			if (Is_Dish_With_Price == True):
				tmp_Result2 = get_Result_dish_with_price(_Dish=dishes_and_prices, _Items=items,
														 _filename=file_name, _Vegans=Vegans)

				tmp_Result2['rest_id'] = Rest_id
				tmp_Result2['file_name'] = file_name
				tmp_Result2['menu_link'] = None
				tmp_Result2['rest_name'] = folder_input_short
				tmp_Result2['update_time'] = time_log
				tmp_Result2['menu_type'] = file_name

				parsed_items_count = len(tmp_Result2) - sum(tmp_Result2[['item_name']].isnull().sum(axis=1))
				parsed_items_count = parsed_items_count +\
									 len(tmp_Result2) - sum(tmp_Result2[['description']].isnull().sum(axis=1))

				parsed_items_count = parsed_items_count + \
									 len(tmp_Result2) - sum(tmp_Result2[['price']].isnull().sum(axis=1))

				query = "INSERT INTO dbo.pdf_convert_log([time], [file_path], [file_folder], [file_name], " \
						"[is_picture], [file_size], [page_count],[download_file_time], [algo_number]," \
						"[is_parsed], [items_count], [parsed_items_count]) " \
						"values (convert(smalldatetime, '%s', 121), '%s', '%s', '%s', %s,%s,%s,%s,%s,%s,%s,%s)" % (
							time_log, path_in_str, folder_input_name, file_name, 0, file_size,
							page_num_max, time_file_down, 2, 1, len(items), parsed_items_count)
				sql_log2 = msSQL.msSQL(connStr)
				sql_log2.insert_to_log(query)

				for i in range(0, len(tmp_Result2)):
					query = "INSERT INTO dbo.menues([item_name], [description],[veg_comment],[price] ,[category], " \
							"[file_name],[restaurant_name], [menu_type], [int_id] ,[update_time] ) " \
							"values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', " \
							"'%s', %s, convert(smalldatetime, '%s', 121))" % (tmp_Result2.iloc[i]['item_name'],
																			  tmp_Result2.iloc[i]['description'],
																			  tmp_Result2.iloc[i]['veg_comment'],
																			  tmp_Result2.iloc[i]['price'],
																			  tmp_Result2.iloc[i]['category'],
																			  tmp_Result2.iloc[i]['file_name'],
																			  tmp_Result2.iloc[i]['rest_name'],
																			  tmp_Result2.iloc[i]['menu_type'],
																			  tmp_Result2.iloc[i]['rest_id'],
																			  tmp_Result2.iloc[i]['update_time'])
					sql_add_items = msSQL.msSQL(connStr)
					sql_add_items.insert_to_log(query)

				# Draw layout with categories

			try:
				path_layout_out = r'%s\%s\%s.pdf' % (setting['path_layout_folder'], folder_input_name, file_name)
				rect_cat = pdf_rectangle.Rectangle(input_df=Categories, path_output=path_layout_out, pdf_path=path_in_str)
				rect_cat.pdf_splitter()
				rect_cat.draw_recs()
				rect_cat.draw_dishes(df=Dishes)
				rect_cat.draw_prices(df=Prices)
				rect_cat.draw_desc(df=Descriptions)
				# Create new folder with rest_name
				rect_cat.create_folder(folder_name=folder_input_name)
				rect_cat.merger()
			except Exception as e:
				print(e)
		except Exception as e:
			print(e)
			print("Exeption. Pdf file %s is not downloaded" % file_name)
			query = "INSERT INTO dbo.pdf_convert_log([time], [file_path], [file_folder], [file_name], " \
					"[file_size],  [is_parsed]) " \
					"values (convert(smalldatetime, '%s', 121), '%s', '%s', '%s', %s, %s)" % (
						time_log, path_in_str, folder_input_name, file_name, file_size, 0)
			sql_log = msSQL.msSQL(connStr)
			sql_log.insert_to_log(query)

	#Updating progres bar
		# finally:
		# 	 Rest_id = Rest_id + 1