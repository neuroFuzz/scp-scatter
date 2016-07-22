"""
    Author: Andres Andreu <andres [at] neurofuzzsecurity dot com>
    Company: neuroFuzz, LLC
    Original Date: 1/1/2012
    Last Modified: 7/21/2016
    Last Modified by: Andres Andreu <andres [at] neurofuzzsecurity dot com>

    The main controller of scp-swarm.
    This is the run time controller of all the actions that scp-swarm triggers.
"""
from threading import Thread
from Queue import Queue
import multiprocessing
import time

from libs.GetOpts import GetOptions
from libs.FileSplitter import FileSplitter
from libs.Transport import XPort
from libs.RemoteCommander import RemoteCommander

USE_TOR = False
spacer = "    "
def printOut(s):
    print "%sXFer Finished: %s".lstrip() % (spacer,s)

# controller function
def mainRun():
    
    ################################################
    # options object
    goObj = GetOptions()
    # populate
    goObj.get_info()
    
    USE_TOR = goObj.getUseTor()
    if USE_TOR:
        from libs.nf_toolkit_requirements import get_required_paths
        exe_paths = get_required_paths()
        if exe_paths.has_key('error_message'):
            print "\n%s\n\n" % exe_paths['error_message']
            import sys
            sys.exit()
    ################################################
    '''
        create FileSplitter object and 
        do the actual splitting into
        local chunks
    '''
    fsp = FileSplitter(filename=goObj.getFileName(), 
                       numchunks=goObj.getNumberOfChunks(),
                       remotepath=goObj.getRemotePath(), 
                       debug=goObj.getDebug(),
                       postfix=goObj.getPostFix()
                       )
    fsp.do_work()
    # get hash of local file
    localmd5hash = fsp.get_hash()
    ################################################
    def put_files(files):
        ''' accepts the queue and the list of files '''
        def producer(q, files):
            '''
                for each file to be uploaded
                start a new XPort thread
            '''
            for fhandle in files:
                thread = XPort(hostname=goObj.getHostName(),username=goObj.getUserName(),
                               port=goObj.getPort(),password=goObj.getPassword(),
                               hostkeyname=goObj.getHostKeyName(),fname=fhandle,
                               remotepath=goObj.getRemotePath())
                thread.start()
                '''
                    add the thread to the queue. The second parameter, boolean True, 
                    tells the put() method to block until a slot is available
                '''
                q.put(thread, True)
     
        finished = []
        def consumer(q, total_files):
            while len(finished) < total_files:
                '''
                    reads items out of the queue, 
                    blocking until an item is available in the queue.
                '''
                thread = q.get(True)
                '''
                    join() causes the consumer to block until 
                    the thread completes its execution
                '''
                thread.join()
                # get name of file successfully transferred
                n = thread.name_file().strip()
                finished.append(n)
                #print "%sXFer Finished: %s" % (spacer,n)
                printOut(n)
     
        q = Queue(7)
        prod_thread = Thread(target=producer, args=(q, files))
        cons_thread = Thread(target=consumer, args=(q, len(files)))
        prod_thread.start()
        cons_thread.start()
        prod_thread.join()
        cons_thread.join()
    # EOF
    
    ################################################
    '''
        make sure destination path exists
    '''
    rc = RemoteCommander(goObj=goObj)
    rc.populate_info()
    rc.create_connection()
    cmd = rc.construct_command(cmd='mkdir', stmt=goObj.getRemotePath())
    print "\nEnsuring remote target path exists\n"
    print "Remote statement used:\n%s\n" % cmd
    rc.run_no_response(command=cmd)
    rc.close()
    ################################################
    
    '''
        fsp.get_flist() returns an array/list
        call the put_files func to kick off
        the threads that will securely 
        transfer the file chunks to their
        destination
    '''
    put_files(fsp.get_flist())
    
    
    ################################################
    '''
        remotely reconstruct file from the chunks
        already transferred
    '''
    rc = RemoteCommander(goObj=goObj)
    rc.populate_info()
    rc.create_connection()
    cmd = rc.construct_command(cmd='cat', stmt=fsp.get_cat_statement())
    print "\nRemotely reconstructing files\n"
    if goObj.getDebug():
        print "Remote statement used:\n%s\n" % cmd
    rc.run_no_response(command=cmd)
    rc.close()
    ################################################
    '''
        remotely get file hash
    '''
    rc = RemoteCommander(goObj=goObj)
    rc.populate_info()
    rc.create_connection()
    cmd = rc.construct_command(cmd='md5', frelated=True, fname=fsp.get_filename())
    remotemd5hash = rc.run_get_response(command=cmd)
    rc.close()
    ################################################
    # output and compare hashes
    print
    print "Local hash: %s" % localmd5hash
    print "Remote hash: %s" % remotemd5hash
    print "\nRemote and local files",
    if localmd5hash == remotemd5hash:
        print " MATCH"
    else:
        print " DO NOT MATCH - something has gone wrong"
    print
    ################################################    
    def cleanLocal():
        fsp.clean_chunks()
        
    def cleanRemote():
        rc = RemoteCommander(goObj=goObj)
        rc.populate_info()
        rc.create_connection()
        rc.clean_chunks(fl=fsp.get_flist())
        rc.close()
    ################################################
    '''
        if cleanup is enabled ...
        since one removal process is local and
        the other is remote then they could be
        run simultaneously. So lets daemonize
        each process as separate and speed things
        up that way
    '''
    if goObj.getCleanUp():
        
        # clean up local chunks
        print "Cleaning up local chunks"
        d = multiprocessing.Process(name='cleanLocal', target=cleanLocal)
        d.daemon = True
        '''
            remotely remove file chunks
            already processed
        '''
        print "Cleaning up remote chunks\n"
        n = multiprocessing.Process(name='cleanRemote', target=cleanRemote)
        n.daemon = True

        d.start()
        time.sleep(1)
        n.start()

        d.join()
        n.join()
# EOF

if __name__=="__main__":
    # run and measure run time    
    import timeit
    tt = timeit.Timer(setup='from __main__ import mainRun', stmt='mainRun()')
    theff = tt.timeit(number=1)/60
    print "Program run time: %f %s\n\n" % (theff,'minutes')