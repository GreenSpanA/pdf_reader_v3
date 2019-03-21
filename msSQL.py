import pyodbc


class msSQL:

	def __init__(self, constring):
		self.path = constring


	def insert_to_log(self, query):
		connStr = pyodbc.connect("DRIVER={ODBC Driver 13 for SQL Server};"
								 "SERVER=DESKTOP-I46RHJS;"
								 "DATABASE=Menus;"
								 "Trusted_Connection=yes")
		cursor = connStr.cursor()
		try:
			#cursor = connStr.cursor()
			cursor.execute(query)
			cursor.fast_executemany
			connStr.commit()
			cursor.close()
		except (Exception, pyodbc.DatabaseError) as e:
			print(e)
			print("SQL ERROR: %s" % query)
		finally:
			if connStr is not None:
				connStr.close()
		return