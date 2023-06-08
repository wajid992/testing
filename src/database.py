from mysql.connector import connect

HOST = "50.87.151.159"
USER = "educonne_Huzaifa"
PASSWORD = "1+rG%-7LMy2E"
DATABASE = "educonne_CourseData"

def interect_with_database(func, commit=False):
	with connect(
		host=HOST,user=USER,password=PASSWORD,database = DATABASE
	) as connection:
		with connection.cursor() as cursor:
			returned = func(cursor)
		if commit:
			connection.commit()
	return returned