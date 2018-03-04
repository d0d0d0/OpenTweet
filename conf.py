### Twitter API credits ###
CONSUMER_KEY = "OBFUSCATED"
CONSUMER_SECRET = "OBFUSCATED"

ACCESS_TOKEN = "OBFUSCATED"
ACCESS_SECRET = "OBFUSCATED"

### mongoDB information ###
HOST = "localhost"
PORT = 27017
DATABASE = "twitter"
COLLECTION = "tweets"

### In-class information ###
COUNTRY = "Turkey"														# Searching country
COUNT = 200																# Number of tweets
FIELDS = ['id', 'user', 'text', 'date', 'longitude', 'latitude']		# Fields of csv file
IS_CSV = False															# If false, it save tweets to mongoDB stated above
CSV_NAME = "tweets.csv"													# Excel file to save information
META_NAME = "meta.txt"													# Tweet meta analyze file
SAMPLE_NAME = "sample.csv"												# Excel file to create sample from db

TIMES = 500 																# Update count 
MINUTE_15 = 60*15

RATE_LIMIT_CODE = "429"