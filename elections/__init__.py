import os
import csv
from ftplib import FTP
from datetime import date
from cStringIO import StringIO
from utils import split_len, get_percentage, strip_dict
from objects import Candidate, Race, ReportingUnit, Result


class AP(object):
    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password

    def get_state(self, state=None, *args, **kwargs):
        return APResults(state, self.username, self.password, *args, **kwargs)


class APResults(object):
    _parties = {
        'Lib': 'L',
        'Dem': 'D',
        'GOP': 'R',
        'Ind': 'I',
        'NP': None
    }
    
    def __init__(self, state, username=None, password=None, results=True):
        """
        If init_objects is set to false, you must
        call the init function later before you
        pull the results down.
        """
        self.username = username
        self.password = password
        self.state = state
        self._candidates = {} # All candidates keyed by AP's `ap_polra_number` ID.
        self._reporting_units = {}
        self._races = {}
        
        self.ftp = FTP('electionsonline.ap.org', self.username, self.password) # Connect
        self._init_races()
        self._init_candidates()
        self._init_reporting_units()
        if results:
            self.fetch_results(self.ftp)
        else:
            # Probably goofy, but fetch_results quits the
            # FTP, so we only need to quit if results=False
            self.ftp.quit()
    
    def __unicode__(self):
        return self.state
    
    def __repr__(self):
        return u'<APResults: %s>' % self.__unicode__()
    
    #
    # Public methods
    #
    
    def get_candidate(self, ap_polra_num):
        """
        Takes AP's polra number and returns a Candidate object.
        """
        return self._candidates.get(ap_polra_num, None)
    
    @property
    def candidates(self):
        """
        Get all candidates
        """
        return self._candidates.values()
    
    def get_race(self, ap_race_number):
        """
        Get a single Race object by it's ap_race_number
        """
        return self._races.get(ap_race_number, None)
    
    @property
    def races(self):
        """
        Get all races
        """
        return self._races.values()
    
    def get_reporting_unit(self, fips):
        """
        Get a single ReportinUnit
        """
        return self._reporting_units.get(fips, None)
    
    @property
    def reporting_units(self):
        """
        Get all reporting units
        """
        return self._reporting_units.values()
    
    @property
    def counties(self):
        """
        Gets all reporting units that can be defined as counties.
        """
        return [o for o in self.reporting_units if o.fips and not o.is_state]
    
    def fetch_results(self, ftp=None):
        """
        This will fetch and fill out all of the results. If called again,
        it will simply run through and update all of the results with 
        the most fresh data from the AP.
        """
        self._get_flat_results(ftp)
    
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
        self.ftp.retrbinary(cmd, buffer.write)
        reader = csv.DictReader(StringIO(buffer.getvalue()), delimiter='|')
        return [strip_dict(i) for i in reader]
    
    def _init_candidates(self):
        """
        Download the state's candidate file and load the data.
        """
        # Fetch the data from the FTP
        candidate_list = self._fetch_csv("/inits/%(state)s/%(state)s_pol.txt" % self.__dict__)
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
                combined_id = u'%s%s' % (self.state, cand['polra_number']),
                abbrev_name = cand['pol_abbrv'],
                suffix = cand['pol_junior'],
                party = self._parties.get(cand['polra_party']),
                # use_suffix?
            )
            # And add it to the global data stores
            self._candidates.update({candidate.ap_polra_number: candidate})
            self._races[candidate.ap_race_number].add_candidate(candidate)
    
    def _init_races(self):
        """
        Download all the races in the state and load the data.
        """
        # Get the data
        race_list = self._fetch_csv("/inits/%(state)s/%(state)s_race.txt" % self.__dict__)
        # Loop through it all
        for race in race_list:
            # Create a Race object...
            race = Race(
                ap_race_number = race['ra_number'],
                office_name = race['ot_name'],
                office_description = race['of_description'],
                office_id = race['office_id'],
                seat_name = race['se_name'],
                seat_number = race['se_number'],
                scope = race['of_scope'],
                date = date(*map(int, [race['el_date'][:4], race['el_date'][4:6], race['el_date'][6:]])),
                num_winners = race['ra_num_winners'],
                party = self._parties.get(race['rt_party_name']),
                uncontested = race['ra_uncontested'],
            )
            # And add it to the global store
            self._races.update({race.ap_race_number: race})
    
    def _init_reporting_units(self):
        """
        Download all the reporting units and load the data.
        """
        # Get the data
        ru_list = self._fetch_csv("/inits/%(state)s/%(state)s_ru.txt" % self.__dict__)
        # Loop through them all
        for ru in ru_list:
            # Create ReportingUnit objects...
            ru = ReportingUnit(
                name = ru['ru_name'],
                ap_number = ru['ru_number'],
                fips = ru['ru_fip'],
                abbrev = ru['ru_abbrv'],
                precincts_total = ru['ru_precincts'],
                num_reg_voters = ru['ru_reg_voters'],
            )
            # And add them to the global store
            self._reporting_units.update({ru.fips: ru})
    
    def _get_flat_results(self, ftp=None):
        if not ftp:
            ftp = FTP('electionsonline.ap.org', self.username, self.password) # Connect
        
        # Download state results file
        if self.state == 'US':
            file_dir = '/US_topofticket/flat/'
        else:
            file_dir = '/%s/flat/' % self.state
        results_file = '%s.txt' % self.state
        
        ftp.retrlines('RETR ' + os.path.join(file_dir, results_file), self._process_flat_results_line)  
        ftp.quit()
    
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
        
        is_state = primary_bits[COUNTY_NUM] == '1'
        
        if primary_bits[FIPS] == '0':
            primary_bits[FIPS] = '00000'
        reporting_unit = self.get_reporting_unit(primary_bits[FIPS])
        race = self.get_race(bits[RACE_NUM]) 
        
        votes_cast = 0
        for cand in candidate_bits:
            candidate = self.get_candidate(cand[CANDIDATE_NUM])
            if is_state:
                # Update the overall vote total if it's state-wide
                candidate.vote_total = int(cand[VOTE_COUNT])
                # And the total votes cast so far in the election
                votes_cast += candidate.vote_total
            candidate.is_winner = cand[IS_WINNER] == 'X'
            candidate.is_runoff = cand[IS_WINNER] == 'R'
            
            result = Result()
            result.race = race
            result.candidate = candidate
            result.vote_total = int(cand[VOTE_COUNT])
            result.reporting_unit = reporting_unit
            result.precincts_reporting = int(primary_bits[PRECINCTS_REPORTING])
            result.precincts_reporting_percent = get_percentage(result.precincts_reporting,
                                                    int(primary_bits[TOT_PRECINCTS]))
            
            reporting_unit._results.update({candidate.ap_polra_number: result})
            if is_state:
                # Set the state-wide result for this candidate
                race._state_results.update({candidate.ap_polra_number: result})
        
        # If this is a state-wide result
        if is_state:
            # Update the race with precinct reporting info
            race.precincts_total = int(primary_bits[TOT_PRECINCTS])
            race.precincts_reporting = int(primary_bits[PRECINCTS_REPORTING])
            race.precincts_reporting_percent =  get_percentage(float(race.precincts_reporting), 
                                                    float(race.precincts_total))
            race.votes_cast = votes_cast
            
            for candidate in race.candidates:
                candidate.vote_total_percent = get_percentage(candidate.vote_total, votes_cast)
