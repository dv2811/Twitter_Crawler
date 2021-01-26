# -*- coding':'utf-8 -*-
#from os.path import dirname,realpath
import json
from requests import get,post
from math import log
from datetime import datetime
from unidecode import unidecode
from dbx_utils import dbx_read,dbx_upload
from math import log

#file_path = dirname(realpath(__file__))
dbx_path = '/Share/Common_Projects/twitter_feeds/inputs'

def sort(result_list):
	for i in range(len(result_list)):
		for j in range(i+1,len(result_list), 1):
			# Sort Tweet by score 
			if result_list[j][1] > result_list[i][1]:
				tmp = result_list[i]
				result_list[i] = result_list[j]
				result_list[j] = tmp
	#return result_list

def dict_gen(filedata):
	data = {}
	content_list = [line.split(',') for line in filedata.splitlines() if line[0]!='#']
	for line in content_list:
		if len(line[0]) not in data:
			data.update({len(line[0]):{ line[0]: [int(line[1])]+line[2:] } })
		else:
			data[ len(line[0])].update({line[0]: [int(line[1])]+line[2:] })
	return data

def score_check(string_list,check_dict):
	# Saturation, 1st keyword match gets full score,2nd one gets int half score,0 for from 3rd one
	collector = []
	coeff = {}
	temp_score = 0
	j_list = []
	# initialize collector
	for item in string_list:
		key = len(item)
		if key in check_dict:
			if item in check_dict[key]:
#				print (item,'added')
				j_list.append(item)
				if check_dict[key][item][1:]!=[]:
					for mem in check_dict[key][item][1:]:
						if mem not in collector:
							# Topics / keywords that often go together reduce their overall score to make up for duplication effect
								# Related topics/ keywords are general topics / keywords that also appear when a more granular keywords / topics are mentioned
								# See topics/ word_score.txt files 
								collector.append(mem)

		for item in j_list:
			if item in collector:
	#			try:
				temp_score+= int(check_dict[len(item)][item][0]/2)
				check_dict[len(item)].pop(item)
				j_list.remove (item)
	#			except:
	#				pass
			else:
				temp_score+= check_dict[len(item)][item][0]
				collector.append(item)
	return temp_score

def tweet_embed(tweet_id):
	url = 'https://publish.twitter.com/oembed'
	data ={
		'url': 'https://twitter.com/i/status/{}'.format(tweet_id),
		'align':'center',
		'omit_script':'true',
		'maxwidth':'550',
		'theme':'dark',
	}
	try:
		response = json.loads(get(url,params = data).content)
		return response['html']
	except Exception as e:
		print (tweet_id)
		print (e)
		return ''
# Grade Tweet and organise by score
class tweet_grading():

	def __init__(self,data):
		
		self.score_dict = []
		self.data = data
		self.word_score = dict_gen(dbx_read(dbx_path+'/word_score.txt'))
		self.topics = dict_gen(dbx_read(dbx_path+'/topics.txt'))
		self.stocks = dict_gen(dbx_read(dbx_path+'/stocks.txt'))
		self.sites = dict_gen(dbx_read(dbx_path+'/site_score.txt'))
		if data == {}:
			pass
		else:
			highscorelist = []
			otherlist = []
			for key in self.data:
				item_score = self.conversation_score(data[key])
				if item_score > 10:
					self.score_dict.append( (key,item_score ) )

			for item in self.score_dict:
				if item[1] > 30:
					highscorelist.append (tweet_embed( item[0] ))
				else:
					otherlist.append (tweet_embed( item[0] ))
			# Sort result by score
			sort(highscorelist)
			sort(otherlist)
			timestamp_string = '<p class = "datestamp">%s</p>'%(datetime.now().strftime('%Y-%m-%d'))
			# Write results with high scores
			tmp_data = timestamp_string+unidecode( ''.join(highscorelist)) + '<script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>'
			dbx_upload(tmp_data,'/Thematic Dossier/Tweets_Highlights.html')
			#with open('Highlights.html','w') as f:
			#	f.write(tmp_data)
			# Write results with low scores
			tmp_data = timestamp_string+unidecode( ''.join(otherlist)) + '<script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>'
			dbx_upload(tmp_data,'/Thematic Dossier/Tweet_Others.html')
			#with open('Others.html','w') as f:
			#	f.write(tmp_data)
	# Create score 
	def single_tweet_score(self,tweet_data):

		if len(tweet_data['string_list']) > 18:
			score_data = 5
		else:
			score_data = 0

		score_data  = score_data + score_check(tweet_data['string_list'],self.word_score) \
					+ score_check(tweet_data['stocks'],self.stocks) \
					+ score_check(tweet_data['context_annotations'],self.topics) \
					+ score_check(tweet_data['linked_site'],self.sites) \
					+  5*len(tweet_data['stocks'])

		pop_score = int(10*log(tweet_data['popularity'],10))
		if score_data <= 5 and pop_score > 25:
			# Exclude tweet with high popularity score but low content score
			return -10
		else:
			return score_data+pop_score

	def conversation_score(self,tweet_list):
		score = 0
		temp_annotation = []
		if len(tweet_list) == 1:
			return self.single_tweet_score(tweet_list[0])
		else:
			score_record = 0
			for item in tweet_list:
				if item['type'] == 'thread':

					if temp_annotation == []:
						temp_annotation = item['context_annotations']
					else:
						for context in item['context_annotations']:
							if context not in item['context_annotations']:
								temp_annotation.append(context)
					item['context_annotations'] = []
					score += self.single_tweet_score(item)
				else:
					temp = (score_check(item['string_list'],self.word_score) + score_check(item['linked_site'],self.sites))
					if temp > 10:
						# Replies and Quotes add point to the conversation but only high score will be registered to avoid over-assigment
						# Replies would be considered with half the weight of thread
						score_record += int(temp/2)
		score = score + temp + score_check(temp_annotation,self.topics)
		return score