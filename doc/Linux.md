# Install

The control web page needs:

    sudo apt install git nodejs node-js-yaml

### Python packages from Debian:

    sudo apt install python3-numpy python3-scipy python3-matplotlib \
             python3-yaml python3-jack-client python3-watchdog \
             python3-websocket

### Python packages not provided by Debian:

`sounddevice` and `pycamilladsp`

You need to prepare a Python Virtual Environment for your user (by inheriting the system Python packages)

```
$ python -m venv --system-site-packages ~/.env
$ source ~/.env/bin/activate
(.env) $ pip3 install sounddevice
(.env) $ pip3 install git+https://github.com/HEnquist/pycamilladsp.git

You can now deactivate the Python Env BUT it is not necessary

(.env) $ deactivate
$
```

