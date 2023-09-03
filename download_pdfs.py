#!/usr/bin/env python

import pickle
#import urllib2
import shutil
import time
import os
import random

import sys

if sys.version_info[0] == 3:
	from urllib.request import urlopen
else:
	# Not Python 3 - today, it is most likely to be Python 2
	# But note that this might need an update when Python 4
	# might be around one day
	from urllib import urlopen

os.system('mkdir -p pdf') # ?

timeout_secs = 10 # after this many seconds we give up on a paper
numok = 0
numtot = 0
db = pickle.load(open('db.p', 'rb'))
#have = set(os.listdir('pdf')) # get list of all pdfs we already have

have = []
for r, d, files in os.walk('pdf') :
	for f in files :
		if f.endswith('.pdf') :
			have.append(f)
have = set(have)

for pid,j in db.items():

  pdfs = [x['href'] for x in j['links'] if x['type'] == 'application/pdf']
  assert len(pdfs) == 1
  pdf_url = pdfs[0] + '.pdf'
  basename = pdf_url.split('/')[-1]
  folder = os.path.join( 'pdf', j['published'][:7])
  if not os.path.isdir(folder) :
    os.mkdir(folder)
  fname = os.path.join( folder, basename)

  # try retrieve the pdf
  numtot += 1
  try:
    if not basename in have:
      print( 'fetching %s into %s' % (pdf_url, fname))
      req = urlopen(pdf_url, None, timeout_secs)
      with open(fname, 'wb') as fp:
          shutil.copyfileobj(req, fp)
      time.sleep(0.1 + random.uniform(0,0.2))
      file_size = os.path.getsize( fname )
      if file_size < 10000 :
        print( 'too small to be a pdf: %s %d' % (fname, file_size))
        #os.unlink( fname )
    else:
      print( '%s exists, skipping' % (fname, ))
    numok+=1
  except Exception as e:
    print( 'error downloading: ', pdf_url)
    print( e)
    break

  print( '%d/%d of %d downloaded ok.' % (numok, numtot, len(db)))

print( 'final number of papers downloaded okay: %d/%d' % (numok, len(db)))
