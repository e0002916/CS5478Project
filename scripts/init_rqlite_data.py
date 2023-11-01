import pyrqlite.dbapi2 as dbapi2

# Connect to the database
connection = dbapi2.connect(
    host='localhost',
    port=4001,
)

try:
    with connection.cursor() as cursor:
        cursor.execute('DROP TABLE IF EXISTS waypoints')
        cursor.execute('CREATE TABLE waypoints (id integer not null primary key autoincrement, name text unique, x float, y float, level integer)')
        cursor.execute('INSERT INTO waypoints(name, x, y, level) VALUES("Mir100_1_start", -5, -6.3, 0)')
        cursor.execute('INSERT INTO waypoints(name, x, y, level) VALUES("Mir100_2_start", 0, -6.3, 0)')
        cursor.execute('INSERT INTO waypoints(name, x, y, level) VALUES("Mir100_3_start", 5, -6.3, 0)')
        cursor.execute('INSERT INTO waypoints(name, x, y, level) VALUES("UR10e_1_pickup", -6.3, -7.97, 0)')
        cursor.execute('INSERT INTO waypoints(name, x, y, level) VALUES("dropoff", -0.00931563, 5.04191, 0)')

        cursor.execute('DROP TABLE IF EXISTS dispensers')
        cursor.execute('CREATE TABLE dispenser (id integer not null primary key autoincrement, name text unique, x float, y float, z float, level integer)')
        cursor.execute('INSERT INTO dispenser(name, x, y, z, level) VALUES("ConveyorBelt1_dispenser", -4.3, -9.57, 0.37, 0)')
        cursor.execute('INSERT INTO dispenser(name, x, y, z, level) VALUES("ConveyorBelt2_dispenser", 0.63, -9.59, 0.37, 0)')
        cursor.execute('INSERT INTO dispenser(name, x, y, z, level) VALUES("ConveyorBelt3_dispenser", 5.58, -9.59, 0.37, 0)')
finally:
    connection.close()
