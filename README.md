# CS5478Project

### Pre-Requisites
```
https://github.com/rqlite/rqlite/releases
https://github.com/cyberbotics/webots
https://www.rabbitmq.com/install-debian.html

pip install git+https://github.com/rqlite/pyrqlite.git
pip install fastpi farm-haystack uvicorn[standard] pika
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
