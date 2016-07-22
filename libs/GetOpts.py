"""
    Author: Andres Andreu <andres [at] neurofuzzsecurity dot com>
    Company: neuroFuzz, LLC
    Original Date: 1/1/2012
    Last Modified: 7/21/2016
    Last Modified by: Andres Andreu <andres [at] neurofuzzsecurity dot com>

    The variable setting class of scp-swarm.
    Basically this either grabs variables from the ones set here or it asks the
    user for answers to questions and sets variables that way.
"""
import os
import sys
import getpass
import paramiko

#################################################
# vars that can be changed
DEBUG = False
USE_TOR = False

hostname = 'hostname'
theport = 22
username = 'user'
passwd = 'xxx'
remotepath = '/data/testdata'
filename = ''
hostkey = "~/.ssh/thekey"
#################################################
numofchunks = 20
cleanup = True
postfix = '__fxfer'

class GetOptions:

    # Constructor
    def __init__(self):
        self.username = username
        self.hostname = hostname
        self.port = theport
        self.hostkey = hostkey
        self.hostkeyname = hostkey
        self.password = passwd
        self.filename = filename
        self.numofchunks = numofchunks
        self.remotepath = remotepath
        self.cleanup = cleanup
        self.postfix = postfix
        
        self.debug = DEBUG
        self.use_tor = USE_TOR
        
        
    def get_info(self):
        ################################################
        # get hostname
        if not hostname:
            self.hostname = raw_input('Hostname: ')
            if len(self.hostname) == 0:
                print '*** Hostname required.'
                sys.exit(1)
        else:
            self.hostname = hostname
        ################################################
        # get port number
        if not theport:
            port = raw_input('Port: ')
            if len(port) > 0:
                self.port = int(port)
        else:
            self.port = theport
        ################################################
        # get username
        if not username:
            if self.username == '':
                default_username = getpass.getuser()
                self.username = raw_input('Username [%s]: ' % default_username)
                if len(self.username) == 0:
                    self.username = default_username
        else:
            self.username = username
        ################################################
        # get password
        if not passwd:
            self.password = getpass.getpass('Password for %s@%s: ' % (self.username, self.hostname))
        else:
            self.password = passwd
        ################################################
        # get number of chunks
        if not numofchunks:
            nchunks = raw_input('Number of Chunks: ')
            if len(nchunks) > 0:
                self.numofchunks = int(nchunks)
        else:
            self.numofchunks = numofchunks
        ################################################
        # get file name
        if not filename:
            self.filename = raw_input('File: ')
            if len(self.filename) == 0:
                print '*** File required.'
                sys.exit(1)
        else:
            self.filename = filename
        ################################################
        # get host key, if we know one
        if self.hostkey:
            hostkeytype = None
            try:
                host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
            except IOError:
                try:
                    host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/ssh/known_hosts'))
                except IOError:
                    print '*** Unable to open host keys file'
                    host_keys = {}
            
            if host_keys.lookup(self.hostname):
                hostkeytype = host_keys[self.hostname].keys()[0]
                self.hostkey = host_keys[self.hostname][hostkeytype]
                if debug:
                    print 'Using host key at %s of type %s' % (self.hostkeyname,hostkeytype)
        ################################################
        
    def getUserName(self):
        return self.username
    
    def getHostName(self):
        return self.hostname
    
    def getPort(self):
        return self.port
    
    def getHostKey(self):
        return self.hostkey
    
    def getHostKeyName(self):
        return self.hostkeyname
    
    def getPassword(self):
        return self.password
        
    def getFileName(self):
        return self.filename
    
    def getNumberOfChunks(self):
        return self.numofchunks
    
    def getRemotePath(self):
        return self.remotepath
    
    def getDebug(self):
        return self.debug
    
    def getCleanUp(self):
        return self.cleanup
    
    def getPostFix(self):
        return self.postfix
    
    def getUseTor(self):
        return self.use_tor
# EOC
