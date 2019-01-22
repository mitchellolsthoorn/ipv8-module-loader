# ipv8-dapps-loader

## Setup
```
pip install -r pyipv8/requirements.txt
pip install -r requirements.txt
export PYTHONPATH="${PYTHONPATH}:."
```

## Run single instance
```
twistd -n dapp -s <state directory location>
```

## Run multiple instances on a single computer
```
twistd --pidfile <state directory location 1>/twistd.pid -n dapp -s <state directory location 1>
twistd --pidfile <state directory location 2>/twistd.pid -n dapp -s <state directory location 2>
```