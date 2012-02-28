#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Collects and organizes election results published the Associated Press's 
data service.

In order to use this library, you must pay AP for access to the data.

More information can be found on the AP's web site (http://www.apdigitalnews.com/ap_elections.html)
or by contacting Anthony Marquez at amarquez@ap.org.
"""
import os
import csv
import itertools
import calculate
from ftplib import FTP
from datetime import date
from cStringIO import StringIO
from dateutil.parser import parse as dateparse


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
    
    def get_state(self, *args, **kwargs):
        """
        Takes a single state postal code, returns an APResult
        object for that state.
        """
        result = State(self, args[0], **kwargs)
        self.ftp.quit()
        return result
    
    def get_states(self, *args, **kwargs):
        """
        Takes a list of state postal codes, returns a list of APResult
        objects.
        """
        results = [State(self, state, **kwargs) for state in args]
        self.ftp.quit()
        return results
    
    def get_topofticket(self, election_date, **kwargs):
        """
        Takes a date in any common format (YYYY-MM-DD is preferred) 
        and returns the results for that date.
        """
        try:
            dt = dateparse(election_date)
        except ValueError:
            raise ValueError("The election date you've submitted could not be parsed. Try submitting it in YYYY-MM-DD format.")
        result = TopOfTicket(self, dt.strftime("%Y%m%d"), **kwargs)
        self.ftp.quit()
        return result
    
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
                raise FileDoesNotExistError("The file you've requested does not exist." +
                    " If you're looking for data about a state, make sure you" +
                    " input valid postal codes. If you're looking for a date," +
                    " make sure it's correct.")
            elif "530 User cannot log in" in e.message:
                raise BadCredentialsError("The username and password you submitted" +
                " are not accepted by the AP's FTP.")
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
        Strip all leading and trailing whitespace in dictionary keys and values.
        
        This problem is common to the AP's CSV files
        """
        return dict((k.strip(), v.strip()) for k, v in d.items() if k != None and v != None)
    
    def _fetch_flatfile(self, path, basicfields, candidatefields):
        """
        Retrive, parse and structure one of the AP's flatfiles.
        
        Returns a list of dictionaries with the standard "basicfields" as
        top-level keys and then a `candidates` key that contains a nested dictionary
        with the candidate data inside.
        
        AP's flatfiles are delimited by ";", do not include headers and include 
        a dynamic number of fields depending on the number of candidates in the 
        data set.
        
        Provide:
            
            * The path of the file you want
            * The list of basic fields that start each row
            * The list of candidate fields that will repeat outwards to the right 
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
            prepped_dict = dict((basicfields[i], v) for i, v in enumerate(basic_data))
            # Split out all the candidate sets that come after the basic fields
            candidate_data = row[len(basicfields):]
            candidate_sets = self._split_list(candidate_data, len(candidatefields))
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


class BaseAPResults(object):
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
        Gets all reporting units that can be defined as counties (read: !states).
        Also does a crosswalk to aggregate New England ReportingUnits into their
        respective counties. 
        """
        # Filter out the state level data
        ru_list = [o for o in self.reporting_units if o.fips and not o.is_state]
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
                    name = COUNTY_CROSSWALK[self.name][county],
                    ap_number = '',
                    fips = county,
                    abbrev = self.name,
                    precincts_total = sum([int(i.precincts_total) for i in units]),
                    num_reg_voters = sum([int(i.num_reg_voters) for i in units]),
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
                first_name = cand['pol_first_name'],
                middle_name = cand['pol_middle_name'],
                last_name = cand['pol_last_name'],
                ap_race_number = cand['ra_number'],
                ap_natl_number = cand['pol_nat_id'],
                ap_polra_number = cand['polra_number'],
                ap_pol_number = cand['pol_number'],
                abbrev_name = cand['pol_abbrv'],
                suffix = cand['pol_junior'],
                party = cand['polra_party'],
                # use_suffix?
            )
            self._races[candidate.ap_race_number].add_candidate(candidate)
    
    def _init_races(self):
        """
        Download all the races in the state and load the data.
        """
        # Get the data
        race_list = self.client._fetch_csv(self.race_file_path)
        # Loop through it all
        for race in race_list:
            # Create a Race object...
            race = Race(
                ap_race_number = race['ra_number'],
                office_name = race['ot_name'],
                office_description = race['of_description'],
                office_id = race['office_id'],
                race_type = race['race_id'],
                seat_name = race['se_name'],
                seat_number = race['se_number'],
                state_postal = race.get('st_postal', None),
                scope = race['of_scope'],
                date = date(*map(int, [race['el_date'][:4], race['el_date'][4:6], race['el_date'][6:]])),
                num_winners = int(race['ra_num_winners']),
                party = race['rt_party_name'],
                uncontested = race['ra_uncontested'] == '1',
            )
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
            # if `st_postal` is in the dict, we're getting Top of the Ticket data,
            # so we want to put reportingunits in the state they belong to.
            # otherwise stuff the RUs into all of the races, as they're all in the same state.
            races = self.filter_races(state_postal=r.get('st_postal', None)) or self.races
            # Create ReportingUnit objects for each race
            for race in races:
                ru = ReportingUnit(
                    name = r['ru_name'],
                    ap_number = r['ru_number'],
                    fips = r['ru_fip'],
                    abbrev = r['ru_abbrv'],
                    precincts_total = int(r['ru_precincts']),
                    num_reg_voters = int(r['ru_reg_voters']),
                )
                # And add them to the global store
                race._reporting_units.update({ru.key: ru})
            # We add a set of reportingunits for the State object
            # so you can get county and state voter info from the
            # State object itself. 
            ru = ReportingUnit(
                name = r['ru_name'],
                ap_number = r['ru_number'],
                fips = r['ru_fip'],
                abbrev = r['ru_abbrv'],
                precincts_total = int(r['ru_precincts']),
                num_reg_voters = int(r['ru_reg_voters']),
            )
            self._reporting_units.update({ru.key: ru})
    
    def _get_flat_delegates(self):
        """
        Download statewide delegate totals and load it into Candidates.
        """
        # Pull the data
        flat_list = self.client._fetch_flatfile(
            self.delegates_file_path,
            [ # First the basic fields that will the same in each row
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
           [ # Then the candidate fields that will repeat after the basics
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
            [ # First the basic fields that will the same in each row
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
           [ # Then the candidate fields that will repeat after the basics
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
            
            # Get the race
            race = self.get_race(row['race_number'])
            
            # Figure out if it's a state or a county
            fips =row['fips']
            is_state = row['county_number'] == '1'
            county_number = str(row['county_number'])
            
            # AP stupidly strips leading 0s in the FIPS for the 
            # results file. This fixes em.
#            if is_state:
#                fips = '00000'
#            else:
#                if self.leading_zero_fips and fips[0] != '0':
#                    fips = '0' + fips
            
            # Pull the reporting unit
            reporting_unit = race.get_reporting_unit("%s%s" % (row['county_name'], county_number))
            # Loop through all the candidates
            votes_cast = 0
            for cand in row['candidates']:
                # Skip it if the candidate is empty, as it sometimes is at
                # the end of the row
                if not cand['candidate_number']:
                    continue
                
                # Pull the existing candidate object
                candidate = race.get_candidate(cand["candidate_number"])
                
                # Pull the vote total
                vote_count = int(cand['vote_count'])
                
                # Add it to the overall total
                votes_cast += vote_count
                
                # Update the candidate's global vote total if data are statewide
                if is_state:
                    candidate.vote_total = vote_count
                
                # Set is_winner and is_runoff
                # (This will just get set over and over as we loop
                # but AP seems to put the statewide result in for every 
                # reporting unit so I think we're safe.)
                candidate.is_winner = cand['is_winner'] == 'X'
                candidate.is_runoff = cand['is_winner'] == 'R'
                
                # Create the Result object, which is specific to the
                # reporting unit in this row of the flatfile.
                result = Result(
                    candidate = candidate,
                    vote_total = vote_count,
                    reporting_unit = reporting_unit
                )
                # Update result connected to the reporting unit
                reporting_unit.update_result(result)
                
            # Update the reporting unit's precincts status
            reporting_unit.precincts_reporting = int(row['precincts_reporting'])
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

class State(BaseAPResults):
    """
    One of these United States.
    
    Returned by the AP client in response to a `get_state` or `get_states`
    call. Contains, among its attributes, the results for all races recorded
    by the AP.
    """

    def __init__(self, client, name, results=True, delegates=True):
        self.results_file_path = "/%(name)s/flat/%(name)s.txt" % {'name': name}
        self.delegates_file_path = "/%(name)s/flat/%(name)s_D.txt" % {'name': name}
        self.race_file_path = "/inits/%(name)s/%(name)s_race.txt" % {'name': name}
        self.reporting_unit_file_path = "/inits/%(name)s/%(name)s_ru.txt" % {'name': name}
        self.candidate_file_path = "/inits/%(name)s/%(name)s_pol.txt" % {'name': name}
        super(State, self).__init__(client, name, results, delegates)


class TopOfTicket(BaseAPResults):
    """
    These United States.
    
    Returned by the AP client in response to a `get_topofticket`
    call. Contains, among its attributes, the results for all races recorded
    by the AP.
    """
    def __init__(self, client, name, results=True, delegates=True):
        self.results_file_path = "/Delegate_Tracking/US/flat/US_%(name)s.txt" % {'name': name}
        self.delegates_file_path = "/Delegate_Tracking/US/flat/US_%(name)s_d.txt" % {'name': name}
        self.race_file_path = "/inits/US/US_%(name)s_race.txt" % {'name': name}
        self.reporting_unit_file_path = "/inits/US/US_%(name)s_ru.txt" % {'name': name}
        self.candidate_file_path = "/inits/US/US_%(name)s_pol.txt" % {'name': name}
        super(TopOfTicket, self).__init__(client, name, results, delegates)
    
    @property
    def states(self):
        return [o for o in self._reporting_units.values() if o.is_state]


class Race(object):
    """
    A contest being decided by voters choosing between candidates.
    
    For example:
    
        * The presidential general election
        * The governorship of Maine
        * Proposition 8 in California
    
    """
    _race_types = {
        'D': 'Dem Primary',
        'R': 'GOP Primary',
        'G': 'General Election',
        'E': 'Dem Caucus',
        'S': 'GOP Caucus',
        'L': 'Libertarian', # Not documented by the AP, but that's what it appears to be.
    }

    def __init__(self, ap_race_number=None, office_name=None, office_description=None,
                 office_id=None, seat_name=None, seat_number=None, state_postal=None, scope=None,
                 date=None, num_winners=None, race_type=None, party=None, uncontested=None,
                 precincts_total=None, precincts_reporting=None,
                 precincts_reporting_percent=None, votes_cast=None):
        self.ap_race_number = ap_race_number
        self.office_name = office_name
        self.office_description = office_description
        self.office_id = office_id
        self.seat_name = seat_name
        self.seat_number = seat_number
        self.state_postal = state_postal
        self.scope = scope
        self.date = date
        self.num_winners = num_winners
        self.race_type = race_type
        self.party = party
        self.uncontested = uncontested
        self._candidates = {}
        self._reporting_units = {}
    
    def __unicode__(self):
        return unicode(self.name)
    
    def __str__(self):
        return self.__unicode__().encode("utf-8")
    
    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.__unicode__())
    
    @property
    def name(self):
        name = ''
        if self.scope == 'L':
            if self.office_description:
                name = '%s %s - %s' % (self.office_name, self.seat_name, self.office_description)
            else:
                name = '%s %s' % (self.office_name, self.seat_name)
        else:
            if self.office_name == "Proposition":
                num = self.seat_name.split('-')[0].strip()
                name = "%s %s" % (self.office_name, num)
            else:
                name = '%s' % self.office_name
        if not self.is_general:
            name = '%s - %s' % (self.race_type_name, name)
        return name
    
    @property
    def candidates(self):
        return sorted(self._candidates.values(), key=lambda x: x.last_name)
    
    def get_candidate(self, ap_polra_num):
        """
        Takes AP's polra number and returns a Candidate object.
        """
        return self._candidates.get(ap_polra_num, None)
    
    def add_candidate(self, candidate):
        self._candidates.update({candidate.ap_polra_number: candidate})

    def get_reporting_unit(self, number):
        """
        Get a single ReportingUnit
        """
        return self._reporting_units.get(number, None)
    
    @property
    def reporting_units(self):
        """
        Returns all reporting units that belong to this race as a list of
        ReportingUnit objects.
        """
        return self._reporting_units.values()
    
    @property
    def state(self):
        """
        Returns the state-level results for this race as a ReportingUnit object.
        """
        return [o for o in self.reporting_units if o.is_state][0]
    
    @property
    def counties(self):
        """
        Returns all the counties that report results for this race as a list
        of ReportingUnit objects.
        """
        ru_list = sorted(
            [o for o in self.reporting_units if o.fips and not o.is_state],
            key=lambda x: x.name
        )
        # If the AP reports sub-County data for this state, as they do for some
        # New England states, we'll need to aggregate it here. If not, we can
        # just pass out the data "as is."
        if self.state.abbrev in COUNTY_CROSSWALK.keys():
            d = {}
            for ru in ru_list:
                try:
                    d[ru.fips].append(ru)
                except KeyError:
                    d[ru.fips] = [ru]
            county_list = []
            for county, units in d.items():
                ru = ReportingUnit(
                    name = COUNTY_CROSSWALK[self.state.abbrev][county],
                    ap_number = '',
                    fips = county,
                    abbrev = self.name,
                    precincts_reporting = sum([int(i.precincts_reporting) for i in units]),
                    precincts_total = sum([int(i.precincts_total) for i in units]),
                    num_reg_voters = sum([int(i.num_reg_voters) for i in units]),
                    votes_cast = sum([int(i.votes_cast) for i in units])
                )
                ru.precincts_reporting_percent = calculate.percentage(
                    ru.precincts_reporting,
                    ru.precincts_total
                )
                # Group all the candidates
                cands = {}
                for unit in units:
                    for result in unit.results:
                        try:
                            cands[result.candidate.ap_polra_number].append(result)
                        except KeyError:
                            cands[result.candidate.ap_polra_number] = [result]
                for ap_polra_number, results in cands.items():
                    combined = Result(
                        candidate = results[0].candidate,
                        reporting_unit = ru,
                        vote_total = sum([i.vote_total for i in results]),
                        vote_total_percent = calculate.percentage(
                            sum([i.vote_total for i in results]),
                            ru.votes_cast
                        )
                    )
                    # Update result connected to the reporting unit
                    ru.update_result(combined)
                # Load the finished county into our list
                county_list.append(ru)
            return county_list
        else:
            return ru_list
        return ru_list
    
    @property
    def race_type_name(self):
        """
        Returns a descriptive name for the race_type.
        """
        return self._race_types.get(self.race_type, None)
    
    @property
    def is_primary(self):
        return self.race_type in ('D', 'R',)
    
    @property
    def is_caucus(self):
        return self.race_type in ('E', 'S',)
    
    @property
    def is_general(self):
        return self.race_type == 'G'


class ReportingUnit(object):
    """
    An area or unit that groups votes into a total.
    
    For instance, a state, a congressional district, a county.
    """
    def __init__(self, ap_number=None, name=None, abbrev=None, fips=None,
                 precincts_total=None, num_reg_voters=None, votes_cast=None,
                 precincts_reporting=None, precincts_reporting_percent=None):
        self.ap_number = ap_number
        self.name = name
        self.abbrev = abbrev
        self.fips = fips
        self.num_reg_voters = num_reg_voters
        self.votes_cast = votes_cast
        self.precincts_total = precincts_total
        self.precincts_reporting = precincts_reporting
        self.precincts_reporting_percent = precincts_reporting_percent
        self._results = {}
    
    def __unicode__(self):
        name = self.name
        if self.is_state:
            name = '%s (state)' % name
        return unicode(name)
    
    def __str__(self):
        return self.__unicode__().encode("utf-8")
    
    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.__unicode__())

    @property
    def key(self):
        return "%(name)s%(ap_number)s" % self.__dict__
    
    @property
    def results(self):
        """
        Returns the Result objects sorted by total votes (highest first).
        
        If no votes are in, it returns the candidates in alphabetical order.
        """
        if self.votes_cast:
            return sorted(self._results.values(), key=lambda x: x.vote_total,
                reverse=True)
        else:
            return sorted(self._results.values(), key=lambda x: x.candidate.last_name)
    
    def update_result(self, result):
        self._results[result.candidate.ap_polra_number] = result
    
    @property
    def is_state(self):
        return self.fips == '00000'


class Candidate(object):
    """
    A choice for voters in a race.
    
    In the presidential race, a person, like Barack Obama.
    In a ballot measure, a direction, like Yes or No.
    """
    def __init__(self, first_name=None, middle_name=None, last_name=None,
                 abbrev_name=None, suffix=None, use_suffix=False, 
                 ap_natl_number=None, ap_polra_number=None, ap_race_number=None,
                 party=None, ap_pol_number=None, is_winner=None,
                 is_runoff=None, delegates=None):
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
    
    def __unicode__(self):
        return unicode(self.name)
    
    def __str__(self):
        return self.__unicode__().encode("utf-8")
    
    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.__unicode__())
    
    @property
    def name(self):
        if not self.last_name in ('Yes', 'No'):
            s = u'%s %s' % (self.first_name, self.last_name)
            return s.strip()
        else:
            return u'%s' % self.last_name


class Result(object):
    """
    The vote count for a candidate in a race in a particular reporting unit.
    """
    def __init__(self, candidate=None, reporting_unit=None, vote_total=None,
                 vote_total_percent=None):
        self.candidate = candidate
        self.reporting_unit = reporting_unit
        self.vote_total = vote_total
        self.vote_total_percent = vote_total_percent
    
    def __unicode__(self):
        return u'%s, %s, %s' % (self.candidate, self.reporting_unit,
                                self.vote_total)
    
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



