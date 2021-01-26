#from requests import get,post
from dbx_utils import dbx_read,dbx_upload
from tweet_score import tweet_grading
from tweet_obj import tweet_agg_dict
import json

users=[line.split(',') for line in dbx_read('/Share/Common_Projects/twitter_feeds/inputs/twitter_acct.txt').splitlines() if line[0]!='#']
'''
users = [["bluff_capital","849319340818169856","0"],["Emergingtrends","764591058","0"],
["Scuttlebutt_Inv","956622294054350849","0"],["WTCM3","1081240896975204352","0"],
["lillianmli","204000290","1"],]
'''
def main(dict):
	data = tweet_agg_dict(users)
	#data = json.loads(open('tweet_data.json').read())
	# Generate dicionaries
	print ('Finished Pulling Tweets...')

	# Store data for further analysis or troubleshoot
	tweet_json_output = json.dumps(data)
	dbx_upload(tweet_json_output , '/Share/Common_Projects/twitter_feeds/tweet_data.json')
	# Grade Tweet and write
	tweet_grading(data)
	return data
#main({})

