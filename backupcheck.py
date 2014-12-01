#!/usr/bin/env python3
# vim:expandtab ts=4 sw=4

"""Compare lists, print out differences
"""
# Changelog:
# 20141113: New Networker-List, compare with CMDB (i-doit)
# 20120604: Filestatus added
# 20120521: Created.

from snippets.send_mail import send_mail
from snippets.get_file_handle import get_file_handle
import socket
import sys
import os
import stat
import time

import requests
import json

import config

#url = "http://fqdn/i-doit/src/jsonrpc.php"


def exit_program(returncode = 0, msg = "", email=None):
    if email != None:
        hostname = socket.gethostname()
        send_mail(sender=config.sender, recipients=email, subject=config.subject, body=msg)
    print(msg)
    sys.exit(returncode)

def append_it_not_in_list(mylist,myelement):
    if myelement not in mylist:
        return mylist.append(myelement.rstrip())
    else:
        return mylist

def pull_file_in_list(filename):
    """Read textfile, return as a list and provide timestamp
    """
    path = "backupcheck/lists"
    tmp_file = get_file_handle(filename=filename, path=path)
    tmp_list = []
    for line in tmp_file:
        if len(line)>2:
            hostname = line.strip().rsplit(".")[0].lower()
            append_it_not_in_list(tmp_list,hostname)
    filestat = os.fstat(tmp_file.fileno())  
    mtime = filestat[stat.ST_MTIME]
    mtime_string = time.ctime(mtime)
    filestatus = filename + ", last modified " + mtime_string + "\n\n"
    tmp_list.sort()
    return tmp_list, filestatus


def api_call(method,params):
    headers = {'content-type': 'application/json'}
    params['apikey'] = config.apikey
    payload = {
        "method": method,
        "params": params,
        "jsonrpc": "2.0",
        "id": 1,
    }

    result = requests.post(
        config.url, data=json.dumps(payload), proxies={'http':''}, headers=headers).json()

    if 'result' in result:
         return result['result']
    
    msg = "Error" + result['error'] + "\n" + "ID" + result['id']
    exit_program(result = 1, msg = msg)

def read_cmdb():
    method = "cmdb.reports.read"
    params = {'id':config.report_id}
    result = api_call(method, params)
    cmdb_list = []
    for host in result:
        append_it_not_in_list(cmdb_list,str(host['Title'].lower()))
    cmdb_list.sort()
    return cmdb_list


def compare_lists(leftlist,rightlist):
    result = []
    for element in leftlist:
        if (not element in rightlist):
            result.append(element)
    return result

def main():
    """Compare Lists and 
    """

    cmdb_list = read_cmdb()
    backup_list, backup_status = pull_file_in_list(filename=config.serverlist)

    nobackup_list = compare_lists(cmdb_list,backup_list)
    nocmdb_list = compare_lists(backup_list,cmdb_list)

    msg = backup_status + "\n"
    msg = msg + "Servers in CMDB, but not in Networker(%d):\n\n" % len(nobackup_list)
    msg = msg + "\n".join(nobackup_list)
    msg = msg + "\n\n" + "-" * 20 + "\n\n"
    msg = msg + "Servers in Networker, but not in CMDB (%d):\n\n" % len(nocmdb_list)
    msg = msg + "\n".join(nocmdb_list)

    exit_program(msg=msg)
    
if __name__ == "__main__":
    main()
