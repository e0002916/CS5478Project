# CS5478Project

### Pre-Requisites
```
https://github.com/rqlite/rqlite/releases
https://github.com/cyberbotics/webots
https://www.rabbitmq.com/install-debian.html

pip install git+https://github.com/rqlite/pyrqlite.git
pip install fastpi farm-haystack uvicorn[standard] pika rasa
```

### Setup
```
# Note, rqlite is assumed to be fixed at localhost:4001
sudo systemctl start rabbitmq-server
sudo systemctl start rqlited
export PYTHONPATH=$PYTHONPATH:/usr/local/webots/lib/controller/python:/[Path-To-CS5478Project]/lib:[Path-ToCS5478Project]/api
```

### TODO
```
Proper error response from controller to signal invalid input
try adding prompt data_store only if train=False
```


### Example Commands
```
curl -X 'GET'   'http://127.0.0.1:8000/query/?query=Find%20out%20the%20x%2Cy%20coordinates%20of%20the%20waypoint%20called%20dropoff%20and%20move%20robot%20MiR100%20there'   -H 'accept: application/json'

curl -X 'GET' \
  'http://127.0.0.1:8000/query/?query=dispense%20a%20item%20called%20coke%20from%20the%20dispenser%20called%20ConveyorBelt1_dispenser.%20There%20is%20always%20coke%20in%20the%20dispenser' \
  -H 'accept: application/json'
```
