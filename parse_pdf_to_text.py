#!/usr/bin/env python

"""
Very simple script that simply iterates over all files pdf/f.pdf
and create a file txt/f.pdf.txt that contains the raw text, extracted
using the "pdftotext" command. If a pdf cannot be converted, this
script will not produce the output file.
"""

#import cPickle as pickle
#import urllib2
#import shutil
import time
import os
#import random

os.system('mkdir -p txt') # ?

#have = set(os.listdir('txt'))

have = []
for r, d, files in os.walk('txt') :
	for f in files :
		if f.endswith('.txt') :
			have.append(f)
have = set(have)


for r, d, files in os.walk('pdf') :
	for f in files :
		if not f.endswith('.pdf') : continue

		folder = r.replace('pdf', 'txt')
		if not os.path.isdir(folder) :
			os.mkdir( folder )

		pdf_path = os.path.join( r, f)
		file_size = os.path.getsize( pdf_path )
		if file_size < 10000 :
			print 'too small to be a pdf: %s %d' % (pdf_path, file_size)
			#os.unlink( pdf_path )
			continue

		txt_basename = f.replace('pdf', 'txt')
		txt_path = pdf_path.replace('pdf', 'txt')
		if not txt_basename in have :
			cmd = "pdftotext %s %s" % (pdf_path, txt_path)
			print '%s' % cmd
			os.system(cmd)

			# check output was made
			if not os.path.isfile(txt_path):
				# there was an error with converting the pdf
				os.system('touch ' + txt_path) # create empty file, but it's a record of having tried to convert

			time.sleep(0.02) # silly way for allowing for ctrl+c termination
#		else:
#			print 'skipping %s, already exists.' % (pdf_path, )
