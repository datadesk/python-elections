#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests out python-elections

Most requests require authentication with, so you'll need to provide that in
a file called private_settings.py
"""
import os
import unittest
from elections import AP
from elections.objects import Candidate, Race, ReportingUnit
from private_settings import AP_USERNAME, AP_PASSWORD

#
# Tests
#

class BaseTest(unittest.TestCase):
    
    def setUp(self):
        self.client = AP(AP_USERNAME, AP_PASSWORD)
        self.iowa = self.client.get_state("IA")


class StateTest(BaseTest):
    
    def test_attrs(self):
        # Races
        obj_list = self.iowa.races
        self.assertEqual(type(obj_list), type([]))
        self.assertEqual(len(obj_list) > 0, True)
        self.assertEqual(type(obj_list[0]), Race)

#        # Candidates
#        obj_list = self.iowa.candidates
#        self.assertEqual(type(obj_list), type([]))
#        self.assertEqual(len(obj_list) > 0, True)
#        self.assertEqual(type(obj_list[0]), Candidate)
#        # Reporting units
#        obj_list = self.iowa.reporting_units
#        self.assertEqual(type(obj_list), type([]))
#        self.assertEqual(len(obj_list) > 0, True)
#        self.assertEqual(type(obj_list[0]), ReportingUnit)
#        # Counties
#        obj_list = self.iowa.counties
#        self.assertEqual(type(obj_list), type([]))
#        self.assertEqual(len(obj_list) == 99, True)
#        self.assertEqual(type(obj_list[0]), ReportingUnit)



if __name__ == '__main__':
    unittest.main()

