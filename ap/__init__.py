import os
from ftplib import FTP
from tools import split_len, get_percentage
from ap.objects import Candidate, Race, ReportingUnit, Result

class APResults(object):
    _parties = {
        'Lib': 'L',
        'Dem': 'D',
        'GOP': 'R',
        'Ind': 'I',
        'NP': None
    }

    def __init__(self, state, username=None, password=None, date=None,
                    init_objects=True):
        """
        If init_objects is set to false, you must
        call the init function later before you
        pull the results down.
        """
        self.username = username
        self.password = password
        self.state = state
        self.date = date
        self.candidates = {}
        self.reporting_units = {}
        self.races = {}
        self.state_results = {}

        if init_objects:
            self._init_objects()

    def get_candidate(self, ap_polra_num):
        return self.candidates.get(ap_polra_num, None)

    def get_candidates(self):
        """
        Get all candidates
        """
        return self.candidates.values()

    def get_candidates_for_race(self, race):
        """
        Takes an AP race number or a race object and returns
        the candidates for that race.
        """
        if isinstance(race, Race):
            race = race.ap_race_number
        return [o for o in self.get_candidates() if o.ap_race_number == race]

    def get_races(self):
        """
        Get all races
        """
        return self.races.values()

    def get_race(self, ap_race_number):
        """
        Get a single Race object by it's ap_race_number
        """
        return self.races.get(ap_race_number, None)

    def get_reporting_unit(self, fips):
        """
        Get a single ReportinUnit
        """
        return self.reporting_units.get(fips, None)

    def get_reporting_units(self):
        """
        Get all reporting units
        """
        return self.reporting_units.values()

    def get_counties(self):
        """
        Gets all reporting units that can be defined as counties.
        """
        return [o for o in self.get_reporting_units() if o.fips and not o.is_state]

    def get_state_results(self):
        """
        Gets all of the results in the state
        """
        return self.state_results.values()

    def get_state_results_for_race(self, race):
        """
        All results for a specific race
        """
        return [o for o in self.get_state_results() if o.race == race]

    def update_results(self):
        self._get_flat_results()

    def _init_objects(self):
        ftp = FTP('electionsonline.ap.org', self.username, self.password) # Connect
        self._init_candidates(ftp)
        self._init_races(ftp)
        self._init_reporting_units(ftp)
        ftp.quit()

    def _init_candidates(self, ftp):
        # Download state candidates file
        cali_dir = '/inits/%s/' % self.state
        cali_results = '%s_pol.txt' % self.state
        ftp.retrlines('RETR ' + os.path.join(cali_dir, cali_results), self._process_candidate_init_line)  

    def _process_candidate_init_line(self, line):
        """
        Takes a single line from the CA_pol.txt init file and turns it into a
        Candidate object.
        """
        POLRA_NUM, FNAME, MNAME, LNAME,\
        ABBRV, SFFX, PARTY, RA_NUM, NAT_NUM, = (0,1,2,3,4,5,6,7,8)

        bits = map(lambda x: x.strip(), line.split('|'))
        if len(bits) < 2:
            return
        del bits[0]
        del bits[-1]
        if 'polra' in bits[0]:
            return

        candidate = Candidate()
        candidate.state_abbrev = self.state,
        candidate.first_name = bits[FNAME]
        candidate.middle_name = bits[MNAME]
        candidate.last_name = bits[LNAME]
        candidate.ap_race_number = bits[RA_NUM]
        candidate.ap_natl_number = bits[NAT_NUM]
        candidate.ap_polra_number = bits[POLRA_NUM]
        candidate.combined_id = u'%s%s' % (self.state, candidate.ap_polra_number)
        candidate.abbrev_name = bits[ABBRV]
        candidate.suffix = bits[SFFX]
        candidate.party = self._parties.get(bits[PARTY])

        self.candidates.update({candidate.ap_polra_number: candidate})

    def _init_races(self, ftp):
        cali_dir = '/inits/%s/' % self.state
        cali_results = '%s_race.txt' % self.state
        ftp.retrlines('RETR ' + os.path.join(cali_dir, cali_results), self._process_race_init_line)   

    def _process_race_init_line(self, line):
        """
        Takes a single line from the CA_race.txt init file and turns it into a
        Race object.
        """
        RA_NUM, SEAT_NUM, OFF_ID, OFF_DESCRIP,\
        OFF_NAME, SEAT_NAME, SCOPE  = (0, 2, 4, 8, 10, 11, 12, )

        bits = map(lambda x: x.strip(), line.split('|'))
        if len(bits) < 2:
            return
        del bits[0]
        del bits[-1]
        if 'ra' in bits[0]:
            return

        race = Race() 
        race.ap_race_number = bits[RA_NUM]
        race.office_name = bits[OFF_NAME]
        race.office_descrip = bits[OFF_DESCRIP]
        race.office_id = bits[OFF_ID]
        race.seat_name = bits[SEAT_NAME]
        race.seat_number = bits[SEAT_NUM]
        race.scope = bits[SCOPE]

        self.races.update({race.ap_race_number: race})

    def _init_reporting_units(self, ftp):
        # Download California candidates file
        state_dir = '/inits/%s/' % self.state
        #TODO: How do we get US files when they're
        # coded by date? Do we ask for a date string
        # in the APResults init?
        #if self.state == 'US':
        #    cali_results = 'US_20101102_ru.txt'
        #else:
        results_file = '%s_ru.txt' % self.state
        ftp.retrlines('RETR ' + os.path.join(state_dir, results_file), self._process_ru_init_line)

    def _process_ru_init_line(self, line):
        """
        Takes a single line from the CA_ru.txt init file and turns it into a
        ReportingUnit object. With the exception of the state (ap_number: 1), all
        ReportingUnit objects should be counties.
        Will also load US states.
        """

        # The fields we want
        AP_NUMBER, NAME, ABBREV, FIPS, NUM_PRECINCTS, NUM_REG_VOTERS = (0,2,3,6,7,8)

        # Split it up and strip whitespace at the same time
        bits = map(lambda x: x.strip(), line.split('|'))
        if len(bits) < 2:
            return
        del bits[0]
        del bits[-1]
        if 'ru' in bits[0]:
            return

        ru = ReportingUnit()
        ru.name = bits[NAME]
        ru.ap_number = bits[AP_NUMBER]
        ru.fips = bits[FIPS]
        ru.abbrev = bits[ABBREV]
        ru.precincts_total = bits[NUM_PRECINCTS]
        ru.num_reg_voters = bits[NUM_REG_VOTERS]

        self.reporting_units.update({ru.fips: ru})

    def _get_flat_results(self):
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
            result.vote_total = cand[VOTE_COUNT]
            result.reporting_unit = reporting_unit
            result.precincts_reporting = int(primary_bits[PRECINCTS_REPORTING]),
            result.precincts_reporting_percent = get_percentage(result.precincts_reporting,
                                                    int(primary_bits[TOT_PRECINCTS]))

            reporting_unit.results.update({candidate.ap_polra_number: result})
            if is_state:
                # Set the state-wide result for this candidate
                self.state_results.update({candidate.ap_polra_number: result})

        # If this is a state-wide result
        if is_state:
            # Update the race with precinct reporting info
            race.precincts_total = primary_bits[TOT_PRECINCTS]
            race.precincts_reporting = primary_bits[PRECINCTS_REPORTING]
            race.precincts_reporting_percent =  get_percentage(float(race.precincts_reporting), 
                                                    float(race.precincts_total))
            race.votes_cast = votes_cast

            for candidate in self.get_candidates_for_race(race):
                candidate.vote_total_percent = get_percentage(candidate.vote_total, votes_cast)


    def __unicode__(self):
        return self.state

    def __repr__(self):
        return u'<APResults: %s>' % self.__unicode__()
