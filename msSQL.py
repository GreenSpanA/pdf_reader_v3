import pyodbc


class msSQL:
	# Connection string
	connStr = pyodbc.connect("DRIVER={ODBC Driver 13 for SQL Server};"
                             "SERVER=DESKTOP-I46RHJS;"
                             "DATABASE=Menus;"
                             "Trusted_Connection=yes")

	def __init__(self, query):
		self.sql = query

	def insert_to_log(self):
		cursor = self.connStr.cursor()
		cursor.execute(self.query)
		self.connStr.commit()
		cursor.close()
		self.connStr.close()
		return