# Juniper Configuration Push Script

This basic python script takes configuration files (set or stanza based) and pushes them to Juniper routers over NETCONF.

It uses the Juniper PyEZ libraries for NETCONF.

## Help:

usage: 

    config_push.py [-h] [-t] [-f] [-d] routers_file config_file config_format


positional arguments:

    routers_file   File that contains a list of routers to update
    config_file    File that contains config you want to push
    config_format  Format of the config: xml, text or set

optional arguments:

    -h, --help     show this help message and exit
    -t             Test run. Apply the config, run a 'show | compare' then
                   rollback. The change is not committed.
    -f             Execute a 'commit full'
    -d             If the -d flag is set, 'config_file' is a directory. Here
                   device specific configs are stored. Is it used to push
                   different configs to each router. Configs must be named
                   ${Device}.conf
 
