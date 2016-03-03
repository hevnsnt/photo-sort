import os
import sys
import time
import shutil
import scandir
import hashlib
import exifread
import argparse
import datetime
from stat import S_ISREG
#import multiprocessing as mp
from multiprocessing import Process, Value, Lock, Pool


class Counter(object):
    def __init__(self, initval=0):
        self.val = Value('i', initval)
        self.lock = Lock()

    def increment(self):
        with self.lock:
            self.val.value += 1

    def value(self):
        with self.lock:
            return self.val.value


## Time Tests:
## Single Threaded: 2.11981105804 1.78328084946 1.87511110306 Total Files Processed: 295
## Multi Threaded: 1.65844511986 1.61673307419
## MP Time processing: 0.818398952484

#######################- Setting Console Colors -########################
# Console colors
W  = '\033[0m'  # white (normal)
R  = '\033[31m'  # red
G  = '\033[32m'  # green
O  = '\033[33m'  # orange
B  = '\033[34m'  # blue
P  = '\033[35m'  # purple
C  = '\033[36m'  # cyan
GR = '\033[37m'  # gray
T  = '\033[93m'  # tan


def photosort(processFile):
    '''This function uses scandir (python 2.x) to retrive
    a list of files, and then process the files to get the file date'''
    global destinationDir
    global notparsed
    global hashes
    global duplicate
    filebanner()
    sha256, date, exif = getDeets(processFile)

    if not sha256 in hashes.keys(): # hashes is a dictionary of seen hashes, if hash not in hashes, this is a new file
        hashes[sha256] = {'date':date, 'exif':exif, 'firstFound':processFile} # So we add it to hashes dict
        filebanner(sha256, date, exif, processFile) 
        move_file(date, os.path.dirname(processFile), destinationDir, processFile, sha256)
        counter.increment()
    else:
        duplicate.increment()
        # If we make it here, we have detected a duplicate file
        date1 = datetime.date(int(hashes[sha256]['date'][0]), int(hashes[sha256]['date'][1]), int(hashes[sha256]['date'][2])) 
        date2 = datetime.date(int(date[0]), int(date[1]), int(date[2]))
                    # print('Already processed file: %s' % hashes[sha256]['firstFound'])
                    # print('With date: %s' % date1)
                    # print('Found file: %s' % os.path.join(dirname, filename))
                    # print('With date: %s' % date2)
        if date1 <= date2:
        # original file is older, I suggest keeping it how it is
            if moveMode:os.remove(processFile) # Because we have the same file, no need to keep this one
        else:
            #original file is newer, I suggest we keep and process this file
            if moveMode:move_file(date, os.path.dirname(processFile), destinationDir, filename, sha256) 
             # Check the existing file vs the processed file to see which is older
            # If EXIF then based AND Date is different go ahead and process it.
        print('done photosort function')


def move_file(date, source, dest, filename, sha256):
    global duplicate # Needed for duplicate tracking
    global notparsed # Needed for notparsed tracking
    destination = os.path.join(dest, date[0], date[1], filename) # This creates the final destination directory\filename
    if verbose:print('\nProcessing: %s \nDestination: %s' % (os.path.join(source, filename), destination)),
    if not testMode:
        if os.path.exists(destination): # No need to check for duplicate if DIR doesnt even exist
            oldFileSHA256 = hashFile(destination) #hash existing file
            if oldFileSHA256 == sha256: # DUPLICATE CHECKING
                if verbose:print(G + ' [Duplicate File Found]' + W)
                if moveMode:os.remove(os.path.join(source, filename)) # Because we have the same file, no need to keep this one
                return
        if not os.path.exists(os.path.join(dest, date[0], date[1])): #If the destination dir doesnt exist
            try:
                if verbose:print('Making %s Directory' % os.path.join(dest, date[0], date[1]))
                os.makedirs(os.path.join(dest, date[0], date[1])) #Try to create it
            except Exception, e:
                print('')
                print (R + 'error: %s' % e + W)
                notparsed.append(os.path.join(source, filename))
                if e.errno == 13:
                    print('\nYou do not have write permission at %s' % dest),
                    print(' Exiting.\n')
                    sys.exit()
                return
        try:
            shutil.copy2(os.path.join(source, filename), destination) #copy2 retains all file attributes
            if verbose:print(G + '[DONE]' + W)
            if moveMode: # moveMode will remove the source file only after it has confirmed the copy is exactly the same hash
                # Need to check new file vs old file hash
                newFileSHA256 = hashFile(destination) #hash newly created file
                if newFileSHA256 == sha256:
                    print('Hash Match: removing %s' % os.path.join(source, filename))
                    #os.remove(os.path.join(source, filename)) # Because we have the same file, no need to keep this one
        except Exception, e:
            print (R + 'error: %s' % e + W)
            notparsed.append(os.path.join(source, filename))
            return



def filebanner(sha256='NA', date=['NA','NA','NA','NA',], exif='NA', filename='NA'):
    os.system('cls' if os.name == 'nt' else 'clear')
    print '#' * 80
    if testMode:
        print('#' + G + ' **TEST MODE** ' + W + 'No file operations')
    else:
        if moveMode:
            print('#' + R + ' **MOVE FILE MODE** ' + W)
        else:
            print('#' + B + ' **!COPY FILE MODE**  No Destructive Operations' + W)
    
    if exif:
        print(W + '# File details retreived from: ' + G + ' EXIF Data')
    else:
        print(W + '# File details retreived from: ' + G + ' Operating System')
    print(W + '# Year: ' + G + date[0] + W + ' | Month: ' + G + date[1] + W + ' | Day: ' + G + date[2])
    print(W + '# Directory: ' + G + os.path.dirname(filename))
    print(W + '# File Name: ' + G + filename)
    print(W + '# SHA256 Hash: ' + G + sha256 + W)
    print '#' * 80
    print("")
    #print('  [' + G + '+' + W + '] EXIF Files: %s' % len(exiffiles))
    #print('  [' + G + '+' + W + '] OS Files: %s' % len(osfiles))
    print('  [' + G + '+' + W + '] Total Files Processed: %s' % counter.value())
    print('  [' + R + '-' + W + '] Total Duplicate Files Found: %s' % duplicate.value())
    print('  [' + R + '-' + W + '] Total Files NOT Copied: %s' % len(notparsed))
    #print('')


def getDeets(file, block_size=2**20):
    global exiffiles
    global osfiles
    global filecount
    print file
    f = open(file, 'rb')
    tags = exifread.process_file(f)
    sha256 = hashFile(file)
    date, exif = getDate(tags, file)
    f.close()
    if not exif:
        osfiles.append(file)
    else:
        exiffiles.append(file)
    filecount.increment()
    return sha256, date, exif


def hashFile(file):
    '''Will return the sha1 hash of a file, expects path to file'''
    f = open(file, 'rb')
    f = f.read()
    sha256 = hashlib.sha256(f).hexdigest()
    #f.close()
    return sha256


def getDate(tags, f):
    '''Attempts to get Date information from EXIF data, if none found it will fall back to file information'''
    if 'EXIF DateTimeOriginal' in tags:
        date = str(tags['EXIF DateTimeOriginal']).replace(':', ' ').split()
        exif = True
    else:
        # File has no EXIF date information, so using last modified date
        # os.stat(filename).st_mtime
        date = str(datetime.datetime.fromtimestamp(os.stat(f).st_mtime)).replace(':', ' ').split()
        date[0] = date[0].replace('-', ' ').split()
        date = [date[0][0], date[0][1], date[0][2], date[1], date[2], date[3]]
        exif = False
    return date, exif

def displayNotparsed(notparsed):
    if len(notparsed) >= 20:
        print(R + '#' * (70))
        print(R + '#' + W + ' %s files were not processed, Would you like to see those items?' % len(notparsed) + R + '   #' + W)
        print(R + '#' * (70) + W)
        userInput = raw_input("Y/N? ").upper()
        if userInput == 'N':
            return
        elif userInput == 'Y':
            print('Items not moved:')
            for item in notparsed:
                print(' [+] %s' % item)
        else: 
            print('Invalid Selection:\n')
            displayNotparsed(notparsed)



#-------------------Get command line input----------------------------------
parser = argparse.ArgumentParser(description='Sorts photos based on their EXIF create date', formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-v', action='store_true', dest='verboseMode', help='Verbose mode will direct output to screen as well as logfile\n\n')
parser.add_argument('-t', action='store_true', dest='testMode', help='Test mode wont actually d0 anything\n\n')
parser.add_argument('-m', action='store_true', dest='moveMode', help='Copy, validate, and then remove source file\n\n')
parser.add_argument('-s', action='store', dest='sourceDir', required=True, help='Get the photo source directory\n\n')
parser.add_argument('-d', action='store', dest='destinationDir', required=True, help='Get the photo sort destination directory\n\n')
#-------------------End command line input----------------------------------

#-------------------Init global vars----------------------------------
results = parser.parse_args()
#logFilename = getloglocation(results.outFilename)
testMode = results.testMode
moveMode = results.moveMode
sourceDir = results.sourceDir
destinationDir = results.destinationDir
verbose = results.verboseMode
filecount = Counter(0)
exiffiles = []
osfiles = []
imagetypes = ('.GIF', '.JPG', '.PNG', '.JPEG')
notparsed = []
duplicate = Counter(0)
hashes = {}
counter = Counter(0)
size_limit = 1000
#-------------------Init global vars----------------------------------


#######################- Multi-Processing -########################
def walk_files(source):
    global imagetypes
    """yield up full pathname for each file in tree under source"""
    for dirpath, dirnames, filenames in scandir.walk(source):
        for filename in filenames:
            fileupper = filename.upper()
            if fileupper.endswith(imagetypes): # Is the file we found the type of file we care about?
                pathname = os.path.join(dirpath, filename)
                yield pathname

            else:
                notparsed.append(os.path.join(dirpath, filename))
            

def files_to_search(source):
    global filecount
    """yield up full pathname for only files we want to search"""
    for fname in walk_files(source):
        try:
            # if it is a regular file and big enough, we want to search it
            sr = os.stat(fname)
            if S_ISREG(sr.st_mode) and sr.st_size >= size_limit:
                yield fname
        except OSError:
            pass

def worker_search_fn(fname):
    photosort(fname)
    return
#######################- Multi-Processing -########################


if __name__ == "__main__": # execute only if run as a script
    start_time = time.time() # keep track of time
    Pool().map(worker_search_fn, files_to_search(sourceDir))

    
    #procs = [Process(target=worker_search_fn, args=(files_to_search(sourceDir),)) for i in range(10)]
    #for p in procs: p.start()
    #for p in procs: p.join()

    print('')
    displayNotparsed(notparsed)
    print('')
    print('Processed %s files' % filecount.value())
    print('Time processing: %s' % str(time.time() - start_time) )
    print('Photosort has completed all operations.' )
    print('')