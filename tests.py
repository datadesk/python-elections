#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests out python-elections

These tests were written using the Los Angeles Times' login, which gives it state
level access for California and nationwide access elsewhere. If you have a different
access level, this will prove to be a problem.

We need to work this out somehow. If you have any bright ideas let me know.
"""
import os
import unittest
from elections import Election
from datetime import date, datetime
#from elections.ap import Nomination, StateDelegation
#from elections.ap import Candidate, Race, ReportingUnit, Result, State
from elections import FileDoesNotExistError, BadCredentialsError



class FTPTest(unittest.TestCase):

    def setUp(self):
        self.username = os.environ['AP_USERNAME'],
        self.password = os.environ['AP_PASSWORD']
        self.electiondate = "20160201"
        self.baddate = "20160202"

    def test_badlogin(self):
        with self.assertRaises(BadCredentialsError):
             Election(
                electiondate=self.electiondate,
                username="foo",
                password="bar"
            )

    def test_baddate(self):
        with self.assertRaises(FileDoesNotExistError):
            Election(
                electiondate=self.baddate,
                username=self.username,
                password=self.password,
            )

    def test_election(self):
        self.election = Election(
            electiondate=self.electiondate,
            username=self.username,
            password=self.password,
        )

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
        self.assertTrue(
            isinstance(race.race_type_name, basestring) or
            isinstance(race.race_type_name, type(None))
        )
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
        ru_list[0].num_reg_voters
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
            ru.num_reg_voters
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

if __name__ == '__main__':
    unittest.main()
