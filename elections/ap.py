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
from cStringIO import StringIO
from BeautifulSoup import BeautifulStoneSoup
from dateutil.parser import parse as dateparse

from elex.api.models import (
    APElection,
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

    def get_electionday(self, election_date, **kwargs):
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
        return ElectionDay(self, dt.strftime("%Y%m%d"), **kwargs)

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

class BaseAPResultCollection(object):
    """
    Base class that defines the methods to retrieve AP CSV
    data and shared properties and methods for State and
    TopOfTicket objects.

    Any class that inherits from BaseAPResults must define
    these paths before it calls the parent __init__:

        * self.results_file_path
        * self.delegates_file_path
        * self.race_file_path
        * self.reporting_unit_file_path
        * self.candidate_file_path
    """
    def __init__(self, client, name, results=True, delegates=True):
        self.client = client
        self.name = name
        # The AP results files for these 7 states are missing
        # the leading 0 on the county FIPS codes.
        if self.name in ('AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT'):
            self.leading_zero_fips = True
        else:
            self.leading_zero_fips = False
        self._races = {}
        self._reporting_units = {}
        self._init_races()
        self._init_reporting_units()
        self._init_candidates()
        if results:
            self.fetch_results()
        # Fetches delegates for any Primary or Caucus races
        if delegates and self.filter_races(is_general=False):
            self.fetch_delegates()

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
    def counties(self):
        """
        Gets all reporting units that can be defined as counties
        (read: !states).

        Also does a crosswalk to aggregate New England ReportingUnits
        into their respective counties.
        """
        # Filter out the state level data
        ru_list = [
            o for o in self.reporting_units
            if o.fips and not o.is_state and o.fips != '00000'
        ]
        # If the AP reports sub-County data for this state, as they do for some
        # New England states, we'll need to aggregate it here. If not, we can
        # just pass out the data "as is."
        if self.name in COUNTY_CROSSWALK.keys():
            d = {}
            for ru in ru_list:
                try:
                    d[ru.fips].append(ru)
                except:
                    d[ru.fips] = [ru]
            county_list = []
            for county, units in d.items():
                ru = ReportingUnit(
                    name=COUNTY_CROSSWALK[self.name][county],
                    ap_number='',
                    fips=county,
                    abbrev=self.name,
                    precincts_total=sum([
                        int(i.precincts_total) for i in units
                    ]),
                    num_reg_voters=sum([int(i.num_reg_voters) for i in units]),
                )
                county_list.append(ru)
            return county_list
        else:
            return ru_list

    def fetch_results(self):
        """
        This will fetch and fill out all of the results. If called again,
        it will simply run through and update all of the results with
        the most fresh data from the AP.
        """
        self._get_flat_results()

    def fetch_delegates(self):
        """
        This will fetch and fill out the delegate_total variable on
        the candidate models with the statewide results.
        """
        self._get_flat_delegates()

    #
    # Private methods
    #

    def _init_candidates(self):
        """
        Download the state's candidate file and load the data.
        """
        # Fetch the data from the FTP
        candidate_list = self.client._fetch_csv(self.candidate_file_path)
        # Loop through it...
        for cand in candidate_list:
            # Create a Candidate...
            candidate = Candidate(
                first_name=cand['pol_first_name'],
                middle_name=cand['pol_middle_name'],
                last_name=cand['pol_last_name'],
                ap_race_number=self.ap_number_template % ({
                    'number': cand['ra_number'],
                    'state': cand.get('st_postal', 'None')
                }),
                ap_natl_number=cand['pol_nat_id'],
                ap_polra_number=cand['polra_number'],
                ap_pol_number=cand['pol_number'],
                abbrev_name=cand['pol_abbrv'],
                suffix=cand['pol_junior'],
                party=cand['polra_party'],
            )
            try:
                self._races[candidate.ap_race_number].candidates.append(candidate)
            except KeyError:
                pass

    def _init_races(self):
        """
        Download all the races in the state and load the data.
        """
        # Get the data
        race_list = self.client._fetch_csv(self.race_file_path)
        # Loop through it all
        for row in race_list:
            # Create a Race object...
            race = Race(
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
            race.ap_race_number=self.ap_number_template % ({
                'number': row['ra_number'],
                'state': row.get('st_postal', 'None')
            })
            # And add it to the global store
            self._races.update({race.ap_race_number: race})

    def _init_reporting_units(self):
        """
        Download all the reporting units and load the data.
        """
        # Get the data
        ru_list = self.client._fetch_csv(self.reporting_unit_file_path)
        # Loop through them all
        for r in ru_list:
            # if `st_postal` is in the dict, we're getting
            # Top of the Ticket data,
            # so we want to put reportingunits in the state they belong to.
            # otherwise stuff the RUs into all of the races,
            # as they're all in the same state.
            races = self.filter_races(
                statepostal=r.get('statepostal', None)
            ) or self.races
            # Create ReportingUnit objects for each race
            for race in races:
                ru = ReportingUnit(
                    electiondate=race.electiondate,
                    statePostal=r['st_postal'],
                    stateName=race.statename,
                    level=r['rut_name'].lower(),
                    reportingunitName=r['ru_name'],
                    reportingunitID=r['ru_number'],
                    fipsCode=r['ru_fip'],
                    lastUpdated=None,
                    precinctsReporting=0,
                    precinctsTotal=int(r['ru_precincts']),
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
                # And add them to the global store
                race.reportingunits.append(ru)

    def _get_flat_delegates(self):
        """
        Download statewide delegate totals and load it into Candidates.
        """
        # Pull the data
        flat_list = self.client._fetch_flatfile(
            self.delegates_file_path,
            [
                # First the basic fields that will the same in each row
                'test',
                'election_date',
                'state_postal',
                'district_type',
                'district_number',
                'district_name',
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
                'delegates',
                'vote_count',
                'is_winner',
                'national_politician_id',
            ]
        )
        # Filter it down to the state level results
        state_data = [i for i in flat_list if i['district_number'] == '1']
        # Loop through them
        for row in state_data:
            # Get the race
            race = self.get_race(row['race_number'])
            # Loop through the candidates in that race
            for cand in row['candidates']:
                # And if it's a legit candidate, cuz sometimes they come out
                # blank at the end of the file.
                if cand['candidate_number']:
                    # Grab the candidate
                    candidate = race.get_candidate(cand['candidate_number'])
                    # Set the delegates
                    candidate.delegates = int(cand['delegates'])

    def _get_flat_results(self, ftp=None):
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
        self.is_test = flat_list[0]['test'] == 't'

        # Start looping through the lines...
        for row in flat_list:

            # Get the race, with a special case for the presidential race
            ap_race_number = self.ap_number_template % ({
                'number': row['race_number'],
                'state': row['state_postal']
            })
            try:
                race = self.get_race(ap_race_number)
            except KeyError:
                continue

            # Figure out if it's a state or a county
            is_state = row['county_number'] == '1'
            county_number = str(row['county_number'])

            # Pull the reporting unit
            reporting_unit = race.get_reporting_unit(
                "%s%s" % (row['county_name'], county_number)
            )
            # Loop through all the candidates
            votes_cast = 0
            for cand in row['candidates']:
                # Skip it if the candidate is empty, as it sometimes is at
                # the end of the row
                if not cand['candidate_number']:
                    continue

                # Pull the existing candidate object
                candidate = race.get_candidate(cand["candidate_number"])
                if not candidate:
                    continue

                # Pull the vote total
                vote_count = int(cand['vote_count'])

                # Add it to the overall total
                votes_cast += vote_count

                # Update the candidate's global vote total
                # if data are statewide
                if is_state:
                    candidate.vote_total = vote_count

                # Set is_winner and is_runoff
                # (This will just get set over and over as we loop
                # but AP seems to put the statewide result in for every
                # reporting unit so I think we're safe.)
                candidate.is_winner = cand['is_winner'] == 'X'
                candidate.is_runoff = cand['is_winner'] == 'R'

                # Set whether the candidate is an incumbent
                candidate.is_incumbent = cand['incumbent'] == '1'

                # Create the Result object, which is specific to the
                # reporting unit in this row of the flatfile.
                result = Result(
                    candidate=candidate,
                    vote_total=vote_count,
                    reporting_unit=reporting_unit
                )
                # Update result connected to the reporting unit
                reporting_unit.update_result(result)

            # Update the reporting unit's precincts status
            reporting_unit.precincts_total = int(row['total_precincts'])
            reporting_unit.precincts_reporting = int(
                row['precincts_reporting']
            )
            reporting_unit.precincts_reporting_percent = calculate.percentage(
                reporting_unit.precincts_reporting,
                reporting_unit.precincts_total
            )

            # Update the total votes cast
            reporting_unit.votes_cast = votes_cast

            # Loop back through the results and set the percentages now
            # that we know the overall total
            for result in reporting_unit.results:
                result.vote_total_percent = calculate.percentage(
                    result.vote_total,
                    votes_cast
                )


class ElectionDay(BaseAPResultCollection):
    """
    All the results from an 2016 election day.

    Returned by the AP client in response to a `get_states_by_date`
    call. Contains, among its attributes, the results for all races recorded
    by the AP.
    """
    ap_number_template = '%(number)s-%(state)s'

    def __init__(self, client, name='20141104', results=True, delegates=False):
        d = {'name': name}
        self.results_file_path = "/Delegate_Tracking/US/flat/US_%(name)s.txt" % d
        self.race_file_path = "/inits/US/US_%(name)s_race.txt" % d
        self.reporting_unit_file_path = "/inits/US/US_%(name)s_ru.txt" % d
        self.candidate_file_path = "/inits/US/US_%(name)s_pol.txt" % d
        super(ElectionDay, self).__init__(client, name, results, delegates)



class Candidate(object):
    """
    A choice for voters in a race.

    In the presidential race, a person, like Barack Obama.
    In a ballot measure, a direction, like Yes or No.
    """
    def __init__(
        self, first_name=None, middle_name=None, last_name=None,
        abbrev_name=None, suffix=None, use_suffix=False,
        ap_natl_number=None, ap_polra_number=None,
        ap_race_number=None,
        party=None, ap_pol_number=None, is_winner=None,
        is_runoff=None, delegates=None, is_incumbent=None,
        vote_total=None
    ):
        self.first_name = first_name
        self.middle_name = middle_name
        self.last_name = last_name
        self.abbrev_name = abbrev_name
        self.suffix = suffix
        self.use_suffix = use_suffix
        self.ap_natl_number = ap_natl_number
        self.ap_polra_number = ap_polra_number
        self.ap_race_number = ap_race_number
        self.ap_pol_number = ap_pol_number
        self.party = party
        self.is_winner = is_winner
        self.is_runoff = is_runoff
        self.delegates = delegates
        self.is_incumbent = is_incumbent
        self.vote_total = vote_total

    def __unicode__(self):
        return unicode(self.name)

    def __str__(self):
        return self.__unicode__().encode("utf-8")

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.__unicode__())

    @property
    def name(self):
        if self.last_name not in ('Yes', 'No'):
            s = " ".join([i for i in [self.first_name, self.last_name] if i])
            return s.strip()
        else:
            return u'%s' % self.last_name


class Result(object):
    """
    The vote count for a candidate in a race in a particular reporting unit.
    """
    def __init__(self, candidate=None, reporting_unit=None, vote_total=None,
                 vote_total_percent=None, electoral_votes_total=None):
        self.candidate = candidate
        self.reporting_unit = reporting_unit
        self.vote_total = vote_total
        self.vote_total_percent = vote_total_percent
        self.electoral_votes_total = electoral_votes_total

    def __unicode__(self):
        return u'%s, %s, %s' % (self.candidate, self.reporting_unit,
                                self.vote_total)

    def __str__(self):
        return self.__unicode__().encode("utf-8")

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.__unicode__())


#
# Trend objects
#

class Chamber(object):
    """
    A chamber of Congress. Holds the makeup during an election for
    each party in a specific house.
    """
    def __init__(self, name):
        self.name = name
        self.dem_net_change = None
        self.gop_net_change = None
        self.others_net_change = None
        ##
        self.dem_won_total = None
        self.gop_won_total = None
        self.others_won_total = None
        ##
        self.dem_leading = None
        self.gop_leading = None
        self.others_leading = None
        ##
        self.dem_current_total = None
        self.gop_current_total = None
        self.others_current_total = None
        ##
        self.dem_holdovers = None
        self.gop_holdovers = None
        self.others_holdovers = None
        ##
        self.dem_insufficient = None
        self.gop_insufficient = None
        self.others_insufficient = None

    @property
    def gop_uncalled(self):
        """
        Uncalled races for GOP.
        Uncalled = "leading" + insufficient votes
        """
        return self.gop_leading + self.gop_insufficient

    @property
    def dem_uncalled(self):
        """
        Uncalled races for Dem.
        Uncalled = "leading" + insufficient votes
        """
        return self.dem_leading + self.dem_insufficient

    @property
    def others_uncalled(self):
        """
        Uncalled races for others.
        Uncalled = "leading" + insufficient votes
        """
        return self.others_leading + self.others_insufficient

    @property
    def all_uncalled(self):
        """
        Uncalled races for all parties.
        Uncalled = "leading" + insufficient votes
        """
        return self.others_uncalled + self.gop_uncalled + self.dem_uncalled

    def __unicode__(self):
        return unicode(self.name)

    def __str__(self):
        return self.__unicode__().encode("utf-8")

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.__unicode__())

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

#
# Town-to-county crosswalk
#

COUNTY_CROSSWALK = {
    'MA': {
        '25001': 'Barnstable',
        '25003': 'Berkshire',
        '25005': 'Bristol',
        '25007': 'Dukes',
        '25009': 'Essex',
        '25011': 'Franklin',
        '25013': 'Hampden',
        '25015': 'Hampshire',
        '25017': 'Middlesex',
        '25019': 'Nantucket',
        '25021': 'Norfolk',
        '25023': 'Plymouth',
        '25025': 'Suffolk',
        '25027': 'Worcester',
    },
    'NH': {
        '33001': 'Belknap',
        '33003': 'Carroll',
        '33005': 'Chesire',
        '33007': 'Coos',
        '33009': 'Grafton',
        '33011': 'Hillborough',
        '33013': 'Merrimack',
        '33015': 'Rockingham',
        '33017': 'Strafford',
        '33019': 'Sullivan',
    },
    'VT': {
        '50001': 'Addison',
        '50003': 'Bennington',
        '50005': 'Caledonia',
        '50007': 'Chittenden',
        '50009': 'Essex',
        '50011': 'Franklin',
        '50013': 'Grand Isle',
        '50015': 'Lamoille',
        '50017': 'Orange',
        '50019': 'Orleans',
        '50021': 'Rutland',
        '50023': 'Washington',
        '50025': 'Windham',
        '50027': 'Windsor',
    }
}
