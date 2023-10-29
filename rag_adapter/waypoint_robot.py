import json
import pika
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.exchange_declare(exchange='move',
                         exchange_type='direct')

def generate_swagger():
   return get_openapi(
       title=f"{__file__} API",
       version="1.0.0",
       description="Your API description",
       routes=app.routes,
   )

app = FastAPI()

@app.put("/move/{robot}/{landmark}")
async def move(robot, landmark):
    message = {"name": landmark, "level": "0"}
    channel.queue_declare(queue=robot)
    channel.basic_publish(exchange='move',
                          routing_key=robot,
                          body=json.dumps(message))
    return True

if __name__ == "__main__":
    swagger = generate_swagger()
    with open(f"{__file__}.swagger.json", "w") as file:
        json.dump(swagger, file)
