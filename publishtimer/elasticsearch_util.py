# -*- coding: utf-8 -*-
"""
Created on Tue Mar 29 14:44:23 2016

@author: Parag Guruji, paragguruji@gmail.com
"""

import os
import datetime
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl import DocType, Date, String
from elasticsearch.connection.http_urllib3 import ConnectionTimeout


CLIENT  = connections.create_connection(hosts=[os.environ['ES_HOST']], 
                                        timeout=int(os.environ['ES_TIMEOUT']))

def get_es_client(enforce_new=False):
    """Returns the singleton Elasticsearch-client object connected to ES server specified by environment variable ES_HOST with default timeout specified by environment variable ES_TIMEOUT
    """
    global CLIENT
    if enforce_new or not CLIENT:
        CLIENT = connections.create_connection(hosts=[os.environ['ES_HOST']], 
                                               timeout=os.environ['ES_TIMEOUT'])
    return CLIENT
    

def get_tweet_index():
    """Generates ES index name for tweet object from current time as tweet-index-<YEAR>-<#WEEK>
    """
    return 'tweets-index-' + \
        '-'.join([str(l) for l in list(datetime.date.isocalendar(
                                        datetime.datetime.now()))][:2])

class Tweet(DocType):
    """DocType for saving a tweet in ES
    """
    saved_at = Date()
    outdated = String()
        

    def save(self, **kwargs):
        """Saves this document to given index into the ES
        """
        self.saved_at = datetime.datetime.now()        
        self.outdated = "No"
        try:
            return super(Tweet, self).save(**kwargs)
        except ConnectionTimeout as ct:
            raw_input("ConnectionTimeout with Elasticsearch." + str(ct) +\
            "\nFix it and then continue.")
            self.save(**kwargs)
