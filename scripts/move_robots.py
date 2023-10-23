import pika
import time

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.exchange_declare(exchange='move',
                         exchange_type='direct')

channel.exchange_declare(exchange='dispense',
                         exchange_type='direct')

channel.queue_declare(queue='Mir100_1')
channel.queue_declare(queue='dispenser')


channel.basic_publish(exchange='move',
                      routing_key='Mir100_1',
                      body='{"name": "UR10e_1_pickup", "level": "0"}')

input("Press Enter to continue...")

channel.basic_publish(exchange='dispense',
                      routing_key='dispenser',
                      body='{"item": "Can", "dispenserId": "ConveyorBelt1"}')

input("Press Enter to continue...")

channel.basic_publish(exchange='move',
                      routing_key='Mir100_1',
                      body='{"name": "dropoff", "level": "0"}')

input("Press Enter to continue...")

channel.basic_publish(exchange='move',
                      routing_key='Mir100_1',
                      body='{"name": "MiR100_1_start", "level": "0"}')

connection.close()
