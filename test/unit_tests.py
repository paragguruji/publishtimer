# -*- coding: utf-8 -*-
"""
Created on Sat Apr  2 09:31:14 2016

@author: Parag Guruji, paragguruji@gmail.com
"""

from multiprocessing import Process
from test.context import api, core
import requests
import unittest
import os
import json
import time


class ApiUnitTests(unittest.TestCase):
    """Test cases for module publishtimer.api"""
        
    def run_app(self):   
        """runs the app on self.base_url"""
        host = os.environ['SERVER_NAME'].split(':')[0]
        port = int(os.environ['SERVER_NAME'].split(':')[1])
        api.app.run(host=host, port=port)


    def validate_response(self, response):
        """validate response by checking all possibilities"""
        if isinstance(response, requests.models.Response) and \
                                response.status_code==200:
            return True
        return False


    def test_ping(self):
        """Tests ping function of api
            URL: 'http://'+os.environ['SERVER_NAME']+'/ping'
        """
        server = Process(target=self.run_app)
        server.start()
        time.sleep(5)
        #print os.environ['SERVER_NAME']
        request_url = 'http://'+ os.environ['SERVER_NAME'] + '/ping'
        response = requests.get(url="http://localhost:5001/ping")
        self.assertEqual("pong", response.text, 
                         msg="Ping failed for URL:"+str(request_url))
        server.terminate()
        server.join()
        
        
    def test_publish_schedule(self):
        """Tests if publishschedule request works
            URL: 'http://' + os.environ['SERVER_NAME'] + '/api/v1.0/publishschedule'
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
        """testing get_data_on_fly
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
        """testing get_data_from_es
        """
        authUid = u'19900726' 
        result = core.get_data_from_es(authUid)
        self.assertIsInstance(result, dict)
        self.assertIn('twitter_id', result)
        self.assertIn('data', result)
        self.assertIsInstance(result.get('data', None), list)
        #self.assertEqual(len(result['data']), 2981)
        self.assertIsInstance(result['data'][1], dict)
        self.assertIn('created_at', result['data'][2])
    
    
    def test_prepare_data(self):
        """testing prepare_data
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
        ind = core.pd.core.index.Index([u'day', 
                                        u'engagement', 
                                        u'favorite_count', 
                                        u'hour', 
                                        u'id', 
                                        u'minute', 
                                        u'retweet_count'], dtype='object')
        self.assertTrue(all(result['data_frame'].columns == ind))
        
        
    def test_compute_times_with_no_data(self):
        """testing compute_times_with_no_data
        """
        data_dict = {'twitter_id': u'19900726', 
                     'data_frame': core.pd.DataFrame()}        
        result = core.compute_times(data_dict)
        self.assertDictEqual(result, {'authUid': u'19900726-tw', 
                                      'completeSchedule': [],
                                      'source': 'internal'})
                                      
                                      
    def test_compute_times_with_data(self):
        """testing compute_times_with_data
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
        """testing fill_incomplete_schedule
        """
        incomplete_schedule_file = "test/data/test_incomplete_schedule.dict"
        completed_schedule_file = "test/data/test_completed_schedule.dict"
        incompplete_schedule = json.load(open(incomplete_schedule_file))
        completed_schedule = json.load(open(completed_schedule_file))
        self.assertDictEqual(completed_schedule, 
                             core.fill_incomplete_schedule(\
                                 incompplete_schedule))
    
    
    def test_write_schedule(self):
        """testing write_schedule
        """
        schedule_file = "test/data/test_completed_schedule.dict"
        schedule = json.load(open(schedule_file))
        result = core.write_schedule(schedule)
        self.assertIsInstance(result, dict)
        self.assertIn('response_from_save_schedule_api', result)
        self.assertIsInstance(result['response_from_save_schedule_api'], dict)
        self.assertIn('schedule_prepared', result)
        self.assertDictEqual(result.get('schedule_prepared', {}), schedule)
        
        
if __name__ == '__main__':    
    unittest.main()