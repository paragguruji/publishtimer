# -*- coding: utf-8 -*-
"""
Created on Tue Mar 29 13:20:37 2016

@author: Parag Guruji, paragguruji@gmail.com
"""

import requests
import os
import logging
import time
import datetime
from publishtimer import helpers, elasticsearch_util as es
from twython import Twython, TwythonError, TwythonAuthError,\
                    TwythonRateLimitError


SESSION_DURATION_MINUTES = 15
SESSION_TIMELINE_REQUEST_LIMIT = 180
SESSION_FOLLOWER_IDS_REQUEST_LIMIT = 15
RETRY_LIMIT = 3


def get_credentials(authUid):
    """Returns access_token and access_token_secret for given authUid in JSON
        format by invoking Crowdfire's internal access_details API.

        Raises ValueError if credentials for given authUid are not available.
    """
    if not isinstance(authUid, str):
        authUid = str(authUid)
    if not authUid.endswith('-tw'):
        authUid = authUid+'-tw'
    response = requests.get(url=os.environ.get(
                                    'CROWDFIRE_INTERNAL_API_BASE_URL', '') +
                            '/internal/util/access-details.html',
                            params={'api_key': os.environ.get(
                                                'CROWDFIRE_INTERNAL_API_KEY',
                                                ''),
                                    'service': os.environ.get('SERVICE', ''),
                                    'authUid': authUid})
    json_response = response.json()
    if json_response.get('code', 0) == 604:
        raise ValueError("No credentials retrieved for authUid " +
                         str(authUid) +
                         " from Crowdfire's internal access_details API")
    d = {'oauth_token': helpers.decrypt(json_response.get('access_token',
                                                          None)),
         'oauth_token_secret': helpers.decrypt(
                                 json_response.get('access_secret', None)),
         'app_key': os.environ.get('TWITTER_APP_KEY', ''),
         'app_secret': os.environ.get('TWITTER_APP_SECRET', '')}
    return d


def make_twython(authUid):
    """Makes a twython object with given authUid as authenticating user
        Raises ValueError if credentials for given authUid not available.
    """
    return Twython(**get_credentials(authUid))


class TwitterUser:
    '''Class to fetch data of one twitter user
    '''
    def __init__(self, logger_name="TwitterUserLogger",
                 log_filename="TwitterUser.log"):
        """Create a TwitterHandle for given oauth_token and oauth_token_secret
        """
        # Set up logger
        self.log_dir = os.path.join(os.getcwd(), 'logs')
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        self.log_path = os.path.join(self.log_dir, log_filename)
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)
        self.logFormatter = logging.Formatter('%(asctime)s - %(name)s - \
        %(levelname)s - %(message)s')
        self.logHandler = logging.FileHandler(filename=self.log_path, mode='a')
        self.logHandler.setLevel(logging.INFO)
        self.logHandler.setFormatter(self.logFormatter)
        self.logger.addHandler(self.logHandler)

        # Start logging
        self.logger.info("\n\nTwitterUser Logs .........\n")

        # Set up timeline request session
        self.timeline_session_start_time = datetime.datetime.now()
        self.timeline_session_end_time = self.timeline_session_start_time + \
            datetime.timedelta(minutes=SESSION_DURATION_MINUTES)
        self.timeline_request_count = 0

        # Set up follower_ids request session
        self.follower_ids_session_start_time = datetime.datetime.now()
        self.follower_ids_session_end_time = \
            self.follower_ids_session_start_time + \
            datetime.timedelta(minutes=SESSION_DURATION_MINUTES)
        self.follower_ids_request_count = 0

        # Set up counts for logging purpose
        self.tweet_per_follower_count = 0
        self.timeline_request_record = 0
        self.follower_ids_request_record = 0

    def fetch_timeline(self, authUid, **kwargs):
        """Fetches list of tweets from user-timeline

            :Returns: [list] list of dicts of tweet objects
            :param authUid: [long]
                user_id of twitter user whose timeline is to be fetched

            :param twitter_handle: [Twython]
                a valid authenticated Twython object
                :default: create handle for authUid using credentials in
                            Crowdfire Access Details

            :param user_id: [long]
                user_id of twitter user whose timeline is to be fetched
                :default: authUid

            :param count: [int]
                number of tweets
                :default: 200

            :param trim_user: [boolean]
                Twitter API trim_user option
                :default: True

            :param exclude_replies: [boolean]
                Twitter API exclude_replies option
                :default: False

            :param include_rts: [boolean]
                Twitter API include_rts option
                :default: True

            :param since_id: [long]
                Twitter API since_id option. give priority to max_id
                :default: None

            :param max_id: [long]
                Twitter API max_id option. has priority over since_id
                :default: None
        """
        twitter_handle = kwargs.get('twitter_handle', None)
        if not twitter_handle:
            twitter_handle = make_twython(authUid)
        user_id = kwargs.get('user_id', authUid)
        count = kwargs.get('count', 200)
        trim_user = kwargs.get('trim_user', True)
        exclude_replies = kwargs.get('exclude_replies', False)
        include_rts = kwargs.get('include_rts', True)
        since_id = kwargs.get('since_id', None)
        max_id = kwargs.get('max_id', None)

        if datetime.datetime.now() >= self.timeline_session_end_time:
                self.timeline_session_start_time = datetime.datetime.now()
                self.timeline_session_end_time = \
                    self.timeline_session_start_time + \
                    datetime.timedelta(minutes=SESSION_DURATION_MINUTES)
                self.timeline_request_count = 0
        elif self.timeline_request_count >= SESSION_TIMELINE_REQUEST_LIMIT:
            sleep_time = (self.timeline_session_end_time -
                          datetime.datetime.now()).total_seconds() + 60
            self.logger.info("Sleeping in fetch_timeline for " +
                             str(sleep_time) + " seconds" +
                             "\n\tsession_timeline_reqs: " +
                             str(self.timeline_request_count) +
                             "\n\ttotal_timeline_reqs: " +
                             str(self.timeline_request_record) +
                             "\n\tsession_follower_ids_reqs: " +
                             str(self.follower_ids_request_count) +
                             "\n\ttotal_follower_ids_reqs: " +
                             str(self.follower_ids_request_record))
            # time.sleep(sleep_time)
            # return self.fetch_timeline(authUid, **kwargs)
        self.timeline_request_count += 1
        self.timeline_request_record += 1
        status_word = 'SUCCESS'
        try:
            if max_id:
                tweet_list = twitter_handle.get_user_timeline(
                                user_id=user_id,
                                count=count,
                                trim_user=trim_user,
                                exclude_replies=exclude_replies,
                                include_rts=include_rts,
                                max_id=max_id)
            elif since_id:
                tweet_list = twitter_handle.get_user_timeline(
                                user_id=user_id,
                                count=count,
                                trim_user=trim_user,
                                exclude_replies=exclude_replies,
                                include_rts=include_rts,
                                since_id=since_id)
            else:
                tweet_list = twitter_handle.get_user_timeline(
                                user_id=user_id,
                                count=count,
                                trim_user=trim_user,
                                exclude_replies=exclude_replies,
                                include_rts=include_rts)
        except TwythonAuthError as tae:
            self.logger.warning(tae.message + str(kwargs),
                                exc_info=True,
                                extra=kwargs)
            tweet_list = []
            status_word = 'TwythonAuthError'
        except TwythonRateLimitError as trle:
            self.logger.warning(trle.message + str(kwargs),
                                exc_info=True,
                                extra=kwargs)
            sleep_time = SESSION_DURATION_MINUTES * 60
            self.logger.info("Unexpected Rate Limit Occured.\
                             Sleeping in fetch_timeline for " +
                             str(sleep_time) + " seconds" +
                             "\n\tsession_timeline_reqs: " +
                             str(self.timeline_request_count) +
                             "\n\ttotal_timeline_reqs: " +
                             str(self.timeline_request_record) +
                             "\n\tsession_follower_ids_reqs: " +
                             str(self.follower_ids_request_count) +
                             "\n\ttotal_follower_ids_reqs: " +
                             str(self.follower_ids_request_record))
            # time.sleep(sleep_time)
            tweet_list = []
            status_word = 'TwythonRateLimitError'
        if tweet_list:
            self.logger.info(str(len(tweet_list)) + "Tweets from id:" +
                             str(tweet_list[-1].get('id')) + " through id:" +
                             str(tweet_list[0].get('id')) + " fetched.")
        return tweet_list, status_word

    def fetching_stint(self, authUid, timeline, save_to_es=True, **kwargs):
        """Mediator function to fetch max 200 tweets for given **kwargs
            :Returns:
            * on success: [long]
                tweet_id of oldest tweet from tweet_list returned by
                fetch_timeline.

            * on failure: [int] -1 when empty list/None is recieved.

            :param authUid: [long]
                user_id of twitter user whose timeline is to be fetched

            :param **kwargs:
                Same as *def fetch_timeline(self, authUid, **kwargs)*
        """
        tweet_list, status_word = self.fetch_timeline(authUid, **kwargs)
        if tweet_list:
            for tweet in tweet_list:
                tweet = helpers.purge_key_deep(tweet, 'media')
                tweet = helpers.purge_key_deep(tweet, 'urls')
                tweet = helpers.purge_key_deep(tweet, 'url')
                timeline.append(tweet)
                if save_to_es:
                    self.save_tweet(tweet)
            return tweet_list[-1].get('id', 0)
        elif status_word == 'TwythonAuthError':
            return -2
        elif status_word == 'TwythonRateLimitError':
            return -3
        return -1

    def request_timeline(self, authUid, save_to_es=True, **kwargs):
        '''Requests timeline of this user with options given in **kwargs
            :param authUid:
                authUid of user whose timeline is to be fetched

            :param save_to_es:
                Flag when set true, data fetched is saved in elasticsearch for
                future usage
                :default: True

            :param **kwargs:
                Same as *def fetch_timeline(self, authUid, **kwargs)*

            Raises ValueError if credentials for given authUid not available.
        '''
        kwargs['twitter_handle'] = \
            kwargs.get('twitter_handle', make_twython(authUid))
        count = kwargs.get('count', 200)
        timeline = []
        begin_time = datetime.datetime.now()
        while count:
            if count > 200:
                kwargs['count'] = 200
            else:
                kwargs['count'] = count
            max_id = self.fetching_stint(authUid,
                                         timeline,
                                         save_to_es,
                                         **kwargs)
            if max_id == kwargs.get('max_id', 1):
                return timeline
            elif max_id == -1:
                return timeline
            else:
                kwargs['max_id'] = max_id
                if count > 200:
                    count -= 200
                else:
                    count = 0
        finish_time = datetime.datetime.now()
        self.logger.info("Gathered timeline for authUid: " +
                         str(authUid) + ":" + str(len(timeline)) +
                         " tweets in " +
                         str((finish_time - begin_time).total_seconds()) +
                         " seconds")
        return timeline

    def save_tweet(self, tweet_dict):
        """Saves one tweet object to ES in the index of name
            tweet-index-<YEAR>-<#WEEK>
        """
        INDEX_NAME = es.get_tweet_index()
        time_str = tweet_dict.get('created_at', '')
        if time_str:
            tweet_dict['created_at'] = datetime.datetime.strptime(
                                        time_str,
                                        "%a %b %d %H:%M:%S +0000 %Y")
        else:
            tweet_dict['created_at'] = None

        tweet_dict.update({u'_id': tweet_dict.get(u'id', "00000"),
                           u'_index': INDEX_NAME})
        tweet = es.Tweet(**tweet_dict)
        res = None
        try:
            res = tweet.save()
            self.tweet_per_follower_count += 1
        except:
            print "Elasticsearch unreachable. Can't save tweet. tweet_id:",\
                    tweet_dict['_id']
        if res:
            self.logger.info(" Success: tweet #" +
                             str(self.tweet_per_follower_count) +
                             " for user_id: " +
                             str(tweet_dict['user']['id']) +
                             " saved in index: " +
                             INDEX_NAME +
                             " tweet_id: " + str(tweet_dict['id']))
        else:
            self.logger.error(" Failure: tweet #" +
                              str(self.tweet_per_follower_count) +
                              " for user_id: " +
                              str(tweet_dict['user']['id']) +
                              " not saved in index: " +
                              INDEX_NAME +
                              " tweet_id: " + str(tweet_dict['id']))

    def list_follower_ids(self, authUid, **kwargs):
        """Return a list of ids of all followers of user specified by
           user_id or screen_name keyword_args.
           If user_id is valid, screen_name is ignored.
           If both are invalid, raises ValueError
           :param user_id: (optional) user_id of target user
           :param screen_name: (optional) screen_name of target user
           :param count: (optional) #followers to fetch ids of.
        """
        followers_ids = []
        next_cursor = -1

        while next_cursor:
            if datetime.datetime.now() >= self.follower_ids_session_end_time:
                self.follower_ids_session_start_time = datetime.datetime.now()
                self.follower_ids_session_end_time = \
                    self.follower_ids_session_start_time + \
                    datetime.timedelta(minutes=SESSION_DURATION_MINUTES)
                self.follower_ids_request_count = 0
            elif self.follower_ids_request_count >= \
                    SESSION_FOLLOWER_IDS_REQUEST_LIMIT:
                sleep_time = (self.follower_ids_session_end_time -
                              datetime.datetime.now()).total_seconds() + 60
                self.logger.info("Sleeping in def list_follower_ids for " +
                                 str(sleep_time) +
                                 " seconds" +
                                 "\n\tsession_timeline_reqs: " +
                                 str(self.timeline_request_count) +
                                 "\n\ttotal_timeline_reqs: " +
                                 str(self.timeline_request_record) +
                                 "\n\tsession_follower_ids_reqs: " +
                                 str(self.follower_ids_request_count) +
                                 "\n\ttotal_follower_ids_reqs: " +
                                 str(self.follower_ids_request_record))
                # time.sleep(sleep_time)
                continue
            self.follower_ids_request_count += 1
            self.follower_ids_request_record += 1
            try:
                tw = kwargs.get('twitter_handle', make_twython(authUid))
                res_dict = tw.get_followers_ids(
                                        user_id=kwargs.get(
                                            'user_id', authUid),
                                        screen_name=kwargs.get(
                                            'screen_name', None),
                                        stringify_ids=False,
                                        count=kwargs.get('count', 5000),
                                        cursor=next_cursor)
                next_cursor = res_dict['next_cursor']
                followers_ids += res_dict['ids']
            except TwythonRateLimitError as trle:
                self.logger.error(trle.message + str(kwargs),
                                  exc_info=True,
                                  extra=kwargs)
                continue
            except TwythonError as te:
                self.logger.error(te.message + str(kwargs),
                                  exc_info=True,
                                  extra=kwargs)
        followers_ids = list(set(followers_ids))
        return followers_ids

    def fetch_follower_timelines(self,
                                 authUid,
                                 followers_count=5000,
                                 tweets_count=3000):
        """Extracts and saves to ES the tweet objects from timelines of
            followers of a user
            :param authUid: [long] user_id of target user
            :param followers_count: [long] #followers
            :param tweets_count: [long] #tweets to fetch per follower
        """
        tw = make_twython(authUid)
        user_id_list = self.list_follower_ids(authUid,
                                              **{'user_id': authUid,
                                                 'count': followers_count,
                                                 'twitter_handle': tw})
        self.logger.info("List of " + str(len(user_id_list)) +
                         " followers fetched for user_id: " +
                         str(authUid))
        for follower_id in user_id_list:
            self.tweet_per_follower_count = 0
            self.request_timeline(authUid=authUid,
                                  user_id=follower_id,
                                  count=tweets_count,
                                  twitter_handle=tw)
            self.logger.info("follower #" +
                             str(user_id_list.index(follower_id) + 1) +
                             " timeline fetched. follower_id: " +
                             str(follower_id) +
                             " #tweets: " +
                             str(self.tweet_per_follower_count))
