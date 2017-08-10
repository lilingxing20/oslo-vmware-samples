#!/usr/bin/env python
# coding=utf-8

'''
Author      : lixx (https://github.com/lilingxing20)
Created Time: Sat 24 Jun 2017 12:24:24 PM CST
Description :
'''

from oslo_vmware import api
from oslo_vmware import rw_handles
from oslo_vmware import vim_util as vutil
from oslo_vmware import vim

from nova.virt.vmwareapi import images
from nova.virt.vmwareapi import vm_util
from nova.virt.vmwareapi import error_util

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def export_stream_optimized_vmdk(session, vm_name, vmdk_path=None):
    """
    """
    vm_ref = vm_util._get_vm_ref_from_name(session, vm_name)

    def _get_vm_and_vmdk_attribs():
        # Get the vmdk info that the VM is pointing to
        vmdk = vm_util.get_vmdk_info(session, vm_ref)
        if not vmdk.path:
            print "No root disk defined. Unable to snapshot."
            raise error_util.NoRootDiskDefined()

        lst_properties = ["datastore", "summary.config.guestId"]
        props = session._call_method(vutil,
                                     "get_object_properties_dict",
                                     vm_ref,
                                     lst_properties)
        os_type = props['summary.config.guestId']
        datastores = props['datastore']
        return (vmdk, datastores, os_type)

    vmdk, datastores, os_type = _get_vm_and_vmdk_attribs()
    file_size = vmdk.capacity_in_bytes

    read_handle = rw_handles.VmdkReadHandle(session,
                                            session._host,
                                            session._port,
                                            vm_ref,
                                            None,
                                            file_size)
    if not vmdk_path:
        vmdk_path = "%s.vmdk" % vm_name
    write_handle = open(vmdk_path, 'w')
    images.start_transfer(None, read_handle, file_size,
                          write_file_handle=write_handle)


class VMwareAPISession(api.VMwareAPISession):
    """Sets up a session with the VC/ESX host and handles all
    the calls made to the host.
    """
    def __init__(self, host_ip='127.0.0.1',
                 username='administrator@vsphere.local',
                 password='!QAZxsw2',
                 retry_count=1,
                 task_poll_interval=0.1,
                 host_port=443,
                 scheme="https",
                 insecure=True):
        super(VMwareAPISession, self).__init__(
                host=host_ip,
                port=host_port,
                server_username=username,
                server_password=password,
                api_retry_count=retry_count,
                task_poll_interval=task_poll_interval,
                scheme=scheme,
                insecure=insecure)

    def _is_vim_object(self, module):
        """Check if the module is a VIM Object instance."""
        return isinstance(module, vim.Vim)

    def _call_method(self, module, method, *args, **kwargs):
        """Calls a method within the module specified with
        args provided.
        """
        if not self._is_vim_object(module):
            return self.invoke_api(module, method, self.vim, *args, **kwargs)
        else:
            return self.invoke_api(module, method, *args, **kwargs)

    def _wait_for_task(self, task_ref):
        """Return a Deferred that will give the result of the given task.
        The task is polled until it completes.
        """
        return self.wait_for_task(task_ref)


if __name__ == '__main__':
    # Get a handle to a vSphere API session
    session = VMwareAPISession(host_ip='172.30.241.15',
                               username='administrator@cbank.com',
                               password='!QAZxsw2',
                               retry_count=1,
                               task_poll_interval=0.1)
    vm_name = 'tt1'
    vmdk_path = 'tt1.vmdk'
    print "Began to export the virtual machine (%s) disk for stramOprimized format images ..." % vm_name
    export_stream_optimized_vmdk(session, vm_name, vmdk_path)
    print "Export the complate."

# vim: tabstop=4 shiftwidth=4 softtabstop=4
