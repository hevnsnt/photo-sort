import scandir
import os
import exifread
import argparse
import hashlib
import datetime
import shutil
import sys
import threading
import signal

class myThread (threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
    def run(self):
        if verbose: print "Starting " + self.name
        photosort(imagetypes, sourceDir, destinationDir)
        if verbose: print "Exiting " + self.name


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


def photosort(imagetypes, source, dest):
    '''This function uses scandir (python 2.x) to retrive
    a list of files, and then process the files to get the file date'''
    global notparsed
    global hashes
    global duplicate
    filebanner()
    for dirname, dirnames, filenames in scandir.walk(source):
        for filename in filenames:
            fileupper = filename.upper()
            if fileupper.endswith(imagetypes): # Is the file we found the type of file we care about?
                sha256, date, exif = getDeets(os.path.join(dirname, filename))
                if not sha256 in hashes.keys(): # hashes is a dictionary of seen hashes, if hash not in hashes, this is a new file
                    hashes[sha256] = {'date':date, 'exif':exif, 'firstFound':os.path.join(dirname, filename)} # So we add it to hashes dict
                    filebanner(sha256, date, exif, dirname, filename) 
                    move_file(date, dirname, dest, filename, sha256)
                else:
                    duplicate += 1
                    # If we make it here, we have detected a duplicate file
                    date1 = datetime.date(int(hashes[sha256]['date'][0]), int(hashes[sha256]['date'][1]), int(hashes[sha256]['date'][2])) 
                    date2 = datetime.date(int(date[0]), int(date[1]), int(date[2]))
                    # print('Already processed file: %s' % hashes[sha256]['firstFound'])
                    # print('With date: %s' % date1)
                    # print('Found file: %s' % os.path.join(dirname, filename))
                    # print('With date: %s' % date2)
                    if date1 <= date2:
                        # original file is older, I suggest keeping it how it is
                        if moveMode:os.remove(os.path.join(source, filename)) # Because we have the same file, no need to keep this one
                    else:
                        #original file is newer, I suggest we keep and process this file
                        if moveMode:move_file(date, dirname, dest, filename, sha256) 
                    # Check the existing file vs the processed file to see which is older
                    # If EXIF then based AND Date is different go ahead and process it.

            else:
                notparsed.append(os.path.join(dirname, filename))


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



def filebanner(sha256='NA', date=['NA','NA','NA','NA',], exif='NA', dirname='NA', filename='NA'):
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
    print(W + '# Directory: ' + G + dirname)
    print(W + '# File Name: ' + G + filename)
    print(W + '# SHA256 Hash: ' + G + sha256 + W)
    print('Number of thread workers: %s' % threading.activeCount())
    print '#' * 80
    print("")
    print('  [' + G + '+' + W + '] EXIF Files: %s' % len(exiffiles))
    print('  [' + G + '+' + W + '] OS Files: %s' % len(osfiles))
    print('  [' + G + '+' + W + '] Total Files Processed: %s' % filecount)
    print('  [' + R + '-' + W + '] Total Duplicate Files Found: %s' % duplicate)
    print('  [' + R + '-' + W + '] Total Files NOT Copied: %s' % len(notparsed))
    #print('')


def getDeets(file, block_size=2**20):
    global exiffiles
    global osfiles
    global filecount
    f = open(file, 'rb')
    tags = exifread.process_file(f)
    sha256 = hashFile(file)
    date, exif = getDate(tags, file)
    f.close()
    if not exif:
        osfiles.append(file)
    else:
        exiffiles.append(file)
    filecount += 1
    return sha256, date, exif


def hashFile(file):
    '''Will return the sha1 hash of a file, expects path to file'''
    f = open(file, 'rb')
    f = f.read()
    sha256 = hashlib.sha256(f).hexdigest()
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

def signal_handler(signal, frame):
        print('You pressed Ctrl+C!')
        sys.exit(0)



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
filecount = 0
exiffiles = []
osfiles = []
imagetypes = ('.GIF', '.JPG', '.PNG', '.JPEG')
notparsed = []
duplicate = 0
hashes = {}
exitFlag = 0
#-------------------Init global vars----------------------------------

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    threadLock = threading.Lock()
    threads = []

    # Create new threads
    thread1 = myThread(1, "Thread-1", 1)
    thread2 = myThread(2, "Thread-2", 2)

    # Start new Threads
    thread1.start()
    thread2.start()

    # Add threads to thread list
    threads.append(thread1)
    threads.append(thread2)

    # Wait for all threads to complete
    for t in threads:
        t.join()
    print "Exiting Main Thread"
    print('')
    displayNotparsed(notparsed)
    print('')
    print('Photosort has completed all operations')
    print('')