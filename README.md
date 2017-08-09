# vmorphan
Find orphaned files on VMWare storages

This script scan all available datastores and check them against internal VMWare database. If it found some lost files, it show path to them. Check or pass them to delete utility - its up to you

```
usage: vmorphan.py [-h] -s HOST [-o PORT] -u USER [-p PASSWORD] [-S] [-n NAME]
                   [-v] [-V]

Standard Arguments for talking to vCenter

optional arguments:
  -h, --help            show this help message and exit
  -s HOST, --host HOST  vSphere service to connect to
  -o PORT, --port PORT  Port to connect on
  -u USER, --user USER  User name to use when connecting to host
  -p PASSWORD, --password PASSWORD
                        Password to use when connecting to host
  -S, --disable_ssl_verification
                        Disable ssl host certificate verification
  -n NAME, --name NAME  Restrict only to this Datastore.
  -v, --verbose         Show what doing now.
  -V, --veryverbose     Hey! Show me everything! ALL actions!

```

Scripts was written in "as fast as possible" mode, so some errors can happen.