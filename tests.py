#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests out python-elections

Most requests require authentication with, so you'll need to provide that in
a file called private_settings.py
"""
import os
import unittest
from ap import APResults
from ap.objects import Candidate
from private_settings import AP_USERNAME, AP_PASSWORD

#
# Tests
#

class BaseTest(unittest.TestCase):
    
    def setUp(self):
        self.client = APResults('IA', AP_USERNAME, AP_PASSWORD)


class DocumentSearchTest(BaseTest):
    
    def test_get_candidates(self):
        obj_list = self.client.get_candidates()
        self.assertEqual(type(obj_list), type([]))
        self.assertEqual(len(obj_list) > 0, True)
        self.assertEqual(type(obj_list[0]), Candidate)
   

if __name__ == '__main__':
    unittest.main()

