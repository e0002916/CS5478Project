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
        cursor.execute('INSERT INTO landmarks(name, x, y, level) VALUES("Mir100_1_start", -5, -6.3, 0)')
        cursor.execute('INSERT INTO landmarks(name, x, y, level) VALUES("Mir100_2_start", 0, -6.3, 0)')
        cursor.execute('INSERT INTO landmarks(name, x, y, level) VALUES("Mir100_3_start", 5, -6.3, 0)')
        cursor.execute('INSERT INTO landmarks(name, x, y, level) VALUES("UR10e_1_pickup", -6.3, -7.97, 0)')
        cursor.execute('INSERT INTO landmarks(name, x, y, level) VALUES("dropoff", -0.00931563, 5.04191, 0)')

        cursor.execute('DROP TABLE IF EXISTS entities')
        cursor.execute('CREATE TABLE entities (id integer not null primary key autoincrement, name text unique)')
        cursor.execute('INSERT INTO entities(name) VALUES("Mir100_1")')
        cursor.execute('INSERT INTO entities(name) VALUES("Mir100_2")')
        cursor.execute('INSERT INTO entities(name) VALUES("Mir100_3")')

        cursor.execute('DROP TABLE IF EXISTS dispenserLocation')
        cursor.execute('CREATE TABLE dispenserLocation (id integer not null primary key autoincrement, name text unique, x float, y float, z float)')
        cursor.execute('INSERT INTO dispenserLocation(name, x, y, z) VALUES("ConveyorBelt1", -4.3, -9.57, 0.37)')
        cursor.execute('INSERT INTO dispenserLocation(name, x, y, z) VALUES("ConveyorBelt2", 0.63, -9.59, 0.37)')
        cursor.execute('INSERT INTO dispenserLocation(name, x, y, z) VALUES("ConveyorBelt3", 5.58, -9.59, 0.37)')
finally:
    connection.close()
