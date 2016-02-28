#####################
# Read list of image files
# Check for Exif Date
# If no exif then check last modified date

import exifread
import scandir
# import glob
import os.path
import shutil
import datetime
import argparse  # Needed to parse commandline arguments
from os import system, name  # Needed to clear the screen for any OS
import fnmatch
import hashlib

############################## Config #####################################
ostype = 'osx'  # Valid types are: nix, osx, or win


############################## Setup #####################################
##DO NOT EDIT BELOW THIS LINE
'''known probs
uses cp, will not work on windows systems
'''
version = '0x01'
if name == 'nt':
	slash = '\\'
	copy = 'copy'
else:
	slash = '/'
	copy = 'cp'


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


def getFiles():
	matches = []
	if not sourceDir == "":
		for root, dirnames, filenames in scandir.walk(sourceDir):
			for filename in fnmatch.filter(filenames, '*.*'):
				matches.append(os.path.join(root, filename))


def getDate(tags, f):
	if 'EXIF DateTimeOriginal' in tags:
		date = str(tags['EXIF DateTimeOriginal']).replace(':', ' ').split()
		source = 'exif'
		if not testMode: print('EXIF Year: %s | Month: %s | Day: %s' % (date[0], date[1], date[2]))
		if not testMode: move_file(f, date[0], date[1], date[2])
	else:
		#print('File has no date information, using last modified date')
		date = str(datetime.datetime.fromtimestamp(os.stat(f).st_mtime)).replace(':', ' ').split()
		date[0] = date[0].replace('-', ' ').split()
		source = 'OS'
		if not testMode: print('Year: %s | Month: %s | Day: %s' % (date[0][0], date[0][1], date[0][2]))
		if not testMode: move_file(f, date[0][0], date[0][1], date[0][2])
	return date, source


def move_file(file, year, month, day):
	destination = destinationDir + slash + year + slash + month + slash + year + '-' + month + '-' + day + slash
	#print('I would move file %s to dir %s' % (file, destination))
	if not testMode:
		try:
			os.makedirs(destination)
		except Exception, e:
			if verbose:
				print ('error: %s' % e)
				raw_input()
		try:
			shutil.cp(file, destination)
		except Exception, e:
			if verbose:
				print ('error: %s' % e)
				raw_input()
		if moveMode:
			sourchHash = hashFile(file)
			print('%s : %s' % (file, sourchHash))
			raw_input()


def hashFile(file):
	'''Will return the sha1 hash of a file, expects path to file'''
	f = open(file, 'rb')
	f = f.read()
	sha256 = hashlib.sha256(f).hexdigest()
	return sha256


def banner():
	system(['clear', 'cls'][name == 'nt'])  # Use the system command clear, unless the system name is nt, then use cls
	print(GR + '        ' + '>' * 18 + '<' * 17)
	print(GR + '        >>>>>>>>' + G + ' photoSort ' + T + 'v' + version + GR + ' <<<<<<<<' + W)
	print(GR + '        ' + '>' * 18 + '<' * 17)
	if verbose:
		print('            ' + '[' + R + '>>>>' + W + '] Verbose mode enabled')
		if name == 'nt':
			print('            ' + '[' + R + '>>>>' + W + '] Windows machine detected\n')
		else:
			print('            ' + '[' + R + '>>>>' + W + '] *nix machine detected\n')

	print(T + 'Reading Files from: ' + W + sourceDir)
	print(T + 'Sorting Files to: ' + W  + destinationDir + '\n')


def display(fname, sha256, date, source):
	banner()
	print(T + 'Currently processing:')
	print(T + 'File: ' + W + fname)
	print(T + 'SHA256: ' + W + sha256)
	print(T + 'Date: ' + W + str(date))
	print(T + 'Source: ' + W + source)
	'''if source == 'exif':
		raw_input()'''


def getDeets(file, block_size=2**20):
	fname = file
	f = open(file, 'rb')
	tags = exifread.process_file(f)
	#f = f.read()
	sha256 = hashFile(fname)
	date, source = getDate(tags, fname)
	return sha256, fname, date, source


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
files = glob.glob(sourceDir + slash + '*.*')
#-------------------Init global vars----------------------------------

if __name__ == "__main__":
	banner()
	#print files
	for f in files:
		#print file
		sha256, fname, date, source = getDeets(f)
		display(f, sha256, date, source)
	
	
