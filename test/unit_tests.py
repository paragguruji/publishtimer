# -*- coding: utf-8 -*-
"""
Created on Sat Apr  2 09:31:14 2016

@author: Parag Guruji, paragguruji@gmail.com
"""

from multiprocessing import Process
from test.context import api, core, elasticsearch_util
import requests
import unittest
import os
import json
import time
from elasticsearch.exceptions import ConnectionError


class ApiUnitTests(unittest.TestCase):
    """Test cases for module publishtimer.api"""
        
    def run_app(self):   
        """runs the app on server specified by environment variable *SERVER_NAME*
        """
        api.initiate()


    def validate_response(self, response):
        """:Returns: **True** if response OK, **False** otherwise
        """
        if isinstance(response, requests.models.Response) and \
                                response.status_code==200:
            return True
        return False


    def test_ping(self):
        """Tests ping function of api
            URL: 'http://<SERVER_NAME>/ping'
            
        """
        server = Process(target=self.run_app)
        server.start()
        time.sleep(5)
        request_url = 'http://'+ os.environ['SERVER_NAME'] + '/ping'
        response = requests.get(url=request_url)
        self.assertEqual("pong", response.text, 
                         msg="Ping failed for URL:"+str(request_url))
        server.terminate()
        server.join()
        
        
    def test_publish_schedule(self):
        """Tests if publishschedule request works (side-effect testing for ES excluded)
        
            :URL: 'http://<SERVER_NAME>/api/v1.0/publishschedule'
            :Data: {'authUid': u'19900726-tw'}
            
        """
        server = Process(target=self.run_app)
        server.start()
        time.sleep(5)
        request_url =   'http://' + os.environ['SERVER_NAME'] + \
                        '/api/v1.0/publishschedule'
        response = requests.put(url=request_url, json={'authUid': u'19900726-tw'})
        self.assertTrue(self.validate_response(response), 
                        msg="publish_schedule response Not OK:\nStatus Code: " + \
                            str(response.status_code) + \
                            "\nJSON: " + json.dumps(response.json()))
        server.terminate()
        server.join()
        
 
class CoreUnitTests(unittest.TestCase):
    """Test cases for module publishtimer.core"""
        
    def test_get_data_on_fly(self):
        """tests function get_data_on_fly
        
            :Signature: get_data_on_fly(authUid, save=True, **kwargs)     
            :Data: authUid = u'19900726', save = False, kwargs={'count' = 220}
            
        """
        authUid = u'19900726' 
        save = False
        kwargs = {'count': 220}
        result = core.get_data_on_fly(authUid, save, **kwargs)
        self.assertIsInstance(result, dict)
        self.assertIn('twitter_id', result)
        self.assertIn('data', result)
        self.assertIsInstance(result.get('data', None), list)
        self.assertEqual(len(result['data']), 220)
        self.assertIsInstance(result['data'][1], dict)
        self.assertIn('created_at', result['data'][2])
    
    
    def test_get_data_from_es(self):
        """tests function get_data_from_es
        
            :Signature: get_data_from_es(authUid)
            :Data: authUid = u'19900726'
            
        """
        authUid = u'19900726' 
        try:
            result = core.get_data_from_es(authUid)
            self.assertIsInstance(result, dict)
            self.assertIn('twitter_id', result)
            self.assertIn('data', result)
            self.assertIsInstance(result.get('data', None), list)
            #self.assertEqual(len(result['data']), 2981)
            self.assertIsInstance(result['data'][1], dict)
            self.assertIn('created_at', result['data'][2])
        except Exception as ex:
            self.assertIsInstance(ex, ConnectionError)
    
    
    def test_prepare_data(self):
        """tests function prepare_data
        
            :Signature: prepare_data(authUid, use_es=True, use_tw=True, save_on_fly=True, **kwargs)
            :Data: authUid = u'19900726', use_es = True, use_tw = False
            
        """
        authUid = u'19900726' 
        use_es = True 
        use_tw = False
        result = core.prepare_data(authUid, use_es=use_es, use_tw=use_tw)
        self.assertIsInstance(result, dict)
        self.assertIn('twitter_id', result)
        self.assertIn('data_frame', result)
        self.assertIsInstance(result.get('data_frame', None), 
                              core.pd.DataFrame)
        self.assertFalse(result.get('data_frame', core.pd.DataFrame()).empty, 
                         msg="data_frame received is empty one")
        print result.get('data_frame', core.pd.DataFrame()).index
        print result.get('data_frame', core.pd.DataFrame()).columns
        self.assertEqual(7, 
                         len(result.get(
                                 'data_frame', core.pd.DataFrame()).columns))
        ind = core.pd.core.index.Index([u'day', 
                                        u'engagement', 
                                        u'favorite_count', 
                                        u'hour', 
                                        u'id', 
                                        u'minute', 
                                        u'retweet_count'], dtype='object')
        self.assertTrue(all(result['data_frame'].columns == ind))
        
        
    def test_compute_times_with_no_data(self):
        """tests function compute_times with no data
        
            :Signature: compute_times(data_dict)
            :Data: data_dict = {'twitter_id': u'19900726', 'data_frame': core.pd.DataFrame()}
            
        """
        data_dict = {'twitter_id': u'19900726', 
                     'data_frame': core.pd.DataFrame()}        
        result = core.compute_times(data_dict)
        self.assertDictEqual(result, {'authUid': u'19900726-tw', 
                                      'completeSchedule': [],
                                      'source': 'internal'})
                                      
                                      
    def test_compute_times_with_data(self):
        """testing compute_times with data
        
            :Signature: compute_times(data_dict)
            :Data: data_dict = {'twitter_id': '19900726', 
                                'data_frame': <pandas.Dataframe initiated with JSON loaded from test_data_file>}            
            :test_data_file = test/data/test_data_timeline_authUid19900726.list
            :test_result_file = test/data/test_compute_times_result_authUid19900726.dict
            
        """
        test_data_file = "test/data/test_data_timeline_authUid19900726.list"
        test_result_file = \
            "test/data/test_compute_times_result_authUid19900726.dict"
        data_dict = {'twitter_id': '19900726', 
                     'data_frame': core.pd.DataFrame(
                                     json.load(open(test_data_file)))}
        expected_result = json.load(open(test_result_file))     
        computed_result = core.compute_times(data_dict)
        self.assertDictEqual(expected_result, computed_result)
        
        
    def test_fill_incomplete_schedule(self):
        """tests function fill_incomplete_schedule
        
            :Signature: fill_incomplete_schedule(incomplete_schedule)
            :Data: incomplete_schedule: <JSON loaded from incomplete_schedule_file>
            :sample incomplete schedule file = test/data/test_incomplete_schedule.dict
            :sample completed schedule file = test/data/test_completed_schedule.dict
            
        """
        incomplete_schedule_file = "test/data/test_incomplete_schedule.dict"
        completed_schedule_file = "test/data/test_completed_schedule.dict"
        incompplete_schedule = json.load(open(incomplete_schedule_file))
        completed_schedule = json.load(open(completed_schedule_file))
        self.assertDictEqual(completed_schedule, 
                             core.fill_incomplete_schedule(\
                                 incompplete_schedule))
    
    
    def test_write_schedule(self):
        """tests function write_schedule
        
            :Signature: write_schedule(schedule)
            :Data: schedule: <JSON loaded from schedule file>
            :schedule_file = test/data/test_completed_schedule.dict
            
        """
        schedule_file = "test/data/test_completed_schedule.dict"
        schedule = json.load(open(schedule_file))
        result = core.write_schedule(schedule)
        self.assertIsInstance(result, dict)
        self.assertIn('response_from_save_schedule_api', result)
        self.assertIsInstance(result['response_from_save_schedule_api'], dict)
        self.assertIn('schedule_prepared', result)
        self.assertDictEqual(result.get('schedule_prepared', {}), schedule)
        

class ElasticsearchUnitTests(unittest.TestCase):
    """Test cases for module publishtimer.elasticsearch_util"""
        
    def test_es_connection(self):
        """tests if ES server is alive and reachable
                    
        """
        flag = False
        msg = "Connection working, but not cluster"
        try:
            cli = elasticsearch_util.get_es_client()
            flag = cli.ping()
        except ConnectionError as ce:
            msg = "Connection Error: " + str(ce.info)
        self.assertTrue(flag, msg=msg)
        

        
if __name__ == '__main__':    
    unittest.main()