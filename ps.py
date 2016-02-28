import scandir
import os
import exifread
import argparse
import hashlib
import datetime
import shutil

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
    filebanner()
    for dirname, dirnames, filenames in scandir.walk(source):
        for filename in filenames:
            fileupper = filename.upper()
            if fileupper.endswith(imagetypes):
                sha256, date, exif = getDeets(os.path.join(dirname, filename))
                filebanner(sha256, date, exif, dirname, filename)
                if not testMode:
                    move_file(date, dirname, dest, filename, sha256)
            else:
                notparsed.append(os.path.join(dirname, filename))


def move_file(date, source, dest, filename, sha256):
    global duplicate # Needed for duplicate tracking
    global notparsed # Needed for notparsed tracking
    destination = os.path.join(dest, date[0], date[1], filename) # This creates the final destination directory\filename
    if verbose:print('Processing: %s \nDestination: %s' % (os.path.join(source, filename), destination)),
    if os.path.exists(destination): # No need to check for duplicate if DIR doesnt even exist
        oldFileSHA256 = hashFile(destination) #hash existing file
        if oldFileSHA256 == sha256: # DUPLICATE CHECKING
            if verbose:print(G + ' [Duplicate File Found]' + W)
            if moveMode:os.remove(os.path.join(source, filename)) # Because we have the same file, no need to keep this one
            duplicate += 1
            return
    if not os.path.exists(os.path.join(dest, date[0], date[1])): #If the destination dir doesnt exist
        try:
            if verbose:print('Making %s Directory' % os.path.join(dest, date[0], date[1]))
            os.makedirs(os.path.join(dest, date[0], date[1])) #Try to create it
        except Exception, e:
            print('')
            print (R + 'error: %s' % e + W)
            notparsed.append(os.path.join(source, filename))
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
        print('#' + R + ' **TEST MODE** ' + W + 'No file operations')
    else:
        if moveMode:
            print('#' + R + ' **MOVE FILE MODE** ' + W + 'No file operations')
        else:
            print('#' + R + ' **COPY FILE MODE** ' + W)
    
    if exif:
        print(W + '# File details retreived from: ' + G + ' EXIF Data')
    else:
        print(W + '# File details retreived from: ' + G + ' Operating System')
    print(W + '# Year: ' + G + date[0] + W + ' | Month: ' + G + date[1] + W + ' | Day: ' + G + date[2])
    print(W + '# Directory: ' + G + dirname)
    print(W + '# File Name: ' + G + filename)
    print(W + '# SHA256 Hash: ' + G + sha256 + W)
    print '#' * 80
    print("")
    print('  [' + G + '+' + W + '] EXIF Files: %s' % len(exiffiles))
    print('  [' + G + '+' + W + '] OS Files: %s' % len(osfiles))
    print('  [' + G + '+' + W + '] Total Files Processed: %s' % filecount)
    print('  [' + R + '-' + W + '] Total Duplicate Files Found: %s' % duplicate)
    print('  [' + R + '-' + W + '] Total Files NOT Copied: %s' % len(notparsed))
    print('')


def getDeets(file, block_size=2**20):
    global exiffiles
    global osfiles
    global filecount
    f = open(file, 'rb')
    tags = exifread.process_file(f)
    sha256 = hashFile(file)
    date, exif = getDate(tags, file)
    if not exif:
        date = [date[0][0], date[0][1], date[0][02], date[1], date[2], date[3]]
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
        exif = False
    return date, exif

def displayNotparsed(notparsed):
    if len(notparsed) >= 20:
        print('%s files were not processed, Would you like to see those items?' % len(notparsed))
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
filecount = 0
exiffiles = []
osfiles = []
imagetypes = ('.GIF', '.JPG', '.PNG', '.JPEG')
notparsed = []
duplicate = 0
#-------------------Init global vars----------------------------------

if __name__ == "__main__":
    # execute only if run as a script
    photosort(imagetypes, sourceDir, destinationDir)
    print('')
    displayNotparsed(notparsed)
    print('')
    print('Photosort has completed all operations')