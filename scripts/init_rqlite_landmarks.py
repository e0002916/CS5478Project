import pyrqlite.dbapi2 as dbapi2

# Connect to the database
connection = dbapi2.connect(
    host='localhost',
    port=4001,
)

try:
    with connection.cursor() as cursor:
        cursor.execute('DROP TABLE IF EXISTS landmarks')
        cursor.execute('CREATE TABLE landmarks (id integer not null primary key autoincrement, name text unique, x float, y float, level integer)')
        cursor.execute('INSERT INTO landmarks(name, x, y, level) VALUES("MiR100_1_start", -5, -6.3, 0)')
        cursor.execute('INSERT INTO landmarks(name, x, y, level) VALUES("MiR100_2_start", 0, -6.3, 0)')
        cursor.execute('INSERT INTO landmarks(name, x, y, level) VALUES("MiR100_3_start", 5, -6.3, 0)')
finally:
    connection.close()
