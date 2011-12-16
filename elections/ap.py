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
import calculate
from ftplib import FTP
from datetime import date
from cStringIO import StringIO

#
# Utils
#

def split_len(seq, length):
    return [seq[i:i+length] for i in range(0, len(seq), length)]

def strip_dict(d):
    """
    Strip all leading and trailing whitespace in dictionary keys and values.
    """
    return dict((k.strip(), v.strip()) for k, v in d.items())

#
# AP data
#

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
    
    def get_state(self, state=None, *args, **kwargs):
        """
        Takes a single state postal code, returns an APResult
        object for that state.
        """
        result = State(self, state, *args, **kwargs)
        self.ftp.quit()
        return result
    
    def get_states(self, states=[], *args, **kwargs):
        """
        Takes a list of state postal codes, returns a list of APResult
        objects.
        """
        results = [State(self, state, *args, **kwargs) for state in states]
        self.ftp.quit()
        return results


class State(object):
    """
    One of these United States.
    
    Returned by the AP client in response to a `get_state` or `get_states`
    call. Contains, among its attributes, the results for all races recorded
    by the AP.
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
        Returns a list of all the races reporting results in this state.
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
        that match. Works an OR query and returns anything that matches
        any of the provided kwargs. 
        
        ex:
            >>> iowa.filter_races(office_name='President', party='GOP')
            [<Race: President>]
        """
        s = set()
        for k in kwargs.keys():
            s.update(filter(lambda x: getattr(x, k) == kwargs[k], self.races))
        return list(s)

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
        Gets all reporting units that can be defined as counties.
        """
        return [o for o in self.reporting_units if o.fips and not o.is_state]

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
    
    def _fetch_csv(self, path):
        """
        Fetch a delimited file from the AP FTP.
        
        Provide the path of the file you want.
        
        Returns a list of dictionaries that's ready to roll.
        """
        buffer = StringIO()
        cmd = 'RETR %s' % path
        self.client.ftp.retrbinary(cmd, buffer.write)
        reader = csv.DictReader(StringIO(buffer.getvalue()), delimiter='|')
        return [strip_dict(i) for i in reader]
    
    def _init_candidates(self):
        """
        Download the state's candidate file and load the data.
        """
        # Fetch the data from the FTP
        candidate_list = self._fetch_csv("/inits/%(name)s/%(name)s_pol.txt" % self.__dict__)
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
        race_list = self._fetch_csv("/inits/%(name)s/%(name)s_race.txt" % self.__dict__)
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
        ru_list = self._fetch_csv("/inits/%(name)s/%(name)s_ru.txt" % self.__dict__)
        # Loop through them all
        for r in ru_list:
            # Create ReportingUnit objects for each race
            for race in self.races:
                ru = ReportingUnit(
                    name = r['ru_name'],
                    ap_number = r['ru_number'],
                    fips = r['ru_fip'],
                    abbrev = r['ru_abbrv'],
                    precincts_total = int(r['ru_precincts']),
                    num_reg_voters = int(r['ru_reg_voters']),
                )
                # And add them to the global store
                race._reporting_units.update({ru.fips: ru})
            # We add a set of reportingunits for the State object
            # so you can get county and state voter info from the
            # State object itself. We null out results, since there
            # shouldn't ever be any for these.
            ru = ReportingUnit(
                name = r['ru_name'],
                ap_number = r['ru_number'],
                fips = r['ru_fip'],
                abbrev = r['ru_abbrv'],
                precincts_total = int(r['ru_precincts']),
                num_reg_voters = int(r['ru_reg_voters']),
            )
            self._reporting_units.update({ru.fips: ru})

    def _get_flat_delegates(self, ftp=None):
        # Download state results file
        if self.name == 'US':
            file_dir = '/US_topofticket/flat/'
        else:
            file_dir = '/%s/flat/' % self.name
        results_file = '%s_D.txt' % self.name
        
        self.client.ftp.retrlines('RETR ' + os.path.join(file_dir, results_file), self._process_flat_delegates_line)  

    def _process_flat_delegates_line(self, line):
        """
        Takes a line from the flat delegates file and tosses it out
        until it finds the state-wide result, then assigns the delegates
        to the proper candidate.
        """
        DISTRICT_NUM, RACE_NUM = (4, 6)
        POLRA_NUM, NUM_DELEGATES = (0, 9)
        
        bits = line.split(';')
        del bits[-1]

        # The first 19 fields are race / reporting unit specific
        primary_bits = bits[:19]
        if primary_bits[DISTRICT_NUM] != '1': 
            return # We only want state results
        # The next X set of 13 fields belong to X # of candidates
        # So we split by 13, and len(candidate_bits) == # of candidates == X
        candidate_bits = split_len(bits[19:], 13) 
        race = self.get_race(primary_bits[RACE_NUM])
        for cand in candidate_bits:
            candidate = race.get_candidate(cand[POLRA_NUM])
            num_delegates = int(cand[NUM_DELEGATES])
            candidate.delegate_total = num_delegates

    def _get_flat_results(self, ftp=None):
        
        # Download state results file
        if self.name == 'US':
            file_dir = '/US_topofticket/flat/'
        else:
            file_dir = '/%s/flat/' % self.name
        results_file = '%s.txt' % self.name
        
        self.client.ftp.retrlines('RETR ' + os.path.join(file_dir, results_file), self._process_flat_results_line)  
    
    def _process_flat_results_line(self, line):
        """
        Takes a line from a flat results file and updates various
        objects with the new information.
        """
        # Race / ReportingUnit fields
        IS_TEST, DATE, STATE, COUNTY_NUM, FIPS, RU_NAME, RACE_NUM,\
        OFFICE_ID, RTYPE_ID, SEAT_NUM, OFFICE_NAME, SEAT_NAME, RTYPE_PARTY, RTYPE,\
        OFFICE_DESCRIP, MAX_WINNERS, NUM_RUNOFF, PRECINCTS_REPORTING, TOT_PRECINCTS =\
        (0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18)
        
        # Candidate fields
        CANDIDATE_NUM, ORDER, PARTY, FNAME, MNAME, LNAME, SFFX, USE_SFFX,\
        INCUMBENT, VOTE_COUNT, IS_WINNER, NPID = (0,1,2,3,4,5,6,7,8,9,10,11)
        
        bits = line.split(';')
        del bits[-1]

        # The first 19 fields are race / reporting unit specific
        primary_bits = bits[:19]
        # The next X set of 12 fields belong to X # of candidates
        # So we split by 12, and len(candidate_bits) == # of candidates == X
        candidate_bits = split_len(bits[19:], 12) 

        self.is_test = primary_bits[IS_TEST] == 't'
        
        is_state = primary_bits[COUNTY_NUM] == '1'
        
        fips = primary_bits[FIPS]
        # AP stupidly strips leading 0s in the FIPS for the 
        # results file. This helps us match back up.
        if is_state:
            fips = '00000'
        else:
            if self.leading_zero_fips and not fips[0] == '0':
                fips = '0' + primary_bits[FIPS]

        race = self.get_race(primary_bits[RACE_NUM]) 
        reporting_unit = race.get_reporting_unit(fips)

        votes_cast = 0
        for cand in candidate_bits:
            candidate = race.get_candidate(cand[CANDIDATE_NUM])
            vote_count = int(cand[VOTE_COUNT])
            votes_cast += vote_count
            if is_state: # Update the overall vote total if it's state-wide
                candidate.vote_total = vote_count
            candidate.is_winner = cand[IS_WINNER] == 'X'
            candidate.is_runoff = cand[IS_WINNER] == 'R'

            reporting_unit.update_result(Result(
                candidate = candidate,
                vote_total = vote_count,
                reporting_unit = reporting_unit
            ))

            reporting_unit.precincts_reporting = int(primary_bits[PRECINCTS_REPORTING])
            reporting_unit.precincts_reporting_percent = calculate.percentage(reporting_unit.precincts_reporting,
                                                    reporting_unit.precincts_total)

        reporting_unit.votes_cast = votes_cast
        
        for result in reporting_unit.results:
            result.vote_total_percent = calculate.percentage(result.vote_total, votes_cast)

class Candidate(object):
    """
    A choice for voters in a race.
    
    In the presidential race, a person, like Barack Obama.
    In a ballot measure, a direction, like Yes or No.
    """
    def __init__(self, first_name=None, middle_name=None, last_name=None,
                 abbrev_name=None, suffix=None, use_suffix=False, 
                 ap_natl_number=None, ap_polra_number=None, ap_race_number=None,
                 combined_id=None, party=None, ap_pol_number=None, is_winner=None,
                 is_runoff=None, delegate_total=None, delegate_total_percent=None):
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
        self.combined_id = combined_id
        self.party = party
        self.is_winner = is_winner
        self.is_runoff = is_runoff
        self.delegate_total = delegate_total

    @property
    def delegates(self):
        return self.delegate_total

    def __unicode__(self):
        if not self.last_name in ('Yes', 'No'):
            s = u'%s %s' % (self.first_name, self.last_name)
            return s.strip()
        else:
            return u'%s' % self.last_name

    def __str__(self):
        return self.__unicode__()

    def __repr__(self):
        return u'<Candidate: %s>' % self.__unicode__()


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
        'S': 'GOP Caucus'
    }

    def __init__(self, ap_race_number=None, office_name=None, office_description=None,
                 office_id=None, seat_name=None, seat_number=None, scope=None,
                 date=None, num_winners=None, race_type=None, party=None, uncontested=None,
                 precincts_total=None, precincts_reporting=None,
                 precincts_reporting_percent=None, votes_cast=None):
        self.ap_race_number = ap_race_number
        self.office_name = office_name
        self.office_description = office_description
        self.office_id = office_id
        self.seat_name = seat_name
        self.seat_number = seat_number
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
            name = u'%s - %s' % (self.race_type_name, name)   
        return name
    
    @property
    def candidates(self):
        return self._candidates.values()
    
    def get_candidate(self, ap_polra_num):
        """
        Takes AP's polra number and returns a Candidate object.
        """
        return self._candidates.get(ap_polra_num, None)
    
    def add_candidate(self, candidate):
        self._candidates.update({candidate.ap_polra_number: candidate})

    def get_reporting_unit(self, fips):
        """
        Get a single ReportingUnit
        """
        return self._reporting_units.get(fips, None)
    
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
        return self.get_reporting_unit('00000')
    
    @property
    def counties(self):
        """
        Returns all the counties that report results for this race as a list
        of ReportingUnit objects.
        """
        return [o for o in self.reporting_units if o.fips and not o.is_state]

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
    def results(self):
        """
        Returns the Result objects sorted by total votes (highest first)
        """
        return sorted(self._results.values(), key=lambda x: x.vote_total, reverse=True)
    
    def update_result(self, result):
        self._results[result.candidate.ap_polra_number] = result
    
    @property
    def is_state(self):
        return self.fips == '00000'


class Result(object):
    """
    The actual vote count for a candidate in a race in a particular reporting unit.
    
    Also, the percent reporting.
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
        return self.__unicode__()

    def __repr__(self):
        return u'<Result: %s>' % self.__unicode__()
