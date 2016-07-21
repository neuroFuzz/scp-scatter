"""
    Author: Andres Andreu <andres [at] neurofuzzsecurity dot com>
    Company: neuroFuzz, LLC
    Original Date: 1/1/2012
    Last Modified: 1/13/2012

    The remote command class of scp-swarm.
    Basically this uses paramiko to run remote commands over SSH.
"""
try:
    import paramiko
except ImportError, e:
    # module doesn't exist, deal with it.
    pass

class RemoteCommander():
    """ RemoteCommander class """

    # Constructor
    def __init__(self, goObj=''):
        self.username = ''
        self.hostname = ''
        self.port = ''
        self.hostkey = ''
        self.password = ''
        self.t = ''
        self.remotepath = ''
        self.debug = ''
        self.goObj = goObj
        self.commands = {'md5':'md5sum ',
                         'cat':'cat ',
                         'rm':'yes|rm '
                        }
        
    def populate_info(self):
        self.username = self.goObj.getUserName()
        self.hostname = self.goObj.getHostName()
        self.port = self.goObj.getPort()
        self.hostkey = self.goObj.getHostKeyName()
        self.password = self.goObj.getPassword()
        self.remotepath = self.goObj.getRemotePath()
        self.debug = self.goObj.getDebug()
        
    def create_connection(self):
        self.t = paramiko.SSHClient()
        self.t.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if self.hostkey:
            #privkey = paramiko.RSAKey.from_private_key_file(self.hostkey)
            #self.t.connect(hostname=self.hostname, pkey=privkey, port=self.port, username=self.username, password=self.password)
            self.t.connect(hostname=self.hostname, key_filename=self.hostkey, port=self.port, username=self.username, password=self.password)
        else:
            self.t.connect(hostname=self.hostname, port=self.port, username=self.username, password=self.password)
        
    def construct_command(self, cmd='', stmt='', frelated=False, fname=''):
        if stmt:
            return self.commands[cmd] + stmt
        if frelated:
            return self.commands[cmd] + self.remotepath + "/" + fname
        
    def run_no_response(self, command=''):
        chan = self.t.get_transport().open_session()
        chan.exec_command(command)
        exit_status = chan.recv_exit_status()
        if self.debug:
            print "Remote Command Exit Status: %s" % exit_status
        
    def run_get_response(self, command=''):
        stdin, stdout, stderr = self.t.exec_command(command)
        '''
            this needs cleaning up, wrote it expecting
            a response like:
            
            447521efba1703445d050ddb24fe76b8  rand100.dat
        '''
        return stdout.read().split()[0]
    
    def clean_chunks(self, fl=[]):
        '''
        for f in fl:
            command = self.construct_command('rm', frelated=True, fname=f)
            self.t.exec_command(command)
        '''
        command = self.construct_command('rm', frelated=True, fname="*" + self.goObj.getPostFix() + "*")
        self.t.exec_command(command)
    
    def close(self):
        self.t.close()
# EOC