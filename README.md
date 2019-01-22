# ipv8-dapps-loader

## Setup
```
pip install -r loader/pyipv8/requirements.txt
pip install -r requirements.txt
export PYTHONPATH="${PYTHONPATH}:."
```

## Run single instance
```
twistd -n dapp -s state
```

## Run multiple instances on a single computer
```
twistd --pidfile 1/twistd.pid -n dapp -s 1
twistd --pidfile 2/twistd.pid -n dapp -s 2
```