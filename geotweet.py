'''
	Created by Doganalp Ergenc
'''

from shutil import copyfile
from os import remove, path
from time import gmtime, strftime, sleep
from pymongo import MongoClient
'''
	Python library for twitter api
'''
import tweepy
import csv
import pprint
import json
from conf import *


class GeoTweet:
	'''
		* GeoTweet created for fetching and saving geo-tagget tweets in a particular country to a CSV file
		* Since it is restricted with Twitter API rate-limit, it restarts itself in every 15 minutes
		* All necessary parameters is defined in config file - conf.py
		* It is also extended to save whole tweets to a mongoDB
	'''
	def __init__(self, con_key=CONSUMER_KEY, con_sec=CONSUMER_SECRET, acc_tok=ACCESS_TOKEN, acc_sec=ACCESS_SECRET):
		self.auth = tweepy.OAuthHandler(con_key, con_sec)
		self.auth.set_access_token(acc_tok, acc_sec)
		self.api = tweepy.API(self.auth)
		self.total_tweets = 0
		self.geotagged_tweets = 0

	def get_place(self, country=COUNTRY):
		'''
		Finds id of a particular country
		'''
		try:
			places = self.api.geo_search(query=country, granularity="country")
			self.place_id = places[0].id
		except Exception as e:
			print str(e)

	def get_recent_tweets(self, is_csv=IS_CSV, count=COUNT):
		'''
		Gets recent tweets (as counts) in a particular country and saves them to csv or mongodb
		'''
		for tweet in tweepy.Cursor(self.api.search, q="place:%s" % self.place_id, count=count).items():
			if is_csv:
				self.save_tweet_csv(tweet)
			else:
				self.save_tweet_db(tweet)

	def update_meta_info(self, meta_name=META_NAME, is_csv=IS_CSV):
		'''
		Record rate of geo-tagged tweets
		'''
		try:
			date = strftime("%Y-%m-%d_%H:%M:%S", gmtime())
			if path.isfile(meta_name):
				meta_split = meta_name.split('.')
				new_name = meta_split[0] + "_" + str(date) + "." + meta_split[1]
				copyfile(meta_name, new_name)
				remove(meta_name)
			with open(meta_name, 'wb') as meta_file:
				if IS_CSV:
					rate = self.geotagged_tweets*1.0/self.total_tweets if self.total_tweets > 0 else 0
					meta_file.write("Total tweets: %d ## geo-tagged tweets: %d ## rate %f" % (self.total_tweets, self.geotagged_tweets, rate))
				else:
					meta_file.write(self.analyze_db())
			meta_file.close()
		except Exception as e:
			print str(e)

	def prepare_header(self, csv_name=CSV_NAME, fields=FIELDS):
		'''
		Preapre CSV headers with fields
		'''
		try:
			with open(csv_name, 'a') as csvfile:
			    writer = csv.DictWriter(csvfile, fieldnames=fields, delimiter='|')
			    writer.writeheader()
		except Exception as e:
			print str(e)

	def save_tweet_csv(self, tweet, csv_name=CSV_NAME, fields=FIELDS):
		'''
		Save tweets to CSV file with location information, with the fields (id, longitude, latitude, user, text, date)
		'''
		try:
			with open(csv_name, 'a') as csvfile:
			    writer = csv.DictWriter(csvfile, fieldnames=fields, delimiter='|')
			    self.total_tweets += 1
			    if tweet.geo:
			    	self.geotagged_tweets += 1
			    	writer.writerow({
			    						'id':			tweet.id_str, 
			    						'longitude': 	str(tweet.geo['coordinates'][0]),
			    						'latitude': 	str(tweet.geo['coordinates'][1]),  
			    						'user': 		tweet.user.screen_name, 
			    						'text': 		tweet.text.encode("ascii", errors="ignore"),
			    						'date': 		str(tweet.created_at) 
			    					})
		except Exception as e:
			print str(e)

	def save_dict_tweet_csv(self, tweet, csv_name=CSV_NAME, fields=FIELDS):
		'''
		Save dictionary tweets from db to CSV file with location information, with the fields (id, longitude, latitude, user, text, date)
		'''
		try:
			with open(csv_name, 'a') as csvfile:
			    writer = csv.DictWriter(csvfile, fieldnames=fields, delimiter='|')
			    if tweet.get('geo'):
			    	writer.writerow({
			    						'id':			tweet['id_str'], 
			    						'longitude': 	str(tweet['geo']['coordinates'][0]),
			    						'latitude': 	str(tweet['geo']['coordinates'][1]),  
			    						'user': 		tweet['user']['screen_name'], 
			    						'text': 		tweet['text'].encode("ascii", errors="ignore"),
			    						'date': 		str(tweet['created_at']) 
			    					})
			    	return 0
			return 1
		except Exception as e:
			print str(e)
			return 1

	def save_tweet_db(self, tweet, host=HOST, port=PORT, db=DATABASE, collect=COLLECTION):
		'''
		Saves a single tweet to db
		'''
		try:
			# TODO: Keep it connected instead of reopening for every tweet
			client = MongoClient(host, port)
			db = client[db]
			tweet_id = db.collect.insert_one((tweet._json)).inserted_id
		except Exception as e:
			print str(e)

	def sample_db2csv(self, host=HOST, port=PORT, db=DATABASE, collect=COLLECTION, size=1000, sample_file=SAMPLE_NAME, fields=FIELDS):
		'''
		Create a sample from db to csv in size
		'''
		try:
			# TODO: Keep it connected instead of reopening for every tweet
			if path.isfile(sample_file):
				remove(sample_file)
			i = 0
			self.prepare_header(csv_name=SAMPLE_NAME)
			client = MongoClient(host, port)
			db = client[db]
			cursor = db.collect.find()
			for document in cursor:
				if i < 1000:
					if not self.save_dict_tweet_csv(tweet=document, csv_name=SAMPLE_NAME):
						i += 1
				else:
					break

		except Exception as e:
			print str(e)	

	def read_db(self, host=HOST, port=PORT, db=DATABASE, collect=COLLECTION):
		'''
		Reads all tweets from db
		'''
		try:
			# TODO: Keep it connected instead of reopening for every tweet
			client = MongoClient(host, port)
			db = client[db]
			cursor = db.collect.find()
			for document in cursor:
				pprint.pprint(document)
		except Exception as e:
			print str(e)	

	def analyze_db(self, host=HOST, port=PORT, db=DATABASE, collect=COLLECTION):
		'''
		Analyze geo-tagged-ness, location correctness, total number of tweets
		'''
		try:
			num_tweets = 0
			num_outbounds = 0
			not_tagged = 0
			# TODO: Keep it connected instead of reopening for every tweet
			client = MongoClient(host, port)
			db = client[db]
			cursor = db.collect.find()
			for document in cursor:
				analyze_tweet = self.ensure_country(tweet=document)
				if analyze_tweet == 1:
					num_outbounds += 1
				elif analyze_tweet == 2:
					not_tagged += 1
				num_tweets += 1

			meta_info = " Number of tweets: %d\n Number of outbound tweets: %d\n Number of geo-tagged tweets: %d\n Ratio of geo-tagged tweets %f\n" % \
						(num_tweets, num_outbounds, num_tweets-not_tagged, (num_tweets-not_tagged)*1.0/num_tweets if num_tweets > 0 else 0)
			'''
			print "Number of tweets: ", str(num_tweets)
			print "Number of outbound tweets: ", str(num_outbounds)
			print "Number of not geo-tagged tweets: ", str(not_tagged)
			'''
			return meta_info
		except Exception as e:
			print str(e)
			return "An error occured: ", str(e)	

	def ensure_country(self, tweet, lon=(26.0, 45.0), lat=(36.0, 42.0)):
		'''
		Ensures if tweets came from desired country using longitude-latitude
		'''
		try:
			if tweet.get('geo'):
				if (lon[0] <= tweet['geo']['coordinates'][1] <= lon[1]) and (lat[0] <= tweet['geo']['coordinates'][0] <= lat[1]):
					return 0
				else:
					# print "Tweet with lon: " + str(tweet['geo']['coordinates'][1]) + " lat: " + str(tweet['geo']['coordinates'][0]) + " is out of bound."
					return 1
			else:
				return 2
		except Exception as e:
			print str(e)	

	def run(self, is_csv=IS_CSV, times=TIMES, meta_name=META_NAME):
		'''
		Overall run
		'''
		self.get_place()
		if is_csv:
			try:
				self.prepare_header()
			except Exception as e:
				print str(e)
				return

		for i in range(times):
			try:
				print "Starting to fetch.."
				self.get_recent_tweets(is_csv=is_csv)
			except Exception as e:
				# Handle twitter api rate limit
				if RATE_LIMIT_CODE in str(e):
					print "Rate limit exceeded, going to 15 minute sleep.."
					sleep(MINUTE_15)
				else:
					print str(e)
			if is_csv:
				self.update_meta_info(meta_name=meta_name)
		
if __name__ == "__main__":
	geotweet = GeoTweet()
	#geotweet.read_db()
	geotweet.run()
	#geotweet.analyze_db()
	#geotweet.update_meta_info()
	#geotweet.sample_db2csv()


