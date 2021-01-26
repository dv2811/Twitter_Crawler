from unidecode import unidecode

threshold = 10
string_exclude = { 
3: ["the","for","are","you","and","amp","our","how",'but','has','who','can','not'],
4: ["from","that","with","this","will","some","more","what","your","they",'just','have','does','also','here'],
5: ["which",'where','these','while','maybe','there','their'],
7: ["because"],
}

muted_users=('thestalwart', 'raoulgmi','balajis', 'northmantrader', 'apompliano', 'santiagoaufund','dtapcap', 'lukegromen', 'amlivemon', 'chamath', 'reformedbroker','huxijin_gt')

def text_count(string):
	delims = (' ',',',"'",'\n','?','&','!','"','(',')','<','=',';','+','|',"*")
	indx = 0
	outdata=[]
	limit = len(string)
	while indx<limit-1:
		if string[indx] not in delims:
			for j in range(indx+1,limit,1):
				if string[j] in delims:  
					tmp = string[indx:j]
					break
				if j == limit-1:
					j+=1
					tmp = string[indx:]
					break
					#self.array.append(string[indx:j].lower())
					# Word shorter than 3 letter won't be counted as meaningful

			if j-indx > 2:
				if 'http' in tmp or tmp[0] in ('#','$','@'):
					pass
				# Links won't be counted as useful words
				elif (j-indx) in string_exclude and tmp.lower() in string_exclude[(j-indx)]:
					pass
				# Cashtags and Hashtags are counted separately
				elif '.' in tmp:
					outdata+=[char.lower() for char in tmp.split('.') if len(char)>2]
				elif ':' in tmp:
					outdata+=[char.lower() for char in tmp.split(':') if len(char)>2]
				elif '/' in tmp:
					outdata+=[char.lower() for char in tmp.split('/') if len(char)>2]
				else:
					outdata.append(tmp.lower())
				#self.useful_words_count+=1
			indx = j+1
		else:
			indx+=1
	return outdata

def tweet_obj_gen(tweet_data):

	temp_dict = {}
	if tweet_data == {}:
		return {}
	# Generate text field if not present
	temp_dict['text']= unidecode(tweet_data['text'])
	temp_dict['type']= tweet_data['type']
	# Determine Tweet type

	temp_dict['conversation_id']=tweet_data['conversation_id']
	# Replace retweet conversation id with that of the original tweet
	if temp_dict['type'] == 'retweet':
		temp_dict['conversation_id'] = tweet_data['referenced_tweets'][0]['id']
	temp_dict['id']=tweet_data['id']

	temp_dict['context_annotations']=[]
	temp_dict['linked_site']=''
	temp_dict['link_url']=''
	temp_dict['link_description']=''
	temp_dict['link_title']=''
	temp_dict['stocks']=[]

	if 'context_annotations' in tweet_data:
		temp_dict['context_annotations']=[context['entity']['name'].lower().strip() for context in tweet_data['context_annotations']]
	#if temp_dict['type'] in ('retweeted','quoted'):

	if 'entities' in tweet_data:
		ent = tweet_data['entities']
		if 'hashtags' in ent:
			for tag in  ent['hashtags']:
				if tag['tag'].lower() not in temp_dict['context_annotations']:
					temp_dict['context_annotations'].append(tag['tag'].lower().strip())
		if 'annotations' in ent:
			for antn in ent['annotations']:
				ant_text = antn['normalized_text'].lower()
				if ant_text != '':
					if ant_text[0]!='$' and ant_text not in temp_dict['context_annotations']:
						temp_dict['context_annotations'].append(antn['normalized_text'].lower().strip())
		# Stock tickers
		if 'cashtags' in ent:
			temp_dict['stocks']=list(set([tag['tag'].replace('$','').lower().strip() for tag in  ent['cashtags']]))
		# Embedded URL - First displayed URL are often with real content and folllowing ones are pictures or thumnails
		# We can add expansions.media_key to assesss whether attachments are GIF, vid or link - GIF to be discarded [future version]
		#if temp_dict['type'] == 'tweet' or temp_dict['type'] == 
		if 'urls' in ent:
			# unwound_url for link shortened by Twitter
			# expanded_url for link not shortened by Twitter
			# User quote a tweet AND comment with GIF, photo or video - iterate through urls to find the quoted tweet
			# Set break if found linked article
			# 1st found linked article will be prioritise over quoted tweet (if user put both a link and Twitter link to a tweet)
			# This approach won't hold if an user decides to put multiple article links in one tweet, but this would be rare enough provided for
			for urlsobj in ent['urls']:
				if 'pic' not in urlsobj['display_url']:

					if 'unwound_url' in urlsobj:
						temp_dict['link_url']=urlsobj['unwound_url']
					elif'expanded_url' in urlsobj:
						temp_dict['link_url']=urlsobj['expanded_url']
					else:
						pass
					if 'title' in urlsobj:
						temp_dict['link_title'] = urlsobj['title']
					if 'description' in urlsobj:
						temp_dict['link_description'] = urlsobj['description']
						break

			# If referenced link is NOT a twitter link
			if 'twitter' in temp_dict['link_url'][:25]:
				temp_dict['linked_site']=[temp_dict['link_url'].split('/')[3].lower()]
				if temp_dict['linked_site'][0] in muted_users:
					return {}
			elif temp_dict['link_url']!= '':
				#print (temp_dict['link_url'][:25])
				# Return URL without GET parameter
				slc = temp_dict['link_url'].find('?')
				if slc !=-1:
					temp_dict['link_url'] = temp_dict['link_url'][:slc]
				temp_dict['linked_site']=[temp_dict['link_url'].split('://')[1].split('/')[0]]
			else:
				pass
	# Retweet Handling
	#Text = Linked content
	# If retweet of same user's post - discard
	temp_dict ['string_list'] = tweet_data ['string_list']
	# Tweet_data objs that pass through this point must be either quote tweets, tweets or replies
	# If content of the tweet is not sufficient - content from shared links will be considered
	# Retweet counts carry less weight than reply or quote_count (quote and reply are quite similar in term )
	if 'public_metrics' in tweet_data:

		temp_dict['popularity'] = tweet_data['public_metrics']['reply_count']\
								+ tweet_data['public_metrics']['quote_count']\
								+ int(tweet_data['public_metrics']['retweet_count']/2)
		if temp_dict['popularity'] == 0:
			temp_dict['popularity'] = 1
	else:
		# set pop at basic if none is present
		temp_dict['popularity'] = 1


	if len(tweet_data ['string_list']) < threshold:
		if temp_dict['link_description']!='':
			temp_dict['text'] = temp_dict['link_title']+' '+temp_dict['link_description']
			temp_dict['string_list'] = text_count(temp_dict['text'])
		# Frivolous content with high like count and no substance - discard 
		elif 'public_metrics' in tweet_data and tweet_data['public_metrics']['like_count'] > 100 and temp_dict['stocks'] == []:
			#print ('Excluded for being too popular!')
			#print (temp_dict)
			return{}
	else:
		pass


	temp_dict['context_annotations'] = list(set(temp_dict['context_annotations']))

	return temp_dict
