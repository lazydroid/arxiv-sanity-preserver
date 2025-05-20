#!/usr/bin/env python

"""
Queries arxiv API and downloads papers (the query is a parameter).
The script is intended to enrich an existing database pickle (by default db.p),
so this file will be loaded first, and then new results will be added to it.
"""

#import urllib
import time
import feedparser
import os
import pickle
import argparse
import random
import utils

import sys

if sys.version_info[0] == 3:
	from urllib.request import urlopen
else:
	# Not Python 3 - today, it is most likely to be Python 2
	# But note that this might need an update when Python 4
	# might be around one day
	from urllib import urlopen

def encode_feedparser_dict(d):
	"""
	helper function to get rid of feedparser bs with a deep copy.
	I hate when libs wrap simple things in their own classes.
	"""
	if isinstance(d, feedparser.FeedParserDict) or isinstance(d, dict):
		j = {}
		for k in d.keys():
			j[k] = encode_feedparser_dict(d[k])
		return j
	elif isinstance(d, list):
		l = []
		for k in d:
			l.append(encode_feedparser_dict(k))
		return l
	else:
		return d

def parse_arxiv_url(url):
	"""
	examples is http://arxiv.org/abs/1512.08756v2
	we want to extract the raw id and the version
	"""
	ix = url.rfind('/')
	idversion = j['id'][ix+1:] # extract just the id (and the version)
	parts = idversion.split('v')
	assert len(parts) == 2, 'error parsing url ' + url
	return parts[0], int(parts[1])

if __name__ == "__main__":

	# last in cs.CV: 2021-05-20T15:24:42Z (50000)

	# parse input arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('--db_path', dest='db_path', type=str, default='db.p', help='database pickle filename that we enrich')
	parser.add_argument('--search_query', dest='search_query', type=str,
				default='cat:cs.CV+OR+cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CL+OR+cat:cs.NE+OR+cat:stat.ML',
				#default='cat:cs.CV+OR+cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CL+OR+cat:cs.NE+OR+cat:stat.ML+cat:cs.NE+OR+cat:cs.CE+OR+cat:cs.CE+OR+cat:cs.RO',
				help='query used for arxiv API. See http://arxiv.org/help/api/user-manual#detailed_examples')
	parser.add_argument('--start_index', dest='start_index', type=int, default=0, help='0 = most recent API result')
	parser.add_argument('--max_index', dest='max_index', type=int, default=50000, help='upper bound on paper index we will fetch')
	parser.add_argument('--results_per_iteration', dest='results_per_iteration', type=int, default=5000, help='passed to arxiv API')
	parser.add_argument('--wait_time', dest='wait_time', type=float, default=300.0, help='lets be gentle to arxiv API (in number of seconds)')
	parser.add_argument('--break_on_no_added', dest='break_on_no_added', type=int, default=1, help='break out early if all returned query papers are already in db? 1=yes, 0=no')
	args = parser.parse_args()

	# misc hardcoded variables
	base_url = 'http://export.arxiv.org/api/query?' # base api query url
	print( 'Searching arXiv for %s' % (args.search_query, ))

	# lets load the existing database to memory
	print('loading the database to memory')
	try:
		db = pickle.load(open(args.db_path, 'rb'))
	except Exception as e:
		print( 'error loading existing database:')
		print( e )
		sys.exit(1)
		#print( 'starting from an empty database')
		#db = {}

	original_db_size = len(db)

	# -----------------------------------------------------------------------------
	# main loop where we fetch the new results
	print( 'database has %d entries at start' % (len(db), ))
	num_added_total = 0
	current_index = args.start_index
#	for i in range(args.start_index, args.max_index, args.results_per_iteration):
	while True:

		print( "Results %i - %i" % (current_index,current_index+args.results_per_iteration))
		query = 'search_query=%s&sortBy=lastUpdatedDate&start=%i&max_results=%i' % (args.search_query, current_index, args.results_per_iteration)

		for retry in range(1,10):
#			with urlopen(base_url+query) as furl:
#				response = furl.read()
			furl = urlopen(base_url+query)
			response = furl.read()
			parse = feedparser.parse(response)

			if len(parse.entries) != 0:
				break

			print( 'Received no results from arxiv. Rate limiting? Exiting. Restart later maybe.')
			print( response)

			wait_time = args.wait_time * retry
			print( 'Sleeping for %i seconds' % wait_time)
			try:
				time.sleep(wait_time + random.uniform(0, 3))
			except KeyboardInterrupt:
				print('Got Ctrl/C, closing...')
				break

		num_added = 0
		num_skipped = 0
		for e in parse.entries:

			j = encode_feedparser_dict(e)

			# extract just the raw arxiv id and version for this paper
			rawid, version = parse_arxiv_url(j['id'])
			j['_rawid'] = rawid
			j['_version'] = version

			# add to our database if we didn't have it before, or if this is a new version
			if not rawid in db or j['_version'] > db[rawid]['_version']:
				db[rawid] = j
				print( 'updated %s added %s' % (j['updated'].encode('utf-8'), j['title'].encode('utf-8')))
				num_added += 1
			else:
				num_skipped += 1

		# print some information
		print( 'Added %d papers, already had %d.' % (num_added, num_skipped))

		if num_added == 0 and args.break_on_no_added == 1:
			print( 'No new papers were added. Assuming no new papers exist. Exiting.')
			break

		print( 'Sleeping for %i seconds' % (args.wait_time , ))
		try:
			time.sleep(args.wait_time + random.uniform(0, 3))
		except KeyboardInterrupt:
			print('Got Ctrl/C, closing...')
			break

		current_index += len(parse.entries)
		if current_index >= args.max_index: break

	# save the database before we quit
	if original_db_size != len(db):
		print( 'saving database with %d papers to %s' % (len(db), args.db_path))
		utils.safe_pickle_dump(db, args.db_path)
	else:
		print( 'database size did not change %d -> %d, skipping db save' % (original_db_size, len(db)))

''' SAMPLE PARSER FEED (empty)
>>> print( json.dumps(feedparser.parse(aaa), indent='\t'))
{
	"bozo": false,
	"entries": [],
	"feed": {
		"links": [
			{
				"href": "http://arxiv.org/api/query?search_query%3Dcat%3Acs.CV%20OR%20cat%3Acs.AI%20OR%20cat%3Acs.LG%20OR%20cat%3Acs.CL%20OR%20cat%3Acs.NE%20OR%20cat%3Astat.ML%26id_list%3D%26start%3D50000%26max_results%3D1000",
				"rel": "self",
				"type": "application/atom+xml"
			}
		],
		"title": "ArXiv Query: search_query=cat:cs.CV OR cat:cs.AI OR cat:cs.LG OR cat:cs.CL OR cat:cs.NE OR cat:stat.ML&amp;id_list=&amp;start=50000&amp;max_results=1000",
		"title_detail": {
			"type": "text/html",
			"language": null,
			"base": "",
			"value": "ArXiv Query: search_query=cat:cs.CV OR cat:cs.AI OR cat:cs.LG OR cat:cs.CL OR cat:cs.NE OR cat:stat.ML&amp;id_list=&amp;start=50000&amp;max_results=1000"
		},
		"id": "http://arxiv.org/api/428wrV1cf7z+M8yfqQxxMCo2RE0",
		"guidislink": true,
		"link": "http://arxiv.org/api/428wrV1cf7z+M8yfqQxxMCo2RE0",
		"updated": "2023-09-02T00:00:00-04:00",
		"updated_parsed": [
			2023,
			9,
			2,
			4,
			0,
			0,
			5,
			245,
			0
		],
		"opensearch_totalresults": "297445",
		"opensearch_startindex": "50000",
		"opensearch_itemsperpage": "1000"
	},
	"headers": {},
	"encoding": "utf-8",
	"version": "atom10",
	"namespaces": {
		"": "http://www.w3.org/2005/Atom",
		"opensearch": "http://a9.com/-/spec/opensearch/1.1/"
	}
}
'''
