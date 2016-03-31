# -*- coding: utf-8 -*-
"""
Created on Mon Mar 28 13:06:02 2016

@author: Parag Guruji, paragguruji@gmail.com
"""

import os
import json
import time
import datetime
import requests
import pandas as pd
import boto.sqs
from dateutil import parser
from publishtimer import twitter_data as td
from publishtimer import elasticsearch_util as es


DAY_MAP = {0:'mon', 1:'tue', 2:'wed', 3:'thu', 4:'fri', 5:'sat', 6:'sun'}
queue = boto.connect_sqs().get_queue(os.environ['CALCULATION_QUEUE_NAME'])
default_schedule = [    '18:00', '10:45', '17:15', '11:40', '22:10', 
                        '09:50', '20:20', '08:55', '21:15', '19:25',
                        '12:00', '23:05', '07:05', '16:10', '13:35', 
                        '06:50', '14:55', '05:20', '15:30', '00:30',
                        '01:10', '10:20', '17:45', '11:15', '22:30', 
                        '09:35', '20:40', '08:25', '21:50', '19:05',
                        '18:35', '02:15', '15:05', '04:45', '13:15', 
                        '03:25', '16:40', '14:20', '23:35', '12:25',
                        '19:45', '21:30', '08:15', '20:55', '09:10', 
                        '22:45', '11:50', '17:25', '10:00', '18:55']

    
def get_data_on_fly(authUid, save=True, **kwargs):
    """Get twitter timeline for given user on fly (w/o ES)
    """
    ret = {'twitter_id': authUid, 'data': []}
    tw = td.TwitterUser()
    tweets = tw.request_timeline(authUid, save_to_es=save, **kwargs)
    ret['data'] = [{'created_at':   str(datetime.datetime.strptime(\
                                            t.get('created_at', ''), 
                                            "%a %b %d %H:%M:%S +0000 %Y"))
                                        if isinstance(t.get('created_at', ''), 
                                                      str)
                                        else str(t.get('created_at', None)),
                        'favorite_count': t['favorite_count'], \
                        'retweet_count': t['retweet_count'], \
                        'id': t['id']   } for t in tweets]
    return ret


def get_data_from_es(authUid):
    """Get twitter timeline for given user from ES
    """
    search_body =   { 
                        "filter" :
                            { 
                                "term" :
                                    {
                                        "user.id" : authUid
                                    }
                            },
                        "fields" : 
                            [
                                'id', 
                                'created_at', 
                                'retweet_count',
                                'favorite_count'
                            ],
                        "size" : 1
                    }
    res = es.get_es_client().search(index='_all', \
                                    doc_type='tweet', \
                                    body=search_body )
    cnt = res['hits']['total']
    if not cnt:
        return {'twitter_id': authUid, 'data': []}
    else:
        data = []
        search_body["size"] = cnt
        res = es.get_es_client().search(index='_all', \
                                        doc_type='tweet', \
                                        body=search_body )
        for i in range(len(res['hits']['hits'])):
            for k in res['hits']['hits'][i]['fields'].keys():
                res['hits']['hits'][i]['fields'][k] \
                = res['hits']['hits'][i]['fields'][k][0]
            data.append(res['hits']['hits'][i]['fields'])
        return {'twitter_id': authUid, 'data': data}
            

def prepare_data(authUid, 
                 use_es=True, 
                 use_tw=True, 
                 save_on_fly=True, 
                 **kwargs):
    """Retreive twitter data from ES or Twitter-API and transform to a form consumable by *compute_times*
    """
    if isinstance(authUid, str):
        authUid = authUid.decode('utf-8')
    if isinstance(authUid, unicode) and authUid.endswith(u'-tw'):
        authUid = long(authUid[:-3])
    data_dict = {'twitter_id': authUid, 'data': []}
    if use_es:
        data_dict = get_data_from_es(authUid)
    if use_tw and not data_dict['data']:
        data_dict = get_data_on_fly(authUid, save=save_on_fly, **kwargs)
    if data_dict['data']:
        for i in range(len(data_dict['data'])):
            d = parser.parse(data_dict['data'][i].pop('created_at'))
            data_dict['data'][i]['day'] = d.weekday()
            data_dict['data'][i]['hour'] = d.hour
            data_dict['data'][i]['minute'] = d.minute
            data_dict['data'][i]['engagement'] \
            = data_dict['data'][i].get('retweet_count', 0) \
            + data_dict['data'][i].get('favorite_count', 0) * 100
    return {'twitter_id': data_dict['twitter_id'], \
            'data_frame': pd.DataFrame(data_dict['data'])}


def compute_times(data_dict):
    """Compute the list of best times from given data
    """
    out_dict = {'authUid': data_dict['twitter_id'], 
                'completeSchedule': [],
                'source': 'internal'}
    df = data_dict['data_frame']
    if df.empty:
        return out_dict
    cols_to_norm = ['engagement']
    df[cols_to_norm] = df[cols_to_norm].apply(lambda x: x/(x.max() - x.min()))
    df_daywise = [df[(df.day==i)][[ 'day', \
                                    'hour', \
                                    'minute', \
                                    'engagement' ]] for i in range(7)]
    for df_i in df_daywise:
        response_dict = {}
        df_i['rank'] = df_i.engagement.rank(method='first', ascending=False)
        d = df_i.sort_values(by='rank').loc[df_i['rank'].isin(range(1, 51))]
        dt = d.T
        if not dt.empty:
            response_dict["day"] = DAY_MAP[dt[d.index[0]].day.astype(int)]
            response_dict["times"] = ['{}:{}'.format(dt[i].hour.astype(int), \
                                                    dt[i].minute.astype(int)) \
                                    for i in d.index]
            out_dict['completeSchedule'].append(response_dict)
    return out_dict
    

def write_schedule(schedule):
    #schedule[''] = 
    for day in DAY_MAP.values():
        if day not in [item['day'] for item in schedule['completeSchedule']]:
            schedule['completeSchedule'].append({   'day': day, 
                                                    'times': default_schedule})
    for item in schedule['completeSchedule']:
        available_len = len(item['times'])
        if available_len < 50:
            item['times']+=[t for t in default_schedule 
                                if t not in item['times']][:50-available_len]
    
    response = requests.put(url=os.environ.get('SAVE_SCHEDULE_URL', ''), 
                              data=schedule)
    return response


def work_once_with_sqs():
    results = queue.get_messages()        
    for msg in results:
        write_schedule(
            compute_times(
                prepare_data(
                    json.loads(
                        msg.get_body())['authUid'])))


def work_once(**params):
    data = prepare_data(**params)
    schedule = compute_times(data)
    return write_schedule(schedule)


def work(interval=30):
    while True:    
        work_once()
        time.sleep(interval)


if __name__=='__main__':
    work()