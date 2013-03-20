A transparent reverse protocol agnostic socks proxy. It allows you to setup gateways to an onion and to hide the address of a reverse proxy from the server and the server's address from the general public. The main purpose is to allow clearnet access to tor hidden services.

To configure simply set the configuration parameters in config.py and then run:

    ./proxy start

It only requires root if the listener port is less than 1024.

### Licensing

This project is licensed under the GPLv3.

### Credit

jtripper (c) 2013

jack@jtripper.net
