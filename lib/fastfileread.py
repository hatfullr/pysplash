import numpy as np
import os.path
from time import time
from multiprocessing import Pool
import warnings
import itertools
import sys
import mmap

def _fromstring(buff,sep=' ',ID=None):
    to_return = np.fromstring(buff,sep=sep)
    if ID is None: return to_return
    else: return to_return, ID
def _frombuffer(buff,chunk=None,shape=None,dtype=None,offset=0,strides=None):
    to_return = np.ndarray(shape=shape,dtype=dtype,buffer=buff,offset=offset,strides=strides)
    if chunk is None: return to_return
    else: return to_return, chunk

class FastFileRead(object):
    """
    Roger Hatfull 2021
    University of Alberta
    
    A class for reading data from text and binary files quickly. It
    can also handle binary files which contain text in their headers
    and/or footers.
    
    All input files must have regular columns of data. If a binary 
    file is provided, you must provide a corresponding numpy format 
    string for reading that file. See the NumPy docs for more info:
    https://numpy.org/doc/stable/reference/arrays.dtypes.html
    
    Only data types of float and int are supported for text files.

    Only files with regularly spaced columns are supported.

    If a binary file contains mixed types, the result will be a NumPy
    array that also has mixed types. This can result in 'TypeError:
    unhashable type' when trying to take a slice of data.

    Data can be accessed from a FastFileRead object using either keys
    like a dictionary if arguments are supplied to the keyword 'key',
    or by using indices or slices as with a list.
    
    If return_type is dict or np.ndarray, then the returned data can
    be accessed using keys with values that are set by the very last
    line in the header section that matches the number of columns in
    the first line of data. If keyword 'header' is 0, then the
    columns can be accessed using keywords 'col0', 'col1', etc. up to
    the total number of columns in the file.
    
             Name         Type                            Description
    -------------   ----------   ------------------------------------
         filename          str   The file or list of files to be read
                     list-like
    
           header          int   The number of lines to skip at the
                     list-like   top of each file. If the file is in
                                 binary format, this speicifes the
                                 number of bits to skip at the
                                 beginning of the file if the header
                                 lines are detected to be binary.
    
           footer          int   The number of lines to skip at the
                     list-like   bottom of each file. If the file is
                                 in binary format, this speicifes the
                                 number of bits to skip at the end
                                 of the file if the footer lines are
                                 detected to be binary.

         max_rows          int   The maximum number of rows to read
                          None   from each data file after skipping
                                 'header' number of rows. If set to
                                 'None' (default) all rows will be
                                 read.
    
    binary_format         None   The format to use when reading
                     list-like   binary files in 'filenames'. If
                           str   None, the file is assumed to be a
                                 text file.
    
       binary_EOL          str   The End Of Line format string used
                     list-like   in the input binary files.
    
           offset          int   Number of bytes to use as offset
                     list-like   when reading binary files.
    
        delimeter          str   Specify the delimeter that separates
                     list-like   the data columns. Default value None
                                 splits by whitespace.
    
    hdr_delimeter         None   Specify the delimeter that separates
                           str   the header columns. Defaults to
                     list-like   value of 'delimeter' if None.
    
      return_type         dict   Choose for the data to be returned
                    np.ndarray   as a list, NumPy array, or a
                          list   dictionary. Some types may be faster
                                 than others. If you choose 'list',
                                 then no headers will be returned.
                                 For np.ndarray and dict, the data
                                 can be accessed using keys
                                 corresponding to the labels found in
                                 the line of the header closest to
                                 the top of the data that matches the
                                 number of columns in the data.
    
              key         None   The reference name or list of names
                           str   given to each of the files in
                          list   'filename'. A file in 'filenames'
                                 can be accessed either using one of
                                 these keys.

         parallel         bool   If True, attempt to read each file
                                 using multiple processes. Sometimes
                                 this will make things faster, but
                                 not always.

           nprocs         None   The number of processes to use when
                           int   'parallel' is True. Set as None to
                                 use the most processes possible.

          verbose         bool   If True, prints the file path for
                                 each file read and how many seconds
                                 it took to read the file.

    """
    
    def __init__(
            self,
            filename,
            header=0,
            footer=0,
            max_rows=None,
            binary_format=None,
            binary_EOL="f8",
            offset=0,
            delimeter=None,
            hdr_delimeter=None,
            return_type=np.ndarray,
            key=None,
            parallel=False,
            nprocs=None,
            verbose=False,
    ):
        if not isinstance(key,(type(None),str,list)): raise ValueError("Received type '"+type(key).__name__+"' for keyword 'key' but expected one of 'None', 'str', or 'list'")
        
        # If filename is a list, convert all the other arguments
        # and keywords to list objects if they are not already list
        # objects.
        if not self._islistlike(filename):
            filename = [filename]
        if not self._islistlike(header):
            header = [header]*len(filename)
        if not self._islistlike(footer):
            footer = [footer]*len(filename)
        if not self._islistlike(max_rows):
            max_rows = [max_rows]*len(filename)
        if not self._islistlike(binary_format):
            binary_format = [binary_format]*len(filename)
        if not self._islistlike(binary_EOL):
            binary_EOL = [binary_EOL]*len(filename)
        if not self._islistlike(offset):
            offset = [offset]*len(filename)
        if not self._islistlike(delimeter):
            delimeter = [delimeter]*len(filename)
        if not self._islistlike(hdr_delimeter):
            hdr_delimeter = [hdr_delimeter]*len(filename)
        if not self._islistlike(return_type):
            return_type = [return_type]*len(filename)

        self.key = key
        if self.key is not None:
            if not self._islistlike(self.key) and len(filename) > 1:
                raise ValueError("Length of keyword argument 'key' doesn't match length of argument 'filename'")
            elif not self._islistlike(self.key): self.key = [self.key]
        
        if self.key is not None and len(filename) != len(self.key):
            raise ValueError("Length of keyword argument 'key' doesn't match length of argument 'filename'")

        if not all(len(l) == len(filename) for l in [header,footer,binary_format,binary_EOL,offset,delimeter,hdr_delimeter,return_type]):
            raise ValueError("All arguments and keywords must have the same length as 'filenames'.")

        fileobjs = [None]*len(filename)
        for i in range(len(fileobjs)):
            if not os.path.isfile(filename[i]): # Check to make sure we can find all the files
                try: FileNotFoundError
                except NameError: FileNotFoundError = IOError
                raise FileNotFoundError("Failed to find file '"+str(filename[i])+"'")

            fileobjs[i] = {
                'path' : filename[i],
                'header' : header[i],
                'footer' : footer[i],
                'max_rows' : max_rows[i],
                'binary_format' : binary_format[i],
                'binary_EOL' : binary_EOL[i],
                'offset' : offset[i],
                'delimeter' : delimeter[i],
                'hdr_delimeter' : hdr_delimeter[i] if hdr_delimeter[i] is not None else delimeter[i],
                'return_type': return_type[i],
                'dtype' : None,
            }

            if binary_format[i] is not None:
                # Search the already-created file objects for the same binary format. If found,
                # copy the dtype to the most recently created file object.
                for fileobj in fileobjs[:i]:
                    if fileobj['binary_format'] == binary_format[i]:
                        fileobjs[i]['dtype'] = fileobj['dtype']
                        break
                else: # If none are found, create the dtype (default to col0, col1, ...)
                    fileobjs[i]['dtype'] = np.dtype([('col'+str(j),b) for j,b in enumerate(fileobjs[i]['binary_format'].split(','))])
        
        
        self.parallel = parallel
        self.nprocs = nprocs
        self.verbose = verbose
        self._setting_item = False

        self._EOL = '\n'.encode()

        if self.parallel:
            self.pool = Pool(self.nprocs)
            self.nprocs = self.pool._processes
            try: # Parallel
                self._read(fileobjs)
                self.pool.close()
                self.pool.join()
            except Exception as e: # Serial
                self.pool.close()
                self.pool.join()
                self.parallel = False
            
                # If for any reason running in parallel doesn't work, notify the user and then
                # run in serial instead
                def f(msg,warning,filename,lineno,*args,**kwargs):
                    return str(filename)+":"+str(lineno)+": "+str(warning.__name__)+": "+str(msg)+"\n"
                warnings.formatwarning = f
                warnings.warn("Parallel processing failed, reverting to serial. Suppress this warning (and all others) using warnings.filterwarnings('ignore'). Error messsage: "+str(e),RuntimeWarning)
                self._read(fileobjs)
        else:
            self._read(fileobjs)

    def __len__(self):
        return len(self._data)
            
    def __getitem__(self,arg):
        if isinstance(arg,(list,tuple,np.ndarray)) and len(arg) == 1: arg = arg[0]
        
        iterators = None
        if hasattr(arg,'__iter__'):
            iterators = [hasattr(a,'__iter__') or isinstance(a,slice) for a in arg]
        
        # If we have only 1 file stored in this object
        if isinstance(self._data, np.ndarray):
            if isinstance(arg,slice):
                if arg.step is not None and not isinstance(arg.step,int):
                    raise IndexError("Cannot slice with non-integer steps")
                start = arg.start
                stop = arg.stop
                if isinstance(start,str): start = self._data.dtype.names.index(start)
                if isinstance(stop,str): stop = self._data.dtype.names.index(stop)
                return self._data[slice(start,stop,arg.step)]
            
            # Simple cases
            if isinstance(arg,int): return self._data[arg]
            if isinstance(arg,str):
                if arg in self._data.dtype.names: return self._data[arg]
                elif arg in self.key: return self._data
                else: raise IndexError("Unrecognized index '"+arg+"'. Valid indices are '"+str(self._data.dtype.names)+"'")
            if isinstance(arg,slice): return self._data[arg]
            
            if hasattr(arg, '__iter__'):
                if sum(iterators) == 0: return self._data[list(arg)]
                if sum(iterators) > 2:
                    raise IndexError("Cannot have > 2 iterable objects when indexing a FastFileRead object")
                if len(arg) != 2:
                    raise IndexError("When indexing using lists, tuples, np.ndarrays, or slices, you must use a maximum of only 2 elements, such as '[:,1]', '[3:9,2:7]', '[(3,4,7):[0,5,2]]'")
                
                # Get the rows
                if iterators[0]:
                    if isinstance(arg[0],slice): rows = self._data[arg[0]]
                    else: rows = np.array([self._data[row] for row in arg[0]])
                else: rows = self._data[arg[0]]
                
                if iterators[1]:
                    # User is doing a simple column retrieval
                    if not isinstance(arg[1],slice):
                        return np.column_stack(tuple([rows[name] for name in [self._data.dtype.names[d] for d in arg[1]]]))
                    return np.column_stack(tuple([rows[name] for name in self._data.dtype.names[arg[1]]]))
                # User is doing a simple row retrieval
                return np.array([row[arg[1]] for row in rows])
            raise IndexError("Failed to find index")

        # If the we have more than 1 file stored in this object
        if isinstance(arg,str): return self._data[self.key.index(arg)]
        
        # Simple cases
        if isinstance(arg,int):
            return np.array(self._data[arg])
        if isinstance(arg,str):
            return np.array(self._data[self.key.index(arg)])
        if isinstance(arg,slice):
            start = arg.start
            stop = arg.stop
            if isinstance(start,str): start = self.key.index(start)
            if isinstance(stop,str): stop = self.key.index(stop)
            return self._data[slice(start,stop,arg.step)]
        
        if hasattr(arg,'__iter__'):
            if len(arg) == 1 and sum(iterators) == 0:
                return np.array([self._data[a] for a in arg])
            if sum(iterators) > 2:
                raise IndexError("Cannot have > 2 iterable objects when indexing a FastFileRead object")
            if len(arg) != 2:
                raise IndexError("When indexing using lists, tuples, np.ndarrays, or slices, you must use a maximum of only 2 elements, such as '[:,1]', '[3:9,2:7]', '[(3,4,7):[0,5,2]]'")
            
            # Get the files
            if iterators[0]:
                if isinstance(arg[0],slice): files = self._data[arg[0]]
                else:
                    indices = []
                    for a in arg[0]:
                        if isinstance(a,int): indices.append(a)
                        elif isinstance(a,str): indices.append(self.key.index(a))
                        else: raise IndexError("Got a file index '"+str(a)+"' of type '"+type(a)+"' but expected types 'int' or 'str'")
                    files = np.array([self._data[index] for index in indices])
            else:
                if isinstance(arg[0],int): files = self._data[arg[0]]
                elif isinstance(arg[0],str): files =  self._data[self.key.index(arg[0])]
                else: raise IndexError("Got a file index '"+str(arg[0])+"' of type '"+type(arg[0])+"' but expected types 'int' or 'str'")

            # Get the columns in each file
            if iterators[1]:
                cols = []
                names = [f.dtype.names for f in files]
                if isinstance(arg[1],slice):
                    cols = names[0]
                    for name in names[1:]:
                        if name != cols:
                            raise IndexError("Cannot index multiple files which have different columns")
                    cols = cols[arg[1]]
                else:
                    # User is doing multiple column retrieval
                    for a in arg[1:]: # Make sure this column exists in every file we want to retrieve
                        if isinstance(a,int):
                            for i,(f,n) in enumerate(zip(files,names)):
                                try: f[n[a]]
                                except IndexError:
                                    raise IndexError("Integer column index '"+str(a)+"' out of range for file with key '"+str(self.key[i])+"' and dtype names of '"+str(f.dtype.names)+"'")
                            cols.append(names[i][a])
                        elif isinstance(a,str):
                            for i,f in enumerate(files):
                                try: f[a]
                                except ValueError as e:
                                    raise ValueError(str(e)+" in file with key '"+str(self.key[i])+"'")
                            cols.append(a)
                        else:
                            raise IndexError("Got column index '"+str(a)+"' of type '"+type(a)+"' but expected types 'int' or 'str'")
                    
                # All files contain the required columns
                return np.array([np.column_stack([f[col] for col in cols]) for f in files])
            else:
                # User is doing single column retrieval
                return np.array([f[arg[1]] for f in files])
            
        raise IndexError("Failed to find index")

    def __str__(self):
        if isinstance(self._data, np.ndarray):
            return "<FastFileRead(1 file)>\n"+self._data.dtype.names.__str__() + "\n" + self._data.__str__()
        else:
            return "<FastFileRead("+str(len(self._data))+" files, key="+str(self.key)+")>"

    def __setitem__(self,arg,val):
        for i in range(0,len(self[arg])):
            self[arg][i] = val[i]
        
    def _islistlike(self,obj):
        return isinstance(obj,(list,tuple,np.ndarray))

    def _stringtype(self,string):
        string = string.strip()
        if string in ['False','True']: return bool
        elif '.' in string:
            try:
                float(string)
                return float
            except ValueError as e:
                if 'could not convert string to float:' in str(e): return str
        else:
            try:
                int(string)
                return int
            except ValueError as e:
                if 'invalid literal for int() with base 10:' in str(e): return str

    def _read(self,fileobjs):
        self._data = [None]*len(fileobjs)
        
        for i,fileobj in enumerate(fileobjs):
            start = time()
            with open(fileobj['path'],'rb') as f:
                fileobj['buffer'] = mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)
                self._prepare_file(fileobj)
                if fileobj['binary_format'] is None: # Text file
                    self._data[i] = self._read_text(fileobj)
                else: # Binary file
                    self._data[i] = self._read_binary(fileobj)
                fileobj['buffer'].close()
                if self.verbose: print("%10f %s" % (time()-start,fileobj['path']))
        if len(self._data) == 1: self._data = self._data[0]

    def _prepare_file(self,fileobj):
        # Prepares an already-opened file

        if fileobj['binary_format'] is None: # Text file
            
            header_lines = [None]*fileobj['header']
            if fileobj['header'] > 0:
                for i in range(0,len(header_lines)):
                    header_lines[i] = fileobj['buffer'].readline()
                    
            fileobj['header'] = fileobj['buffer'].tell()
            line_length = fileobj['buffer'].find(self._EOL) - fileobj['header'] + 1 # +1 for EOL
            first_line = fileobj['buffer'].readline()
            
            if fileobj['delimeter'] is None: ncols = len(first_line.split())
            else: ncols = len(first_line.split(fileobj['delimeter']))

            fileobj['buffer'].seek(0,2)
            filesize = fileobj['buffer'].tell()
            fileobj['buffer'].seek(fileobj['header'])
            
            if fileobj['footer'] > 0:
                # Omit 'footer' text lines from the bottom of the file.
                last_line_end = fileobj['buffer'].rfind(self._EOL)
                for i in range(fileobj['footer']-1):
                    last_line_end = fileobj['buffer'].rfind(self._EOL,0,last_line_end)
                fileobj['footer'] = filesize-last_line_end
            else:
                fileobj['footer'] = filesize
            
            #fileobj['buffer'] = fileobj['buffer'][top:(nlines-fileobj['footer'])*line_length]
            
            # The key 'dtype' in this context is actually a Python list, not a NumPy dtype
            fileobj['dtype'] = ['col'+str(i) for i in range(ncols)]
            
            if fileobj['return_type'] in (dict,np.ndarray):
                # Search for the right header
                for line in header_lines[::-1]:
                    if fileobj['hdr_delimeter'] is None: ls = line.split()
                    else: ls = line.split(fileobj['hdr_delimeter'])
                    if len(ls) == ncols:
                        fileobj['dtype'] = ls
                        break
                    
        else: # Binary file
            ncols = fileobj['binary_format'].count(',') + 1
            # Try reading the header as text first
            if fileobj['header'] > 0:
                try: # Test the beginning of the file to see if it is text
                    if fileobj['hdr_delimeter'] is None:
                        line = str(fileobj['buffer'].readline().decode('ascii')).split()
                    else:
                        line = str(fileobj['buffer'].readline().decode('ascii')).split(fileobj['hdr_delimeter'])
                except UnicodeDecodeError: # It is binary, so skip the first N bits
                    fileobj['buffer'].seek(fileobj['header'])
                else: # First line is text; no exception was raised
                    # Expect all lines up to header to be text
                    if fileobj['return_type'] in (dict,np.ndarray) and len(line) == ncols: fileobj['dtype'].names = line
                    
                    for _ in range(1,fileobj['header']):
                        try:
                            if fileobj['hdr_delimeter'] is None:
                                line = str(fileobj['buffer'].readline().decode('ascii')).split()
                            else:
                                line = str(fileobj['buffer'].readline().decode('ascii')).split(fileobj['hdr_delimeter'])
                        except UnicodeDecodeError: # Binary, but we expected text!
                            raise ValueError("Found a text header when a binary format was specified and keyword 'header' > number of lines in the file's actual header, for file '"+str(fileobj['path'])+"'")
                        else: # Text
                            if fileobj['return_type'] in (dict,np.ndarray) and len(line) == ncols: fileobj['dtype'].names = line

            # Check if the footer is binary or text
            if fileobj['footer'] > 0:
                # Check the very first part of the footer
                fileobj['buffer'].seek(-16,2)
                try:
                    fileobj['buffer'].read(16).decode('ascii')
                except UnicodeDecodeError: # Found binary
                    fileobj['buffer'].seek(fileobj['header'])
                    # Keep the footer the same, as we expect it is in number of bytes to skip
                    pass
                    #raise ValueError("Found a text footer when a binary format was specified and the keyword 'footer' > number of lines in the file's actual footer, for file '"+str(fileobj['path'])+"'")
                else: # Found text
                    # This means the user wants to omit 'footer' text lines from the bottom of the file.
                    fileobj['buffer'].seek(0,2)
                    filesize = fileobj['buffer'].tell()
                    fileobj['buffer'].seek(fileobj['header'])
                    last_line_end = fileobj['buffer'].rfind(self._EOL)
                    for i in range(fileobj['footer']-1):
                        last_line_end = fileobj['buffer'].rfind(self._EOL,0,last_line_end)
                    fileobj['footer'] = filesize-last_line_end
    
    #@profile
    def _read_binary(self,fileobj):
        # Reads an already-opened binary file object
        
        ncols = fileobj['binary_format'].count(',') + 1
        lencols = sum(fileobj['binary_format'].count(str(num))*num for num in [1,2,4,6,8])
        strides = lencols + sum(fileobj['binary_EOL'].count(str(num))*num for num in [1,2,4,6,8])
        
        top = fileobj['buffer'].tell()
        fileobj['buffer'].seek(-fileobj['footer'],2)
        bottom = fileobj['buffer'].tell()
        nlines = int((bottom-top)/strides)
        if fileobj['max_rows'] is not None: nlines = min(nlines,fileobj['max_rows'])
        fileobj['buffer'].seek(top)
        
        if self.parallel:
            chunks = np.array_split((np.arange(nlines)),self.nprocs)
            
            procs = [None]*self.nprocs
            for i,chunk in enumerate(chunks):
                start = chunk[0]*strides
                stop = (chunk[-1]+1)*strides
                
                procs[i] = self.pool.apply_async(
                    _frombuffer,
                    args=(
                        fileobj['buffer'].read(stop-start), # buffer
                        chunk, # chunk
                        (chunk[-1] - chunk[0])+1, # shape
                        fileobj['dtype'], # dtype
                        fileobj['offset'], # Don't ask, it just works...
                        strides, # strides
                    ),
                )
            d = np.empty(nlines,dtype=fileobj['dtype'])
            for i in range(self.nprocs):
                result,chunk = procs[i].get()
                d[chunk] = result
        else:
            d = _frombuffer(
                fileobj['buffer'].read(bottom-top),
                shape=nlines,
                dtype=fileobj['dtype'],
                strides=strides,
                offset=fileobj['offset'],
            )
        
        if fileobj['return_type'] is np.ndarray: return d
        elif fileobj['return_type'] is dict: return {name:d[name] for name in d.dtype.names}
        elif fileobj['return_type'] is list: return list(d)
        else:
            raise Exception("return_type for '"+fileobj['path']+"' is not one of 'dict', 'np.ndarray', or 'list'.")

    #@profile
    def _read_text(self,fileobj):
        # Reads an already-opened text file object

        fileobj['buffer'].seek(fileobj['header'])
        line_length = fileobj['buffer'].find(self._EOL) + 1 - fileobj['header']# +1 for EOL
        ncols = len(fileobj['dtype'])
        filesize = fileobj['footer']-fileobj['header']
        nlines = int(filesize/line_length)
        if fileobj['max_rows'] is not None:
            nlines = min(nlines,fileobj['max_rows'])
            filesize = nlines*line_length
        
        if self.parallel:
            d = [None]*self.nprocs
            
            chunks = np.array_split(np.arange(nlines),self.nprocs)
            
            procs = [None]*self.nprocs
            for i in range(self.nprocs):
                bchunk = fileobj['buffer'].read(len(chunks[i])*line_length)#[chunks[i][0]*line_length:(chunks[i][-1]+1)*line_length]
                if fileobj['delimeter'] is None:
                    procs[i] = self.pool.apply_async(_fromstring,args=(bchunk,' ',i))
                else:
                    procs[i] = self.pool.apply_async(_fromstring,args=(bchunk,fileobj['delimeter'],i))

            for i in range(self.nprocs):
                result,ID = procs[i].get()
                d[ID] = result

            d = np.concatenate(d).reshape((nlines,ncols))
        else:
            if fileobj['delimeter'] is None: d = _fromstring(fileobj['buffer'].read(filesize))
            else: d = _fromstring(fileobj['buffer'].read(filesize),sep=fileobj['delimeter'])
            d = d.reshape((nlines,ncols))

        if fileobj['return_type'] is np.ndarray: return d
        elif fileobj['return_type'] is dict: return {name:d[name] for name in d.dtype.names}
        elif fileobj['return_type'] is list: return list(d)
        else:
            raise Exception("return_type for '"+fileobj['path']+"' is not one of 'dict', 'np.ndarray', or 'list'.")

def read_starsmasher(filenames,return_headers=False,key=None,**kwargs):
    if key is None: key = filenames
    if isinstance(key,str): key = [key]
    else: key = list(key)
    header_names = [
        'ntot',
        'nnopt',
        'hco',
        'hfloor',
        'sep0',
        'tf',
        'dtout',
        'nout',
        'nit',
        't',
        'nav',
        'alpha',
        'beta',
        'tjumpahead',
        'ngr',
        'nrelax',
        'trelax',
        'dt',
        'omega2',
        'ncooling',
        'erad',
        'ndisplace',
        'displacex',
        'displacey',
        'displacez',
    ]
    data_names = [
        'x',
        'y',
        'z',
        'am',
        'hp',
        'rho',
        'vx',
        'vy',
        'vz',
        'vxdot',
        'vydot',
        'vzdot',
        'u',
        'udot',
        'grpot',
        'meanmolecular',
        'cc',
        'divv',
        # These are present only when ncooling!=0
        'ueq',
        'tthermal',
    ]
    header_format = ['i4']*2 + ['f8']*5 + ['i4']*2 + ['f8','i4'] + ['f8']*3 + ['i4']*2 + ['f8']*3 + ['i4','f8','i4'] + ['f8']*3
    header_format = '<' + ",".join(header_format)
    data_format = '<'+'f8,'*16 + 'f4,f8'

    header_size = sum([header_format.count(str(num))*num for num in [1,2,4,6,8]]) + 8 # +8 for newline

    # We need to read all the headers first no matter what, so that we know if
    # ncooling=0 or not for each file.
    if not isinstance(filenames,(list,tuple,np.ndarray)): filenames = [filenames]
    
    filesizes = np.zeros(len(filenames),dtype=int)
    for i,filename in enumerate(filenames):
        with open(filename,'rb') as f:
            f.seek(0,2)
            filesizes[i] = f.tell()

    headers = FastFileRead(
        filenames,
        footer=filesizes-header_size,
        binary_format=header_format,
        offset=4,
        key=key,
        **kwargs
    )

    

    data_formats = [None]*len(key)
    data_column_names = [None]*len(key)
    for i,k in enumerate(key):
        headers[k].dtype.names = header_names
        if headers[k]['ncooling'] == 0:
            data_formats[i] = data_format
            data_column_names[i] = data_names[:-2]
        elif headers[k]['ncooling'] == 1:
            data_formats[i] = data_format + ',f8,f8'
            data_column_names[i] = data_names
        elif headers[k]['ncooling'] == 2:
            data_formats[i] = data_format + ',f8,f8,f8,f8,f8'
            data_column_names[i] = data_names + ['opacity','uraddot','temperature']
            
    data = FastFileRead(
        filenames,
        header=header_size,
        binary_format=data_formats,
        offset=4,
        key=key,
        **kwargs
    )

    for i in range(len(filenames)):
        data[i].dtype.names = data_column_names[i]
    
    if return_headers: return data, headers
    else: return data

    

        
"""
# For testing:
from glob import glob
text_files = sorted(glob("text_files/*.track"))
binary_files = sorted(glob("binary_files/*.track"))
headerless_binary_files = sorted(glob("headerless_binary_files/*.track"))
mix_files = sorted(glob("mix_files/*.track"))

parallel = False

print("Binary files")
ffr = FastFileRead(binary_files,header=1,binary_format='<'+19*'f8,'+'i4',offset=4,return_type=dict,footer=0,verbose=True,parallel=parallel)
#print(ffr[0])

print("Headerless binary files")
ffr = FastFileRead(headerless_binary_files,header=0,binary_format='<'+19*'f8,'+'i4',offset=4,return_type=dict,footer=0,verbose=parallel)

print("Mixed binary files with weird footers and headers")
ffr = FastFileRead(mix_files,header=1,binary_format='<'+19*'f8,'+'i4',offset=4,return_type=list,footer=2,verbose=True,parallel=parallel)
print("Text files")
ffr = FastFileRead(text_files,header=1,return_type=np.ndarray,parallel=parallel,verbose=True)
print(ffr[0])
"""
