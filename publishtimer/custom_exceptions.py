# -*- coding: utf-8 -*-
"""
Created on Wed Apr 27 19:05:53 2016

@author: Parag Guruji, paragguruji@gmail.com
"""

from werkzeug.exceptions import HTTPException

class WriteScheduleFailedError(HTTPException):
    """Exception to be raised when schedule is computed successfully by the publishtimer but save_schedule API returns failure response.
        The response includes error code and reason as returned by the save_schedule API and the schedule computed by publishtimer
    """
    def __init__(self, **kwargs):
        self.code = 512
        self.upstream_response = kwargs.get('upstream_response')
        self.computed_schedule = kwargs.get('computed_schedule', [])
        self.description = 'Error in writing computed schedule to profile \
because request to WriteSchedule API failed with error code: ' + \
        str(self.upstream_response.status_code) + '; reason: ' + \
        str(self.upstream_response.reason)
        super(WriteScheduleFailedError, 
              self).__init__(description=self.description, 
                             response=self.upstream_response)
