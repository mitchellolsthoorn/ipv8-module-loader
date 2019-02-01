# ipv8-dapps-loader

## Setup
```
pip install -r requirements.txt
sudo apt install python-libtorrent
export PYTHONPATH="${PYTHONPATH}:."
```

## Run single instance
```
twistd -n dapp -s <state directory location>
```

Example:
```
twistd -n dapp -s data/one
```

## Run multiple instances on a single computer
```
twistd --pidfile twistd1.pid -n dapp -s <state directory location 1>
twistd --pidfile twistd2.pid -n dapp -s <state directory location 2>
...
twistd --pidfile twistdX.pid -n dapp -s <state directory location X>
```

Example:
```
twistd --pidfile twistd1.pid -n dapp -s data/one
twistd --pidfile twistd2.pid -n dapp -s data/two
```