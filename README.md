# ipv8-module-loader

## Setup
```
pip install -r requirements.txt
sudo apt install python-libtorrent
export PYTHONPATH="${PYTHONPATH}:."
```

## Run single instance
```
twistd -n module-loader -s <state directory location>
```

Example:
```
twistd -n module-loader -s data/one
```

## Run multiple instances on a single computer
```
twistd --pidfile twistd1.pid -n module-loader -s <state directory location 1>
twistd --pidfile twistd2.pid -n module-loader -s <state directory location 2>
...
twistd --pidfile twistdX.pid -n module-loader -s <state directory location X>
```

Example:
```
twistd --pidfile twistd1.pid -n module-loader -s data/one
twistd --pidfile twistd2.pid -n module-loader -s data/two
```