"""
    Author: Andres Andreu <andres [at] neurofuzzsecurity dot com>
    Company: neuroFuzz, LLC
    Original Date: 1/1/2012
    Last Modified: 7/19/2016
    Last Modified by: Muthukumar Thevar <muthukumar dot thevar [at] yahoo dot com>

    The transport class of scp-swarm.
    Basically this interfaces with scp.
    It either uses the system level scp or paramiko's wrapper around scp.
"""
from threading import Thread
import os

class XPort(Thread):
    """ Threaded Transport class """
    # Constructor
    def __init__(self, hostname='', username='', port='', password='', hostkeyname='', fname='', remotepath=''):
        Thread.__init__(self)
        self.username = username
        self.hostname = hostname
        self.port = port
        self.hostkeyname = hostkeyname
        self.password = password
        self.fname = fname
        self.remotepath = remotepath
    
    def run(self):
        '''
            try to utilize *nix system level
            utils first, fall back to 
            paramiko which is slower
        '''
        myscp = self.which('scp')
        if myscp:
            import pexpect
            if self.remotepath.startswith("/"):
                cln = ""
            else:
                cln = "~/"
            if self.hostkeyname:
                scpstmt = 'scp -C -P%d -i %s %s %s@%s:%s%s/' % (self.port,self.hostkeyname,self.fname,self.username,self.hostname,cln,self.remotepath)
                child = pexpect.spawn(scpstmt, timeout=None)
                child.setecho(False)
                print "Pushing file: %s" % self.fname
                child.expect(pexpect.EOF)
            else:
                scpstmt = 'scp -C -P%d %s %s@%s:%s%s/' % (self.port,self.fname,self.username,self.hostname,cln,self.remotepath)
                child = pexpect.spawn(scpstmt, timeout=None)
                child.setecho(False)
                exp = "%s@%s's password:" % (self.username,self.hostname)
                child.expect (exp)
                print "Pushing file: %s" % self.fname
                child.sendline (self.password)
                child.expect(pexpect.EOF)
        else:
            import paramiko
            t = paramiko.SSHClient()
            t.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                t.connect(hostname=self.hostname, port=self.port, username=self.username, password=self.password)
                sftp = t.open_sftp()
                print "Pushing file: %s" % self.fname
                sftp.put(self.fname, self.remotepath + '/' + self.fname)
                sftp.close()
                t.close()
            except Exception:
                pass
        
    def name_file(self):
        return self.fname

        """
        # copy this demo onto the server
        try:
            sftp.mkdir("demo_sftp_folder")
        except IOError:
            print '(assuming demo_sftp_folder/ already exists)'
        sftp.open('demo_sftp_folder/README', 'w').write('This was created by demo_sftp.py.\n')
        data = open('demo_sftp.py', 'r').read()
        sftp.open('demo_sftp_folder/demo_sftp.py', 'w').write(data)
        print 'created demo_sftp_folder/ on the server'
        
        # copy the README back here
        data = sftp.open('demo_sftp_folder/README', 'r').read()
        open('README_demo_sftp', 'w').write(data)
        print 'copied README back here'
        
        # BETTER: use the get() and put() methods
        sftp.put('demo_sftp.py', 'demo_sftp_folder/demo_sftp.py')
        sftp.get('demo_sftp_folder/README', 'README_demo_sftp')
        """

    def which(self,program):
        def is_exe(fpath):
            return os.path.exists(fpath) and os.access(fpath, os.X_OK)
    
        def ext_candidates(fpath):
            yield fpath
            for ext in os.environ.get("PATHEXT", "").split(os.pathsep):
                yield fpath + ext
    
        fpath, fname = os.path.split(program)
        if fpath:
            if is_exe(program):
                return program
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                exe_file = os.path.join(path, program)
                for candidate in ext_candidates(exe_file):
                    if is_exe(candidate):
                        return candidate
    
        return None  
        
# EOC