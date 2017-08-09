#!/usr/bin/env python
# This script scan all available datastores and check them against
# internal VMWare database. 
# all what you want to install - only pyvmomi
# pip install pyvmomi

import atexit
import requests
import ssl
import sys
import time
from tools import cli
from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect

# here stores files URL like this
# [vm-stor10] PET-1498002939529/AS-139529Snapshot2.vmsn

file_info = []

# disable  urllib3 warnings
if hasattr(requests.packages.urllib3, 'disable_warnings'):
    requests.packages.urllib3.disable_warnings()


def get_args():
    parser = cli.build_arg_parser()
    parser.add_argument('-n', '--name', required=False,
                        help="Restrict only to this Datastore.")
    parser.add_argument('-v', '--verbose', required=False, action='store_true',
                        help="Show what doing now.")
    parser.add_argument('-V', '--veryverbose', required=False, action='store_true',
                        help="Hey! Show me everything! ALL actions!")
    my_args = parser.parse_args()
    return cli.prompt_for_password(my_args)

args = get_args()


def get_obj(content, vim_type, name=None):
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vim_type, True)
    if name:
        for c in container.view:
            if c.name == name:
                obj = c
                return [obj]
    else:
        return container.view


# http://stackoverflow.com/questions/1094841/
def sizeof_fmt(num):
    """
    Returns the human readable version of a file size

    :param num:
    :return:
    """
    for item in ['B', 'KB', 'MB', 'GB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, item)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')


def print_datastore_info(ds_obj):
    total = 0 
    summary = ds_obj.summary
    ds_capacity = summary.capacity
    ds_freespace = summary.freeSpace
    ds_uncommitted = summary.uncommitted if summary.uncommitted else 0
    ds_provisioned = ds_capacity - ds_freespace + ds_uncommitted
    ds_overp = ds_provisioned - ds_capacity
    ds_overp_pct = (ds_overp * 100) / ds_capacity \
        if ds_capacity else 0

    for item in ds_obj.vm: # get list of VM in
        for t in item.layoutEx.file: # get list of every vm file
            if args.veryverbose:
                print "CH %s " % t.name
            if t.name not in file_info: # filename not in collected list?
                if args.veryverbose:
                    print "NF %s " % t.name
                if summary.name in t.name: # is this file on our stor?
                    if ".vmsn" not in t.name: # skip snapshots - they not listed by default
                        print "%s %s" % (t.name, sizeof_fmt(t.size)) # gotcha! show them 
                        total = total + t.size
    
    if args.verbose:
        print "%s : can cleaned up %s from %s " % (summary.name, sizeof_fmt(total), sizeof_fmt(ds_provisioned))
    print ""


def spinning_cursor():
    while True:
        for cursor in '|/-\\':
            yield cursor


def find_files(dsbrowser, dsname, datacenter, fulldsname):
    """
    function to search for VMX files on any datastore that is passed to it
    """
    
    search = vim.HostDatastoreBrowserSearchSpec()
    search.matchPattern = "*.*"
    search_ds = dsbrowser.SearchDatastoreSubFolders_Task(dsname, search)
    
    spinner = spinning_cursor()

    if "error" in search_ds.info.state:
        print search_ds.info.error.msg
        return
    while search_ds.info.state != "success":
        if "error" in search_ds.info.state:
            print search_ds.info.error.msg
            return
        if args.verbose:
            print "Checking %s : '%s' " % (dsname, search_ds.info.state),
            sys.stdout.write(spinner.next())
            sys.stdout.flush()
            time.sleep(0.1)
            sys.stdout.write('\r')
        pass
    
    for rs in search_ds.info.result:
        for f in rs.file:
            try:
                file_info.append(rs.folderPath+f.path)
                if args.veryverbose:
                    print "Found %s%s" % (rs.folderPath,f.path)
            except Exception, e:
                print "Caught exception : " + str(e)
                return -1
    if args.verbose:
        print "\r%s: collected %s files                                     " % (dsname,len(file_info))

def main():

    if args.verbose:
        sys.stdout.write("Connect to VMWare ... ")
        sys.stdout.flush()
        
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    if args.disable_ssl_verification:
        context.verify_mode = ssl.CERT_NONE
    
    
    si = SmartConnect(
        host=args.host,
        user=args.user,
        pwd=args.password,
        port=args.port, sslContext=context)
    # disconnect vc
    atexit.register(Disconnect, si)
    if args.verbose:
        print "Connected!"
    content = si.RetrieveContent()

    datacenter = content.rootFolder.childEntity[0]
    datastores = datacenter.datastore
    vmfolder = datacenter.vmFolder
    vmlist = vmfolder.childEntity

    dc_to_check = ""
    if args.name:
        dc_to_check = args.name

    for ds in datastores:
        if args.veryverbose:
            print "Look at %s " % ds.summary.name
        
        if dc_to_check in ds.summary.name:
            if args.verbose:
                print "Check %s " % ds.summary.name
            find_files(ds.browser, "[%s]" % ds.summary.name, datacenter.name, ds.summary.name)
            print_datastore_info(ds)
        else:
            if args.verbose:
                print "Skip %s\r" % ds.summary.name,

# start
if __name__ == "__main__":
    main()
