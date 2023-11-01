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
sudo systemctl start rabbitmq-server
sudo systemctl start rqlited
export PYTHONPATH=$PYTHONPATH:/usr/local/webots/lib/controller/python:/[Path-To-CS5478Project]/lib
```
