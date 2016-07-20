"""
    Author: Andres Andreu <andres [at] neurofuzzsecurity dot com>
    Company: neuroFuzz, LLC
    Original Date: 1/1/2012
    Last Modified: 1/13/2012

    The file splitter class of scp-swarm.
    Basically this interfaces with split
    if it exists on the run time system.
    It either uses the system level split
    or handles the file splitting function
    itself.
"""
import os
import hashlib
import sys

class FileSplitterException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)
# EOC

class FileSplitter:
    """ File splitter class """

    # Constructor
    def __init__(self, filename='', numchunks='', remotepath='', postfix='', debug=False):
        # cache filename
        self.__filename = filename
        # remote path
        self.__remotepath = remotepath
        # number of equal sized chunks
        self.__numchunks = numchunks
        # Size of each chunk
        self.__chunksize = 0
        # postfix string for the chunk filename
        self.__postfix = postfix
        # Action = split
        self.__action = 0
        """
            cat statement
            this will be used later on the remote endpoint to
            reconstruct the end result file
        """
        self.__cat = ''
        # file list
        self.__flist = []
        self.__logfile = ''
        self.__logfhandle = ''
        # hash
        if self.__filename:
            self.__filehash = self.md5(fileName=self.__filename)
            self.createLog()
        else:
            sys.exit("Error: filename not given")
        self.__debug = debug
        self.__tmp = None
        self.__tmpout = None


    def do_work(self):
        if self.__action==0:
            self.split()
        elif self.__action==1:
            self.combine()
        else:
            return None
        
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
        
    def split(self):
        """ Split the file and save chunks to separate files """
        
        spl = self.which('split')
        if spl:
            self.__tmp = "/tmp"
            self.__tmpout = "/tmp/output"
            if not os.path.exists(self.__tmpout):
                os.makedirs(self.__tmpout)
            #os.chdir("/tmp")
            '''
                assume split prog overwrites existing files if
                there is a conflict in file names
            '''
            #thecommand = "%s -a 3 -b 500k %s %s/%s" % (spl, self.__filename, self.__tmpout, self.__filename + self.__postfix)
            thecommand = "%s -a 3 -b 10m %s %s/%s" % (spl, self.__filename, self.__tmpout, self.__filename + self.__postfix)
            os.system(thecommand)
            dirList=os.listdir(self.__tmpout)
            #self.constructCat(dirList)
            for chunkfilename in dirList:
                #print chunkfilename 
                #self.__cat += self.__remotepath + "/" + chunkfilename + " "
                #print self.__cat
                self.__flist.append(self.__tmpout + "/" + chunkfilename)
                #print self.__flist
                self.writeLog(chunkfilename, self.md5(fileName=self.__tmpout + "/" + chunkfilename))
            self.__numchunks = len([item for item in os.listdir(self.__tmpout) if os.path.isfile(self.__tmpout + "/" + item)])
        else:
            try:
                f = open(self.__filename, 'rb')
            except (OSError, IOError), e:
                raise FileSplitterException, str(e)
    
            bname = (os.path.split(self.__filename))[1]
            # Get the file size
            fsize = os.path.getsize(self.__filename)
            # dynamically calculate number of chunks
            strfsize = str(fsize)
            '''
                in MB's
                8 - teens
                9 - hundreds
                10 - gigabytes
            '''
            if len(strfsize) == 8:
                #self.__numchunks = fsize/100000
                self.__numchunks = fsize/50000
            elif len(strfsize) == 9:
                #self.__numchunks = fsize/1000000
                self.__numchunks = fsize/500000
            elif len(strfsize) == 10:
                #self.__numchunks = fsize/10000000
                self.__numchunks = fsize/5000000
            #print '\nSplitting file %s into %d chunks' % (self.__filename, self.__numchunks)
            # Get size of each chunk
            self.__chunksize = int(float(fsize)/float(self.__numchunks))
    
            chunksz = self.__chunksize
            total_bytes = 0
    
            for x in range(self.__numchunks):
                #chunkfilename = bname + '-' + str(x+1) + self.__postfix
                chunkfilename = bname + ('-%03d' % (x+1)) + self.__postfix
                # kill residual file if it exists
                if os.path.exists(chunkfilename):
                    os.remove(chunkfilename)
                """
                    if reading the last section, calculate correct
                    chunk size.
                """
                if x == self.__numchunks - 1:
                    chunksz = fsize - total_bytes
    
                try:
                    if self.__debug:
                        print 'Writing file chunk: %s' % chunkfilename
                    data = f.read(chunksz)
                    total_bytes += len(data)
                    chunkf = file(chunkfilename, 'wb')
                    chunkf.write(data)
                    chunkf.close()
                    #self.__cat += self.__remotepath + "/" + chunkfilename + " "
                    self.__flist.append(chunkfilename)
                    self.writeLog(chunkfilename, self.md5(fileName=chunkfilename))
                except (OSError, IOError), e:
                    print e
                    continue
                except EOFError, e:
                    print e
                    break

        print '\nSplit complete on file: %s into %d chunks\n' % (self.__filename, self.__numchunks)
        self.__logfhandle.close()
        #self.__cat += "> " + self.__remotepath + "/" + self.__filename
        self.set_cat_statement()

    def set_cat_statement(self):
        if len(self.__flist) > 0:
            '''
                the order of the files in the cat statement is
                of the utmost importance, so the list/array
                must be sorted. The output of the split
                (whether system level or this class code) is
                hierarchical but the multi-threaded nature of
                the file xfer process puts stuff remotely out
                of order. This sort process below ensures that
                the cat statement will be valid, otherwise
                the hashes wont match and the remote file
                will not be correct (even though the size may
                be correct)
            '''
            sortout = sorted(self.__flist)
            for fl in sortout:
                if self.__tmpout:
                    #self.__cat += self.__remotepath + "/" + fl.split(self.__tmpout)[1] + " "
                    self.__cat += self.__remotepath + "/" + fl[len(self.__tmpout)+1:len(fl)] + " "
                else:
                    self.__cat += self.__remotepath + "/" + fl + " "
            self.__cat += "> " + self.__remotepath + "/" + self.__filename

    def sort_index(self, f1, f2):

        index1 = f1.rfind('-')
        index2 = f2.rfind('-')
        
        if index1 != -1 and index2 != -1:
            i1 = int(f1[index1:len(f1)])
            i2 = int(f2[index2:len(f2)])
            return i2 - i1
        
    
    def md5(self, fileName, excludeLine="", includeLine=""):
        """Compute md5 hash of the specified file"""
        m = hashlib.md5()
        try:
            fd = open(fileName,"rb")
        except IOError:
            print "Unable to open the file in readmode:", fileName
            return
        eachLine = fd.readline()
        while eachLine:
            if excludeLine and eachLine.startswith(excludeLine):
                continue
            m.update(eachLine)
            eachLine = fd.readline()
        m.update(includeLine)
        fd.close()
        
        return m.hexdigest()
    # EOF
    
    def createLog(self):
        fname = self.__filename + self.__postfix + ".log"
        self.__logfile = fname
        logf = file(fname, 'w')
        logf.write(self.__filename + ":" + self.__filehash + "\n")
        logf.close()
        self.__logfhandle = open(fname, "a")
        
    def writeLog(self, n, nhash):
        #fname = os.getcwd() + "/" + self.__logfile
        #fname = "./" + self.__logfile
        #text_file = open(fname, "w")
        #text_file.write(n + ":" + nhash + "\n")
        self.__logfhandle.write(n + ":" + nhash + "\n")
        #text_file.close()
    
    def get_cat_statement(self):
        return self.__cat
    
    def get_flist(self):
        return self.__flist
    
    def get_hash(self):
        return self.__filehash
    
    def get_filename(self):
        return self.__filename
    
    def getTmpOut(self):
        return self.__tmpout
    
    def clean_chunks(self):
        for f in self.__flist:
            os.remove(f)
        #os.system("yes|rm " + os.getcwd() + "/*" + self.__postfix)

# EOC