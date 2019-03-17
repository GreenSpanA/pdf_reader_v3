from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.colors import pink, black, red, blue, green
pdfmetrics.registerFont(TTFont('Vera', 'Vera.ttf'))
pdfmetrics.registerFont(TTFont('VeraBd', 'VeraBd.ttf'))
pdfmetrics.registerFont(TTFont('VeraIt', 'VeraIt.ttf'))
pdfmetrics.registerFont(TTFont('VeraBI', 'VeraBI.ttf'))
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor
from PyPDF2 import PdfFileWriter, PdfFileReader
import os
import glob
from pathlib import Path

class Rectangle:
	# Initializer
	folder_splitted = r'F:\100nuts\MENUES_LAYOTED\Splitted_Files'
	folder_splitted_layoted = r'F:\100nuts\MENUES_LAYOTED\Splitted_Files\Layoted\Categories'
	folder_splitted_layoted_dishes = r'F:\100nuts\MENUES_LAYOTED\Splitted_Files\Layoted\Dishes'
	folder_layoted = r'F:\100nuts\MENUS_OUT'

	def __init__(self, input_df, path_output, pdf_path):
		self.input_df = input_df
		self.path_output = path_output
		self.pdf_path = pdf_path

	@staticmethod
	def remove_from_folder(folder):
		for the_file in os.listdir(folder):
			file_path = os.path.join(folder, the_file)
			try:
				if os.path.isfile(file_path):
					os.unlink(file_path)
			except Exception as e:
				print(e)
		return

	def pdf_splitter(self):
		Rectangle.remove_from_folder(self.folder_splitted_layoted)
		Rectangle.remove_from_folder(self.folder_splitted)
		Rectangle.remove_from_folder(self.folder_splitted_layoted_dishes)
		path = self.pdf_path
		folder_out = self.folder_splitted
		fname = os.path.splitext(os.path.basename(path))[0]

		pdf = PdfFileReader(path)
		for page in range(pdf.getNumPages()):
			pdf_writer = PdfFileWriter()
			pdf_writer.addPage(pdf.getPage(page))

			output_filename = '{}\{}_page_{}.pdf'.format(folder_out, fname,
														 page + 1)

			with open(output_filename, 'wb') as out:
				pdf_writer.write(out)

			print('Created: {}'.format(output_filename))

	def out_pathes(self):
		output_path = self.folder_splitted_layoted_dishes
		tmp = r'%s\*.pdf' % output_path
		paths = glob.glob(tmp)
		paths.sort()
		return paths

	def create_folder(self, folder_name):
		path = self.folder_layoted
		tmp_path = r'%s\%s' % (path, folder_name)
		if not os.path.exists(tmp_path):
			os.makedirs(tmp_path)

	def merger(self):
		input_paths = Rectangle.out_pathes(self)
		output_path = self.path_output
		pdf_writer = PdfFileWriter()

		for path in input_paths:
			path = path.replace("\\", "/")
			pdf_reader = PdfFileReader(path)
			for page in range(pdf_reader.getNumPages()):
				pdf_writer.addPage(pdf_reader.getPage(page))

		with open(output_path, 'wb') as fh:
			pdf_writer.write(fh)


	def pdf_boundary_boxes(self, df, path_input, path_output, page_num=0, show_height=True, show_number=False, r=0, g=1, b=0.4, color=''):
		#path_input = self.folder_splitted
		#path_output = self.folder_splitted_layoted
		#df = self.input_df

		packet = io.BytesIO()
		# create a new PDF with Reportlab
		can = canvas.Canvas(packet, pagesize=letter)
		can.setFont('Vera', 6)
		# can.setStrokeColorRGB(r, g, b)
		can.setStrokeColor(color)
		# x0, y0, x1, y1
		for i in range(0, len(df)):
			# bottom line
			can.line(df.iloc[i]['x0'], df.iloc[i]['y0'], df.iloc[i]['x1'],
					 df.iloc[i]['y0'])

			# right line
			can.line(df.iloc[i]['x1'], df.iloc[i]['y0'], df.iloc[i]['x1'],
					 df.iloc[i]['y1'])

			# upper line
			can.line(df.iloc[i]['x1'], df.iloc[i]['y1'], df.iloc[i]['x0'],
					 df.iloc[i]['y1'])

			# text with height

			if show_number:
				can.drawString(df.iloc[i]['x1'], 0.5 * (df.iloc[i]['y1'] + df.iloc[i]['y0']),
							   "(%s)" % (i))
			if show_height:
				can.drawString(df.iloc[i]['x1'], df.iloc[i]['y1'],
							   "(%s)" % (df.iloc[i]['height']))

			# left line
			can.line(df.iloc[i]['x0'], df.iloc[i]['y1'], df.iloc[i]['x0'],
					 df.iloc[i]['y0'])

		can.save()

		# move to the beginning of the StringIO buffer
		packet.seek(0)
		new_pdf = PdfFileReader(packet)
		# read your existing PDF
		existing_pdf = PdfFileReader(open(path_input, "rb"))
		output = PdfFileWriter()
		# add the "watermark" zero page existing page
		page = existing_pdf.getPage(page_num)
		page.mergePage(new_pdf.getPage(page_num))
		output.addPage(page)
		# finally, write "output" to a real file
		outputStream = open(path_output, "wb")
		output.write(outputStream)
		outputStream.close()
		return

	def draw_recs(self, item_entity='cat'):
		df = self.input_df
		for i in list(df['page_num'].unique()):
			path = self.pdf_path
			fname = os.path.splitext(os.path.basename(path))[0]
			path_input = r'%s\%s_page_%s.pdf' % (self.folder_splitted, fname, i)
			path_output = r'%s\%s_page_%s_%s.pdf' % (self.folder_splitted_layoted, fname, i, item_entity)

			print("Input is %s; output is %s" % (path_input, path_output))

			Rectangle.pdf_boundary_boxes(self, path_input=path_input, path_output=path_output,
										 df=df[df['page_num'] == i], show_height=False, color='green')
		return

	def draw_dishes(self, df, item_entity='items'):
		for i in list(df['page_num'].unique()):
			path = self.pdf_path
			fname = os.path.splitext(os.path.basename(path))[0]
			path_input = r'%s\%s_page_%s_%s.pdf' % (self.folder_splitted_layoted, fname, i, 'cat')
			print("NEW: %s" % path_input)
			path_output = r'%s\%s_page_%s_%s.pdf' % (self.folder_splitted_layoted_dishes, fname, i, item_entity)

			print("Input is %s; output is %s" % (path_input, path_output))

			Rectangle.pdf_boundary_boxes(self, path_input=path_input, path_output=path_output,
										 df=df[df['page_num'] == i], show_height=False, color='red')

