import pika
import time

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.exchange_declare(exchange='move',
                         exchange_type='fanout')

channel.queue_declare(queue='Mir100_1')

channel.basic_publish(exchange='move',
                      routing_key='Mir100_1',
                      body='{"name": "A", "level": "0"}')
time.sleep(3)
channel.basic_publish(exchange='move',
                      routing_key='Mir100_1',
                      body='{"name": "B", "level": "0"}')
time.sleep(3)
channel.basic_publish(exchange='move',
                      routing_key='Mir100_1',
                      body='{"name": "C", "level": "0"}')
time.sleep(3)
channel.basic_publish(exchange='move',
                      routing_key='Mir100_1',
                      body='{"name": "D", "level": "0"}')
time.sleep(3)

connection.close()
