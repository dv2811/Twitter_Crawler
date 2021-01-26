# -*- coding':'utf-8 -*-
from requests import get,post
from unidecode import unidecode
from json import loads,dumps
from tw_utils import text_count, tweet_obj_gen
from datetime import datetime,date,timedelta
from dateutil.tz import *

token = 'AAAAAAAAAAAAAAAAAAAAAGa4KwEAAAAAzwahzmg3facOICE5gTSIGTch%2BbQ%3DDw7f9jkcJrAczABdFi3W8AXuWTk9NDD68yXLdkfqM1lBttT4Yy'
headers = {"Authorization": "Bearer {}".format(token)}
threshold = 10
#Get time in UTC
nw = datetime.now(tzlocal()).astimezone(tzoffset(None, 0)).replace(tzinfo=None)
#Tweet past 2 days
day = 2
date_from = (nw+timedelta(days=-day)).strftime('%Y-%m-%dT%H:%M:%SZ')
tweet_list = []
id_collector = []
# List of Twitter accounts


params = {'tweet.fields':'referenced_tweets,conversation_id,created_at,in_reply_to_user_id,context_annotations,entities,public_metrics,lang',
		'expansions':'attachments.poll_ids',
		'media.fields':'type',
		'user.fields':'username',
		'start_time':date_from,
		'max_results':'100',}

# Contents from these users will be excluded from consideration
muted_users=('thestalwart', 'raoulgmi', 'northmantrader', 'apompliano','dtapcap','santiagoaufund', 'lukegromen', 'amlivemon', 'chamath', 'reformedbroker','huxijin_gt','balajis')
muted_user_id=['14096763','2453385626','1001490017917784064','714051110','339061487','583517629','2936015319','895814938995957760','3540699975','2775998016','2178012643']


def get_id(screen_name):
	url = 'https://api.twitter.com/2/users/by/username/'+screen_name
	res = get(url,headers=headers).text.split('id":"',1)[1].split('","')[0]
	return res

def referenced_tweet_find(tweet_id):
	# Added author_id for this module as we may encounter content from muted users
	params = {'tweet.fields':'referenced_tweets,conversation_id,created_at,in_reply_to_user_id,context_annotations,entities,public_metrics,author_id,lang',
	'expansions':'attachments.poll_ids',
	#'media.fields':'type',
	'user.fields':'username',
	'ids':tweet_id,
	}
	response = get('https://api.twitter.com/2/tweets', headers=headers, params=params)
	try:
		response = loads(response.content)['data'][0]
	except:
		return {}
	if response['author_id'] in muted_user_id or 'attachments' in response:
		return {}
	if 'referenced_tweets' in response:
		if 'in_reply_to_user_id' in response and response['in_reply_to_user_id'] not in muted_user_id:
			if response['in_reply_to_user_id']==response['author_id']:
				response.update({'type':'thread'})
			else:
				response.update({'type':'reply'})
		else:
			# No Retweet could be retweeted or quoted
			# Retweets /  Quote tweets of quote tweets are too 'loopy' for serious contents - could return {} in here and stop?
			response.update({'type':'quote'})
	else:
		response.update({'type':'tweet'})
	# Tweet text count larger than 10 (avg word length + space = 4)
	string_list = text_count( unidecode(response['text']) )

	if len(string_list) < threshold and 'http' not in response['text'] :
		return {}
	else:
		response.update({'string_list':string_list})

	return response

def tweet_process(tweet_data):
#	try:
	text = unidecode(tweet_data['text'])
#	except:
#		print (tweet_data)
	string_list = text_count(text)
	word_length = len(string_list)

	if word_length < threshold:
		if tweet_data['type']	== 'reply':
			return {}
		elif tweet_data['type'] == 'tweet':
			if 'entities' not in tweet_data:
				return {}
			else:
				tweet_data.update({'string_list': string_list})
				return (tweet_obj_gen(tweet_data))
		else:
			child_id = tweet_data['referenced_tweets'][0]['id']
			if child_id not in id_collector:
				id_collector.append(child_id)
				return (tweet_obj_gen(referenced_tweet_find( child_id )))
			else:
				return {}
	else:
		if tweet_data['type'] == 'quote':
			id_collector.append( tweet_data['id'] )
		tweet_data.update({'string_list': string_list})
		return (tweet_obj_gen (tweet_data))

def tweet_category(item,screen_name,userid):
	if 'attachments' in item or item['lang'] not in ('en','fr'):
		return {}
	else:
		if 'referenced_tweets' in item.keys():
			if item['referenced_tweets'][0]['type'] == 'retweeted':

				text = item['text']
				rt_name = text[4:text.find(':',4)].lower()
				if rt_name ==  screen_name.lower() or rt_name in muted_users:
					return {}
				else:
					item.update({'type':'retweet'})

			elif 'in_reply_to_user_id' in item:
				id_collector.append(item['id'])
				if item['in_reply_to_user_id'] == userid:
					item.update({'type':'thread'})
				else:
					item.update({'type':'reply'})

			else:
				item.update({'type':'quote'})

		else:
			id_collector.append(item['id'])
			item.update({'type':'tweet'})
		return item

class get_user_timeline():

	def __init__(self,hit):
		# If user ID is supplied - add to link
		# If user ID is NOT supplied - look up user ID automatically
		if hit[1].isdigit():
			self.userid = hit[1]
		else:
			self.userid = get_id(hit[0])
		url = 'https://api.twitter.com/2/users/{}/tweets'.format(self.userid)
		if hit[2]=='1':
			params.update({'exclude':'retweets'},)
		elif hit[2]=='2':
			params.update({'exclude':'retweets,replies'},)
		else:
			pass

		self.next_token=''
		self.tweet_request_obj(url, params,hit[1] )
		while self.next_token!='':
			params.update({'pagination_token':self.next_token})
			self.tweet_request_obj(url, params,hit[1] )

	# Connect to Twitter API
	def tweet_request_obj(self,url, params,screen_name):

		response = get( url, headers=headers, params=params)

		if response.status_code != 200 :
			print ('Request returned an error: {} {}'.format(response.status_code, response.text))
			self.next_token=''
		elif 'data' not in response.text:
			self.next_token=''
			pass
		else:
			tweet_list_obj = loads(response.content)
			for item in tweet_list_obj['data']:
				tmp = tweet_category(item,screen_name,self.userid)
				if tmp !={}:
					print (screen_name, tmp['id'])
					tweet_list.append(tmp)

			# Get next page token - if not exist, return ''
			if 'meta' in tweet_list_obj and 'next_token' in tweet_list_obj['meta']:
				self.next_token=tweet_list_obj['meta']['next_token']
			else:
				self.next_token=''
			#print (json.dumps(tweet_list_obj['data'],indent=3, sort_keys=True))
def tweet_agg_dict(users):
	
	tweet_dict={}
	for user in users:
		get_user_timeline(user)

	for item in tweet_list:
		#print (item)
		d = tweet_process(item)
		if d != {}:
			if 'string_list' not in d:
				print (d)
			conv_id = d['conversation_id']
			if conv_id in tweet_dict:
				tweet_dict [conv_id].append (d)
			else:
				tweet_dict.update({conv_id : [d]})
	return tweet_dict