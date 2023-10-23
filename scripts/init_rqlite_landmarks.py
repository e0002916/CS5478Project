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
        cursor.execute('INSERT INTO landmarks(name, x, y, level) VALUES("UR10e_1_pickup", -6.3, -7.97, 0)')
        cursor.execute('INSERT INTO landmarks(name, x, y, level) VALUES("dropoff", -0.00931563, 5.04191, 0)')
finally:
    connection.close()
