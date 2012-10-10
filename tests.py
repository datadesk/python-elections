#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests out python-elections

Most requests require authentication with, so you'll need to provide that in
a file called private_settings.py with AP_USERNAME, AP_PASSWORD and TEST_STATE

These tests were written using the Los Angeles Times' login, which gives it state
level access for California and nationwide access elsewhere. If you have a different
access level, this will prove to be a problem. 

We need to work this out somehow. If you have any bright ideas let me know.
"""
import os
import unittest
from elections import AP
from datetime import date, datetime
from elections.ap import Nomination, StateDelegation
from elections.ap import Candidate, Race, ReportingUnit, Result, State
from elections.ap import FileDoesNotExistError, BadCredentialsError
from private_settings import AP_USERNAME, AP_PASSWORD, TEST_STATE


class BaseTest(unittest.TestCase):
    
    def setUp(self):
        self.client = AP(AP_USERNAME, AP_PASSWORD)


class APTest(BaseTest):
    
    def test_badlogin(self):
        client = AP("foo", "bar")
        self.assertRaises(BadCredentialsError, client.get_state, TEST_STATE)
    
    def test_badstate(self):
        self.assertRaises(FileDoesNotExistError, self.client.get_state, "XYZ")
    
    def test_county_aggregates(self):
        self.state = self.client.get_state(TEST_STATE)
        county_list = self.state.counties
        self.assertEqual(type(county_list), type([]))
        self.assertEqual(len(county_list) == 58, True)
        [self.assertEqual(type(i), ReportingUnit) for i in county_list]
        [self.assertEqual(i.is_state, False) for i in county_list]
    
    def test_state_reporting_unit(self):
        """
        Makes sure Wyoming only has one 'state'-identified RU.
        """
        self.state = self.client.get_state(TEST_STATE)
        self.assertEqual(type(self.state.races[0].state), ReportingUnit)
    
    def test_getstate(self):
        # Pull state
        self.state = self.client.get_state(TEST_STATE)
        
        # Races
        race_list = self.state.races
        self.assertTrue(isinstance(race_list, list))
        self.assertTrue(len(race_list) > 0)
        self.assertTrue(isinstance(race_list[0], Race))
        self.assertEqual(self.state.get_race(race_list[0].ap_race_number), race_list[0])
        self.assertRaises(KeyError, self.state.get_race, 'foo')
        race = self.state.races[0]
        self.assertTrue(isinstance(race.ap_race_number, basestring))
        self.assertTrue(isinstance(race.office_name, basestring))
        self.assertTrue(isinstance(race.office_description, basestring))
        self.assertTrue(isinstance(race.office_id, basestring))
        self.assertTrue(isinstance(race.seat_name, basestring))
        self.assertTrue(isinstance(race.seat_number, basestring))
        self.assertTrue(isinstance(race.scope, basestring))
        self.assertTrue(isinstance(race.date, date))
        self.assertTrue(isinstance(race.num_winners, int))
        self.assertTrue(isinstance(race.race_type, basestring))
        self.assertTrue(isinstance(race.party, basestring))
        self.assertTrue(isinstance(race.uncontested, bool))
        self.assertTrue(isinstance(race.name, basestring))
        self.assertTrue(isinstance(race.race_type_name, basestring))
        self.assertTrue(isinstance(race.is_primary, bool))
        self.assertTrue(isinstance(race.is_caucus, bool))
        self.assertTrue(isinstance(race.is_general, bool))
        
        # Reporting units
        ru_list = self.state.reporting_units
        self.assertTrue(isinstance(ru_list, list))
        self.assertTrue(len(ru_list) > 0)
        self.assertTrue(isinstance(ru_list[0], ReportingUnit))
        self.assertEqual(self.state.get_reporting_unit(ru_list[0].key), ru_list[0])
        self.assertRaises(KeyError, self.state.get_reporting_unit, 'foo')
        self.assertTrue(isinstance(ru_list[0], ReportingUnit))
        self.assertTrue(isinstance(ru_list[0].ap_number, basestring))
        self.assertTrue(isinstance(ru_list[0].name, basestring))
        self.assertTrue(isinstance(ru_list[0].abbrev, basestring))
        self.assertTrue(isinstance(ru_list[0].fips, basestring))
        self.assertTrue(isinstance(ru_list[0].num_reg_voters, int))
        self.assertTrue(isinstance(ru_list[0].precincts_total, int))
        self.assertTrue(isinstance(ru_list[0].precincts_reporting, type(None)))
        self.assertTrue(isinstance(ru_list[0].precincts_reporting_percent, type(None)))
        ru_list = self.state.races[0].reporting_units
        self.assertTrue(isinstance(ru_list, list))
        self.assertTrue(len(ru_list) > 0)
        for ru in ru_list:
            self.assertTrue(isinstance(ru, ReportingUnit))
            self.assertTrue(isinstance(ru.ap_number, basestring))
            self.assertTrue(isinstance(ru.name, basestring))
            self.assertTrue(isinstance(ru.abbrev, basestring))
            self.assertTrue(isinstance(ru.fips, basestring))
            self.assertTrue(isinstance(ru.num_reg_voters, int))
            self.assertTrue(isinstance(ru.precincts_total, (int,  type(None))))
            self.assertTrue(isinstance(ru.precincts_reporting, (int,  type(None))))
            self.assertTrue(isinstance(ru.precincts_reporting_percent, (float,  type(None))))
            if ru.results:
                self.assertTrue(isinstance(ru.results[0], Result))
            # Results
            for result in ru.results:
                self.assertTrue(isinstance(result, Result))
                self.assertTrue(isinstance(result.candidate, Candidate))
                self.assertEqual(result.reporting_unit, ru)
                self.assertTrue(isinstance(result.vote_total, int))
                try:
                    self.assertTrue(isinstance(result.vote_total_percent, float))
                except:
                    self.assertTrue(isinstance(result.vote_total_percent, type(None)))
        
        # Counties
        county_list = self.state.races[0].counties
        self.assertEqual(type(county_list), type([]))
        self.assertEqual(len(county_list) == 58, True)
        self.assertEqual(type(county_list[0]), ReportingUnit)
        self.assertEqual(county_list[0].is_state, False)
        
        # State
        state = self.state.races[0].state
        self.assertEqual(type(state), ReportingUnit)
        self.assertEqual(state.is_state, True)
        
        # Candidates
        cand_list = self.state.races[0].candidates
        self.assertTrue(isinstance(race.candidates, list))
        self.assertTrue(len(cand_list) > 0)
        for cand in cand_list:
            self.assertTrue(isinstance(cand, Candidate))
            self.assertTrue(isinstance(cand.first_name, basestring))
            self.assertTrue(isinstance(cand.middle_name, basestring))
            self.assertTrue(isinstance(cand.last_name, basestring))
            self.assertTrue(isinstance(cand.abbrev_name, basestring))
            self.assertTrue(isinstance(cand.suffix, basestring))
            self.assertTrue(isinstance(cand.use_suffix, bool))
            self.assertTrue(isinstance(cand.ap_natl_number, basestring))
            self.assertTrue(isinstance(cand.ap_polra_number, basestring))
            self.assertTrue(isinstance(cand.ap_pol_number, basestring))
            self.assertTrue(isinstance(cand.party, basestring))
            self.assertTrue(isinstance(cand.is_winner, bool))
            self.assertTrue(isinstance(cand.is_runoff, bool))
            self.assertTrue(isinstance(cand.is_incumbent, bool))
            #self.assertTrue(isinstance(cand.delegates, int))
            self.assertTrue(isinstance(cand.name, basestring))
        
        # FTP hits
        self.assertEqual(self.client._ftp_hits, 1)
    
    def test_getstates(self):
        # Pull states, using the state twice since that's all we have access to.
        self.first_two = self.client.get_states(TEST_STATE, TEST_STATE)
        self.assertEqual(type(self.first_two), type([]))
        self.assertEqual(len(self.first_two), 2)
        [self.assertEqual(type(i), State) for i in self.first_two]
        
        # FTP hits
        self.assertEqual(self.client._ftp_hits, 1)
    
    def test_topofticket(self):
        # The 2012 general election
        self.nov6 = self.client.get_topofticket()
        self.assertEqual(len(self.nov6.filter_races(office_name='President')), 52)
        self.assertEqual(len(self.nov6.filter_races(office_name='President', state_postal='CO')), 1)
        # Test custom properties
        self.assertEqual(len(self.nov6.states), 51)
        [self.assertEqual(type(i), ReportingUnit) for i in self.nov6.states]
        # Pull some bum dates
        self.assertRaises(FileDoesNotExistError, self.client.get_topofticket, "2011-02-07")
        self.assertRaises(ValueError, self.client.get_topofticket, 'abcdef')
        # Test the results against a get_state method to verify they are the same
        self.tt = self.client.get_topofticket()
        self.st = self.client.get_state(TEST_STATE)
        self.tt = self.tt.filter_races(office_name='President', state_postal='CA')[0]
        self.st = self.st.filter_races(office_name='President', state_postal='CA')[0]
#        self.assertEqual(
#            [i.vote_total for i in self.tt.state.results],
#            [i.vote_total for i in self.st.state.results]
#        )
     
    def test_presidential_summary(self):
        self.nov6 = self.client.get_presidential_summary()
        self.assertEqual(len(self.nov6.states), 51)
        self.assertEqual(len([self.nov6.nationwide]), 1)
        self.assertEqual(self.nov6.nationwide.electoral_votes_total, 538)
        self.assertEqual(sum([i.electoral_votes_total for i in self.nov6.states]), 538)
        [self.assertTrue(isinstance(i,ReportingUnit)) for i in self.nov6.counties]
        [self.assertTrue(isinstance(i.electoral_votes_total,int))
            for i in self.nov6.nationwide.results]
        for state in self.nov6.states:
            [self.assertTrue(isinstance(i.electoral_votes_total,int))
                for i in state.results]
        for county in self.nov6.counties:
            [self.assertTrue(isinstance(i.vote_total,int))
                for i in county.results]

#    def test_delegate_summary(self):
#        self.delsum = self.client.get_delegate_summary()
#        self.assertEqual(len(self.delsum), 2)
#        [self.assertEqual(type(i), Nomination) for i in self.delsum]
#        [self.assertEqual(type(i), Candidate) for i in self.delsum[0].candidates]
#        [self.assertEqual(type(i), StateDelegation) for i in self.delsum[0].states]
#        [self.assertEqual(type(i), Candidate) for i in self.delsum[0].states[0].candidates]


if __name__ == '__main__':
    unittest.main()
