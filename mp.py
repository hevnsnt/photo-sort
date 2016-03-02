import os
import re
import sys
from stat import S_ISREG
import multiprocessing as mp

# uncomment these if you really want a hard-coded $HOME/patterns file
#home = os.environ.get('HOME')
#patterns_file = os.path.join(home, 'patterns')

target = sys.argv[1]
size_limit = int(sys.argv[2])
assert size_limit >= 0
patterns_file = sys.argv[3]


# build s_pat as string like:  (?:foo|bar|baz)
# This will match any of the sub-patterns foo, bar, or baz
# but the '?:' means Python won't bother to build a "match group".
with open(patterns_file) as f:
    s_pat = r'(?:{})'.format('|'.join(line.strip() for line in f))

# pre-compile pattern for speed
pat = re.compile(s_pat)


def walk_files(topdir):
    """yield up full pathname for each file in tree under topdir"""
    for dirpath, dirnames, filenames in os.walk(topdir):
        for fname in filenames:
            pathname = os.path.join(dirpath, fname)
            yield pathname

def files_to_search(topdir):
    """yield up full pathname for only files we want to search"""
    for fname in walk_files(topdir):
        try:
            # if it is a regular file and big enough, we want to search it
            sr = os.stat(fname)
            if S_ISREG(sr.st_mode) and sr.st_size >= size_limit:
                yield fname
        except OSError:
            pass

def worker_search_fn(fname):
    with open(fname, 'rt') as f:
        # read one line at a time from file
        for line in f:
            if re.search(pat, line):
                # found a match! print filename to stdout
                print(fname)
                # stop reading file; just return
                return

mp.Pool().map(worker_search_fn, files_to_search(target))
