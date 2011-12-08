import os
from ftplib import FTP
from tools import split_len, get_percentage
from ap.objects import Candidate, Race

class APResults(object):
    _parties = {
        'Lib': 'L',
        'Dem': 'D',
        'GOP': 'R',
        'Ind': 'I',
        'NP': None
    }

    def __init__(self, state, username=None, password=None, 
                    init_objects=True):
        """
        If init_objects is set to false, you must
        call the init function later before you
        pull the results down.
        """
        self.username = username
        self.password = password
        self.state = state
        self.candidates = {}
        self.reporting_units = {}
        self.races = {}

        if init_objects:
            self._init_objects()

    def get_candidates(self):
        return self.candidates.values()

    def get_candidates_for_race(self, race):
        """
        Takes an AP race number or a race object and returns
        the candidates for that race.
        """
        if type(race) == object:
            race = race.ap_race_number
        return [o for o in self.get_candidates() if o.ap_race_number == race]

    def get_races(self):
        return self.races.values()

    def _init_objects(self):
        ftp = FTP('electionsonline.ap.org', self.username, self.password) # Connect
        self._init_candidates(ftp)
        self._init_races(ftp)
        #self._init_reportingunits(ftp)
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

        self.candidates[candidate.combined_id] = candidate

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

        self.races[race.ap_number] = race

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
        pass

    def __unicode__(self):
        return self.state

    def __repr__(self):
        return u'<APResults: %s>' % self.__unicode__()
