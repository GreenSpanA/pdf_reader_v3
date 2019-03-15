import pdfquery
import pandas as pd
import re
from pdf_reader import get_name, get_diff3, get_coordinates


class PdfFile:
	# Structure of DataFrame with items
	df_columns = ['name', 'x0', 'x1', 'y0', 'y1', 'height', 'width', 'page_num']

	# Initializer
	def __init__(self, path):
		self.path = path

	# Download pdf file into object
	def pdf_download(self):
		pdf = pdfquery.PDFQuery(self.path)
		pdf.load()
		return pdf

	# Get coordinates from LTTextLineHorizontal string
	@staticmethod
	def get_coordinates(tmp_str):
		tmp_str = re.findall(r'\s([\d\.\,\-]+)\s', tmp_str)[0]
		tmp_coord = tmp_str.split(",")
		# tmp_coord = np.around(tmp_coord, decimals=3)
		return [(lambda x: round(float(x), 3))(x) for x in tmp_coord]

	# Get names of items
	@staticmethod
	def get_name(tmp_str):
		if len(re.findall(r'"([^"]*)"', tmp_str)) == 0:
			tmp_str = re.findall(r'\#(.+)\#', tmp_str.translate(str.maketrans({"'": '#'})))[0]
		else:
			tmp_str = re.findall(r'"([^"]*)"', tmp_str)[0]
		tmp_str = tmp_str.replace("\\n", "")
		return tmp_str

	# Obtain pd.DataFrame with all items in pdf file.
	def get_items(self):
		pdf = pdfquery.PDFQuery(self.path)
		print('Start downloading pdf...')
		pdf.load()
		items = pd.DataFrame(columns=self.df_columns)
		pq_items = pdf.pq('LTTextBoxVertical, LTTextLineHorizontal')
		try:
			for pq in pq_items:

				page_pq = next(pq.iterancestors('LTPage'))  # Use just the first ancestor
				page_num = page_pq.layout.pageid
				cur_str_item = str(pq.layout)
				tmp_items = pd.DataFrame([[
					get_name(cur_str_item),
					float(get_coordinates(cur_str_item)[0]),
					float(get_coordinates(cur_str_item)[2]),
					float(get_coordinates(cur_str_item)[1]),
					float(get_coordinates(cur_str_item)[3])
				]],
					columns=['name', 'x0', 'x1', 'y0', 'y1'])
				tmp_items['height'] = get_diff3(tmp_items['y1'], tmp_items['y0'])
				tmp_items['width'] = get_diff3(tmp_items['x1'], tmp_items['x0'])
				tmp_items['page_num'] = page_num

				items = items.append(tmp_items, ignore_index=True)

		except Exception as e:
			items = pd.DataFrame(columns=self.df_columns)

		finally:
			return items