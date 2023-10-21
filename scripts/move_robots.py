import pika
import time

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.exchange_declare(exchange='move',
                         exchange_type='fanout')

channel.queue_declare(queue='Mir100_1')

channel.basic_publish(exchange='move',
                      routing_key='Mir100_1',
                      body='{"name": "PICKUP", "level": "0"}')

input("Press Enter to continue...")

channel.basic_publish(exchange='move',
                      routing_key='Mir100_1',
                      body='{"name": "A", "level": "0"}')

connection.close()
