import tweepy
import os
from dotenv import load_dotenv

load_dotenv()

TWITTER_CONSUMER_KEY = os.getenv("TWITTER_CONSUMER_KEY")
TWITTER_CONSUMER_SECRET = os.getenv("TWITTER_CONSUMER_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
os.environ["TWITTER_CONSUMER_KEY"] = TWITTER_CONSUMER_KEY
os.environ["TWITTER_CONSUMER_SECRET"] = TWITTER_CONSUMER_SECRET
os.environ["TWITTER_ACCESS_TOKEN"] = TWITTER_ACCESS_TOKEN
os.environ["TWITTER_ACCESS_SECRET"] = TWITTER_ACCESS_SECRET


class TwitterPost:
    def __init__(self):
        self.client = self.twitConnection()

    def twitConnection(self):
        client = tweepy.Client(
            consumer_key=TWITTER_CONSUMER_KEY, consumer_secret=TWITTER_CONSUMER_SECRET,
            access_token=TWITTER_ACCESS_TOKEN, access_token_secret=TWITTER_ACCESS_SECRET)

        return client

    def make_tweet(self, message):
        client = self.twitConnection()
        client.create_tweet(text=message)


if __name__ == '__main__':
    tweet = TwitterPost()
    tweet.make_tweet("Hello, i am a tester")
    print("Tweeted successfully")
