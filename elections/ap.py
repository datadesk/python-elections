#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Collects and organizes election results published the Associated Press'
data service.

In order to use this library, you must pay AP for access to the data.

More information can be found on the AP's web site (http://www.apdigitalnews.\
com/ap_elections.html) or by contacting Anthony Marquez at amarquez@ap.org.
"""
import os
import csv
import copy
import itertools
import calculate
from ftplib import FTP
from datetime import date
from pprint import pprint
from cStringIO import StringIO
from BeautifulSoup import BeautifulStoneSoup
from dateutil.parser import parse as dateparse

from elex.api.models import (
    Candidate,
    BallotMeasure,
    CandidateReportingUnit,
    ReportingUnit,
    Race,
    Elections,
    Election
)


class AP(object):
    """
    The public client you can use to connect to AP's data feed.

    Example usage:

        >>> from elections import AP
        >>> client = AP(USERNAME, PASSWORD)
        >>> client.get_state("IA")
    """
    FTP_HOSTNAME = 'electionsonline.ap.org'

    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password
        self._ftp = None
        self._ftp_hits = 0

    def __unicode__(self):
        return unicode(self.username)

    def __str__(self):
        return self.__unicode__().encode("utf-8")

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.__unicode__())

    #
    # Public methods
    #

    @property
    def ftp(self):
        """
        Checks if we have an active FTP connection.
        If not, activates a new connection to the AP.
        """
        if not self._ftp or not self._ftp.sock:
            self._ftp = FTP(self.FTP_HOSTNAME, self.username, self.password)
            self._ftp_hits += 1
        return self._ftp

    def get_election(self, election_date, **kwargs):
        """
        Takes a date in any common format (YYYY-MM-DD is preferred)
        and returns a list of APResult objects for states holding
        elections that day.
        """
        try:
            dt = dateparse(election_date)
        except ValueError:
            raise ValueError(
                "The election date you've submitted could not be parsed. \
Try submitting it in YYYY-MM-DD format."
            )
        return Election(self, dt.strftime("%Y%m%d"), **kwargs)

    #
    # Private methods
    #

    def _fetch(self, path):
        """
        Fetch a file from the AP FTP.

        Provide a path, get back a file obj with your data.
        """
        # Make a file object to store our target
        buffer_ = StringIO()
        # Craft an FTP command that can pull the file
        cmd = 'RETR %s' % path
        # Connect to the FTP server, issue the command and catch the data
        # in our buffer file object.
        try:
            self.ftp.retrbinary(cmd, buffer_.write)
        except Exception, e:
            if "550 The system cannot find the" in e.message:
                raise FileDoesNotExistError(
                    "The file you've requested does not exist." +
                    " If you're looking for data about a state, make sure" +
                    " you input valid postal codes. If you're looking" +
                    " for a date, make sure it's correct."
                )
            elif "530 User cannot log in" in e.message:
                raise BadCredentialsError(
                    "The username and password you submitted" +
                    " are not accepted by the AP's FTP."
                )
            else:
                raise e
        # Return the file object
        return StringIO(buffer_.getvalue())

    def _fetch_csv(self, path, delimiter="|", fieldnames=None):
        """
        Fetch a pipe delimited file from the AP FTP.

        Provide the path of the file you want.

        Returns a list of dictionaries that's ready to roll.
        """
        # Fetch the data and stuff it in a CSV DictReaddr
        reader = csv.DictReader(
            self._fetch(path),
            delimiter=delimiter,
            fieldnames=fieldnames
        )
        # Clean up the keys and values, since AP provides them a little messy
        return [self._strip_dict(i) for i in reader]

    def _strip_dict(self, d):
        """
        Strip all leading and trailing whitespace in dictionary keys & values.

        This problem is common to the AP's CSV files
        """
        return dict(
            (k.strip(), v.strip()) for k, v in d.items()
            if k is not None and v is not None
        )

    def _fetch_flatfile(self, path, basicfields, candidatefields):
        """
        Retrive, parse and structure one of the AP's flatfiles.

        Returns a list of dictionaries with the standard "basicfields" as
        top-level keys and then a `candidates` key that contains a nested dict
        with the candidate data inside.

        AP's flatfiles are delimited by ";", do not include headers and include
        a dynamic number of fields depending on the number of candidates in the
        data set.

        Provide:

            * The path of the file you want
            * The list of basic fields that start each row
            * The list of candidate fields that will repeat outwards to right
              for each candidate in the data set.
        """
        # Fetch the data and toss it in a CSV reader
        reader = csv.reader(
            self._fetch(path),
            delimiter=";",
        )
        raw_data = list(reader)
        # Loop thorugh the raw data...
        prepped_data = []
        for row in raw_data:
            # Slice off the last field since it's always empty
            row = row[:-1]
            # Split out the basic fields
            basic_data = row[:len(basicfields)]
            # Load them into a new dictionary with the proper keys
            prepped_dict = dict(
                (basicfields[i], v) for i, v in enumerate(basic_data)
            )
            # Split out all the candidate sets that come after the basic fields
            candidate_data = row[len(basicfields):]
            candidate_sets = self._split_list(
                candidate_data, len(candidatefields)
            )
            # Load candidate data into a list of dicts with the proper keys
            prepped_dict['candidates'] = [
                dict((candidatefields[i], v) for i, v in enumerate(cand))
                for cand in candidate_sets
            ]
            prepped_data.append(prepped_dict)
        # Pass it all out
        return prepped_data

    def _split_list(self, iterable, n, fillvalue=None):
        """
        Splits the provided list into groups of n length.

        You can optionally provide a value to be included if the last list
        comes up short of the n value. By default it's none.

        Example usage:

            >>> _split_list([1,2,3,4,5,6], 2)
            [(1, 2), (3, 4), (5, 6)]
            >>> _split_list([1,2,3,4,5], 2, fillvalue="x")
            [(1, 2), (3, 4), (5, "x")]

        Derived from a snippet published by Stephan202
        http://stackoverflow.com/a/1625013
        """
        args = [iter(iterable)] * n
        return list(itertools.izip_longest(*args, fillvalue=fillvalue))


#
# Result collections
#

class Election(object):
    """
    Base class that defines the methods to retrieve AP CSV
    data and shared properties and methods for State and
    TopOfTicket objects.
    """
    ap_number_template = '%(number)s-%(state)s'

    def __init__(self, client, name='20160201', results=True, delegates=True):

        # The FTP connection
        self.client = client

        # The name of the election provided by the user
        self.name = name

        # Setting the file paths
        d = {'name': name}
        self.results_file_path = "/Delegate_Tracking/US/flat/US_%(name)s.txt" % d
        self.race_file_path = "/inits/US/US_%(name)s_race.txt" % d
        self.reporting_unit_file_path = "/inits/US/US_%(name)s_ru.txt" % d
        self.candidate_file_path = "/inits/US/US_%(name)s_pol.txt" % d

        # Cache for the objects so we can grab them when we need them
        self._races = {}
        self._reporting_units = {}
        self._candidates = {}
        self._results = {}

        # Load initialization data
        self._init_races()
        self._init_reporting_units()
        self._init_candidates()

        # Load results data
        if results:
            self._get_results()

    def __unicode__(self):
        return unicode(self.name)

    def __str__(self):
        return self.__unicode__().encode("utf-8")

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.__unicode__())

    #
    # Public methods
    #

    @property
    def races(self):
        """
        Returns a list of all the races reporting results.
        """
        return self._races.values()

    def get_race(self, ap_race_number):
        """
        Get a single Race object by it's ap_race_number
        """
        try:
            return self._races[ap_race_number]
        except KeyError:
            raise KeyError("The race you requested does not exist.")

    def filter_races(self, **kwargs):
        """
        Takes a series of keyword arguments and returns any Race objects
        that match. Works an AND query and returns anything that matches
        all of the provided kwargs.

        ex:
            >>> iowa.filter_races(office_name='President', party='GOP')
            [<Race: President>]
        """
        races = self.races
        for k in kwargs.keys():
            races = filter(lambda x: getattr(x, k) == kwargs[k], races)
        return races

    @property
    def reporting_units(self):
        """
        Get all reporting units
        """
        return self._reporting_units.values()

    def get_reporting_unit(self, fips):
        """
        Get a single ReportinUnit
        """
        try:
            return self._reporting_units[fips]
        except KeyError:
            raise KeyError("The reporting unit you requested does not exist.")

    @property
    def candidates(self):
        """
        Get all candidates
        """
        return self._candidates.values()

    def get_candidate(self, candidate_id):
        """
        Get a single ReportinUnit
        """
        try:
            return self._candidates[candidate_id]
        except KeyError:
            raise KeyError("The candidate you requested does not exist.")

    #
    # Private methods
    #

    def _init_races(self):
        """
        Download all the races in the state and load the data.
        """
        # Get the data
        row_list = self.client._fetch_csv(self.race_file_path)
        # Loop through it all
        for row in row_list:
            # Create a Race object...
            obj = Race(
                electiondate=row['el_date'],
                statePostal=row['st_postal'],
                stateName=None,
                test=None,
                raceID=row['ra_number'],
                raceType=None,
                raceTypeID=row['race_id'],
                officeID=row['office_id'],
                officeName=row['ot_name'],
                party=row['rt_party_name'],
                seatName=row['se_name'] or None,
                description=row['of_description'] or None,
                seatNum=row['se_number'] or None,
                uncontested=row['ra_uncontested'] == '1',
                lastUpdated=None,
                initialization_data=True,
                national=row['ra_national_b'] == '1',
                candidates=[],
                reportingUnits=[],
            )

            # A custom ID so we can grab this from other methods
            obj.ap_race_number = self.ap_number_template % ({
                'number': row['ra_number'],
                'state': row.get('st_postal', 'None')
            })

            # And add it to the global store
            self._races[obj.ap_race_number] = obj

    def _init_reporting_units(self):
        """
        Download all the reporting units and load the data.
        """
        # Get the data
        row_list = self.client._fetch_csv(self.reporting_unit_file_path)
        # Loop through them all
        for row in row_list:
            race_list = self.filter_races(statepostal=row['st_postal'])
            # Create ReportingUnit objects for each race
            for race in race_list:
                obj = ReportingUnit(
                    electiondate=race.electiondate,
                    statePostal=row['st_postal'],
                    stateName=race.statename,
                    level=row['rut_name'].lower(),
                    reportingunitName=row['ru_name'],
                    reportingunitID=row['ru_number'],
                    fipsCode=row['ru_fip'],
                    lastUpdated=None,
                    precinctsReporting=0,
                    precinctsTotal=int(row['ru_precincts']),
                    precinctsReportingPct=0.0,
                    uncontested=race.uncontested,
                    test=race.uncontested,
                    raceid=race.raceid,
                    racetype=race.racetype,
                    racetypeid=race.racetypeid,
                    officeid=race.officeid,
                    officename=race.officename,
                    seatname=race.seatname,
                    description=race.description,
                    seatnum=race.seatnum,
                    initialization_data=True,
                    national=race.national,
                    candidates=[],
                    votecount=0,
                )

                # Add them to global store using a custom
                # key we create here on-the-fly because
                # we'll need it elsewhere
                obj.key = "%s%s" % (row['ru_name'], row['ru_number'])
                self._reporting_units[obj.key] = obj

                # Add them to the race object
                race.reportingunits.append(obj)

    def _init_candidates(self):
        """
        Download the state's candidate file and load the data.
        """
        # Fetch the data from the FTP
        row_list = self.client._fetch_csv(self.candidate_file_path)
        # Loop through it...
        for row in row_list:
            # Create a Candidate...
            obj = Candidate(
                ballotorder=row['polra_in_order'],
                candidateid=row['polra_number'],
                first=row['pol_first_name'],
                last=row['pol_last_name'],
                party=row['polra_party'],
                polid=row['pol_nat_id'],
                polnum=row['pol_number'],
            )

            # Create our custom key
            obj.ap_race_number = self.ap_number_template % ({
                'number': row['ra_number'],
                'state': row.get('st_postal', 'None')
            })

            # Add the candidate to the related races candidate list
            self._races[obj.ap_race_number].candidates.append(obj)

            # Add the candidate to the global store
            self._candidates[obj.candidateid] = obj

    def _get_results(self, ftp=None):
        """
        Download, parse and structure the state and county votes totals.
        """
        # Download the data
        flat_list = self.client._fetch_flatfile(
            self.results_file_path,
            [
                # First the basic fields that will the same in each row
                'test',
                'election_date',
                'state_postal',
                'county_number',
                'fips',
                'county_name',
                'race_number',
                'office_id',
                'race_type_id',
                'seat_number',
                'office_name',
                'seat_name',
                'race_type_party',
                'race_type',
                'office_description',
                'number_of_winners',
                'number_in_runoff',
                'precincts_reporting',
                'total_precincts',
            ],
            [
                # Then the candidate fields that will repeat after the basics
                'candidate_number',
                'order',
                'party',
                'first_name',
                'middle_name',
                'last_name',
                'junior',
                'use_junior',
                'incumbent',
                'vote_count',
                'is_winner',
                'national_politician_id',
            ]
        )

        # Figure out if we're dealing with test data or the real thing
        is_test = flat_list[0]['test'] == 't'

        # Start looping through the lines...
        for row in flat_list:

            # Get the race, with a special case for the presidential race
            ap_race_number = self.ap_number_template % ({
                'number': row['race_number'],
                'state': row['state_postal']
            })
            race = self.get_race(ap_race_number)

            # Total the votes
            votes_total = sum([int(o['vote_count']) for o in row['candidates']])

            # Loop through all the candidates
            for candrow in row['candidates']:
                # Skip it if the candidate is empty, as it sometimes is at
                # the end of the row
                if not candrow['candidate_number']:
                    continue

                # Pull the existing candidate object
                candidate = self.get_candidate(candrow["candidate_number"])

                # Pull the reporting unit
                ru_key = "%s%s" % (row['county_name'], row['county_number'])
                reporting_unit = self.get_reporting_unit(ru_key)

                cru = CandidateReportingUnit(
                    test=is_test,
                    initialization_data=False,
                    lastupdated=None,
                    # Race
                    electiondate=race.electiondate,
                    raceid=race.raceid,
                    statepostal=race.statepostal,
                    statename=race.statename,
                    racetype=race.racetype,
                    racetypeid=race.racetypeid,
                    officeid=race.officeid,
                    officename=race.officename,
                    seatname=race.seatname,
                    description=race.description,
                    seatnum=race.seatnum,
                    national=race.national,
                    is_ballot_measure=None,
                    uncontested=race.uncontested,
                    # Candidate
                    first=candidate.first,
                    last=candidate.last,
                    party=candidate.party,
                    candidateID=candidate.candidateid,
                    polID=candidate.polid,
                    polNum=candidate.polnum,
                    incumbent=candrow['incumbent'] == '1',
                    ballotOrder=candidate.ballotorder,
                    # Results
                    voteCount=int(candrow['vote_count']),
                    votePct=calculate.percentage(int(candrow['vote_count']), votes_total),
                    winner=candrow['is_winner'],
                    # Reporting unit
                    level=reporting_unit.level,
                    reportingunitname=reporting_unit.reportingunitname,
                    reportingunitid=reporting_unit.reportingunitid,
                    fipscode=reporting_unit.fipscode,
                    precinctsreporting=reporting_unit.precinctsreporting,
                    precinctstotal=reporting_unit.precinctstotal,
                    precinctsreportingpct=reporting_unit.precinctsreportingpct,
                )

                cru.key = "%s%s%s" % (
                    race.raceid,
                    ru_key,
                    candrow["candidate_number"],
                )
                self._results[cru.key] = cru

            # Update the reporting unit's precincts status
            reporting_unit.precinctstotal = int(row['total_precincts'])
            reporting_unit.precinctsreporting = int(row['precincts_reporting'])
            reporting_unit.precinctsreportingpct = calculate.percentage(
                reporting_unit.precinctsreporting,
                reporting_unit.precinctstotal
            )
            reporting_unit.votecount = votes_total


#
# Errors
#


class FileDoesNotExistError(Exception):

    def __init__(self, value):
        self.parameter = value

    def __str__(self):
        return repr(self.parameter)


class BadCredentialsError(Exception):

    def __init__(self, value):
        self.parameter = value

    def __str__(self):
        return repr(self.parameter)
