===========================
The Associated Press client
===========================

Retrieving data
===============

The AP client is public class you can use to connect to the AP's data feed.

.. function:: client.get_state(state_postal_code)

   Takes a single state postal code, returns that state's results. ::

        >>> from elections import AP
        >>> client = AP(USERNAME, PASSWORD)
        >>> client.get_state('IA')
        <State: IA>

.. function:: client.get_states(*state_postal_codes)

   Takes one to many state postal codes as arguments, returns a list of results for the requested states. ::

        >>> from elections import AP
        >>> client = AP(USERNAME, PASSWORD)
        >>> client.get_states('IA', 'NH')
        [<State: IA>, <State: NH>]

.. function:: client.get_topofticket(election_date)

   Top of the ticket is an AP data service that provides limited results on the top races for all 50 states (i.e. President, Governor, US Senate, and US House). It requires a date in any common format, YYYY-MM-DD is preferred, and returns all results for that date. ::

   If you do not provide a date, it defaults to the next major election. Today that is the Nov. 6, 2012 general election.

        >>> from elections import AP
        >>> client = AP(USERNAME, PASSWORD)
        >>> client.get_topofticket('2012-02-07')
        <TopOfTicket: 20120207>

..   function:: client.get_presidential_summary(districts=False)

    Returns a summary of presidential election results at three levels: nationwide popular vote and electoral vote; state-level popular vote and electoral vote; county-level popular vote.

    If `districts` is provided and set to True the results will include Congressional district-level results in the two states that break out their presidential electors: Maine and Nebraska. This feature only works if the AP has given your account access to the ME and NE data folders. By default, `districts` is set to False.

        >>> from elections import AP
        >>> client = AP(USERNAME, PASSWORD)
        >>> client.get_presidential_summary()
        <PresidentialSummary: None>

.. function:: client.get_delegate_summary()

   Return a nationwide summary and state-level totals contain delegate counts for all the candidates in the presidential nomination contest held by the two major parties.

   **Warning:** This method does not currently work because the 2012 primaries are over and the AP has removed the folders it depends on.

        >>> from elections import AP
        >>> client = AP(USERNAME, PASSWORD)
        >>> client.documents.get_delegate_summary()
        [<Nomination: Dem>, <Nomination: GOP>]

.. raw:: html
 
   <hr>

Election Result Collections
===========================

Depending on which client method you use to harvest data, results may be returned as `State` or `TopOfTicket` objects. Don't worry about the distinction, because they act pretty much the same. They share the following attributes for you to use.

.. attribute:: obj.counties

    Returns a list of all the counties from the pool of reporting units.

        >>> obj = client.get_state('IA')
        >>> obj.counties
        [<ReportingUnit: Guthrie>, <ReportingUnit: Union>, <ReportingUnit: Crawford>, <ReportingUnit: Wright>, <ReportingUnit: Tama>, <ReportingUnit: Hamilton>, <ReportingUnit: Worth>, <ReportingUnit: Hancock>, <ReportingUnit: Cherokee>, <ReportingUnit: Carroll>, <ReportingUnit: Webster>, <ReportingUnit: Clarke>, ...]

.. function:: obj.filter_races(**kwargs)

   Takes a series of keyword arguments and returns any races that match.
        
        >>> obj = client.get_state('IA')
        >>> obj.filter_races(office_name='President', party='GOP')
        [<Race: GOP Caucus - President>]

.. attribute:: obj.races

    Returns a list of all the races reporting results.

        >>> obj = client.get_state('IA')
        >>> obj.races
        [<Race: GOP Caucus - President>]

.. attribute:: obj.reporting_units

    Returns a list of all reporting units in the result collection.

        >>> obj = client.get_state("IA")
        >>> obj.reporting_units
        [<ReportingUnit: Guthrie>, <ReportingUnit: Union>, <ReportingUnit: Crawford>, <ReportingUnit: Wright>, <ReportingUnit: Tama>, <ReportingUnit: Hamilton>, <ReportingUnit: Worth>, <ReportingUnit: Hancock>, <ReportingUnit: Cherokee>, <ReportingUnit: Carroll>, <ReportingUnit: Webster>, <ReportingUnit: Clarke>, ...]

.. attribute:: obj.states

      Returns a list of all the states from the pool of reporting units. Only available on `TopOfTicket` result collections.

        >>> obj = client.get_topofticket('2012-02-07')
        >>> obj.states
        [<ReportingUnit: Missouri (state)>, <ReportingUnit: Minnesota (state)>, <ReportingUnit: Colorado (state)>]


Races
-----

A contest being decided by voters choosing between candidates. This object is the key to everything about it. It is often found in the `races` attribute of a result collection.

.. attribute:: obj.ap_race_number

    AP-assigned race number. Race numbers are guaranteed to be unique only within a state.

        >>> obj.ap_race_number
        '16957'

.. attribute:: obj.candidates

    The list of candidates participating in the race.

        >>> obj.candidates
        [<Candidate: Michele Bachmann>, <Candidate: Herman Cain>, <Candidate: Newt Gingrich>, <Candidate: Jon Huntsman>, <Candidate: No Preference>, <Candidate: Other>, <Candidate: Ron Paul>, <Candidate: Rick Perry>, <Candidate: Buddy Roemer>, <Candidate: Mitt Romney>, <Candidate: Rick Santorum>]

.. attribute:: obj.counties

    Returns all the counties that report results for this race as a list.

        >>> obj.counties
        [<ReportingUnit: Adair>, <ReportingUnit: Adams>, <ReportingUnit: Allamakee>, <ReportingUnit: Appanoose>, <ReportingUnit: Audubon>, <ReportingUnit: Benton>, <ReportingUnit: Black Hawk>, <ReportingUnit: Boone>, <ReportingUnit: Bremer>, <ReportingUnit: Buchanan>, ...

.. attribute:: obj.date

    The date of the election in Python's datetime format.

        >>> obj.date
        datetime.date(2012, 1, 3)

.. attribute:: obj.is_primary

    Returns `True` if the race is a primary.

.. attribute:: obj.is_caucus

    Returns `True` if the race is a caucus.

.. attribute:: obj.is_general

    Returns `True` if the race is part of a general election.

.. attribute:: obj.name

    The name of the race.

        >>> obj.name
        'GOP Caucus - President'

.. attribute:: obj.num_winners

    Integer giving the maximum number of winners.

        >>> obj.num_winners
        1

.. attribute:: obj.office_name

    Character string for office name (e.g., U.S. House, Governor, etc.)

        >>> obj.office_name
        'President'

.. attribute:: obj.office_description

    Character string further describing the office type. May be empty.

.. attribute:: obj.office_id

    Single character Office Type ID. Only top-of-the-ticket races (President, Governor, US Senate, and US House) are guaranteed to be unique on a national level. All other office types are guaranteed to be unique only within a state. A full list of the office identifiers can be found in AP's documentation.

.. attribute:: obj.party

    Name of party to which race applies, i.e., GOP if a Republican Primary.

.. attribute:: obj.race_type_name

    Returns a descriptive name for the race_type.

        >>> obj.race_type_name
        'GOP Caucus'

.. attribute:: obj.reporting_units

    Returns all reporting units that belong to this race as a list.

        >>> obj.reporting_units
        [<ReportingUnit: Guthrie>, <ReportingUnit: Union>, <ReportingUnit: Crawford>, <ReportingUnit: Wright>, <ReportingUnit: Tama>, <ReportingUnit: Hamilton>, <ReportingUnit: Worth>, <ReportingUnit: Hancock>, <ReportingUnit: Cherokee>, <ReportingUnit: Carroll>, ...

.. attribute:: obj.scope

    Office scope – whether the race is a Local (L) or Statewide (S) race

        >>> obj.scope
        'S'

.. attribute:: obj.state

    Returns the state-level results for this race as a ReportingUnit object.

        >>> obj.state
        <ReportingUnit: Iowa (state)>

.. attribute:: obj.seat_name

    Character string giving the district or initiative name (e.g., District 46, 1A-Gay Marriage, etc.) This may be empty for a statewide race (e.g., a Governor race).

.. attribute:: obj.seat_number

    Integer indicating district number or an initiative number. This may be zero (0) for a statewide race.

.. attribute:: obj.state_postal

    Two character state postal string (e.g., IA, LA, etc.).

.. attribute:: self.uncontested

    Returns `True` is the race is uncontested.

.. attribute:: self.is_referendum

    Returns `True` if this is a race where the people vote to decide about a law, measure, proposition, amendment, etc.


Reporting Units
---------------

An area or unit that groups votes into a total. For instance, a state, a congressional district, a county.

.. attribute:: obj.abbrev

    Short Name of reporting unit

        >>> obj.abbrev
        'Poweshiek'

.. attribute:: obj.ap_number

    Unique ID within a state for reporting unit.

        >>> obj.ap_number
        '16079'

.. attribute:: obj.name

    The full name of the reporting unit

        >>> obj.name
        'Poweshiek'

.. attribute:: obj.fips

    The unique FIPS code for this reporting unit, assigned by the U.S. government.

        >>> obj.fips
        '19157'

.. attribute:: obj.num_reg_voters

    The number of registered votes who live in this reporting unit.

        >>> obj.num_reg_voters
        3897

.. attribute:: obj.votes_cast

    The number of votes cast in this reporting unit.

        >>> obj.votes_cast
        709

.. attribute:: obj.precincts_total

    The number of voting precincts in this reporting unit.

        >>> obj.precincts_total
        10

.. attribute:: obj.precincts_reporting

    The number of precincts that have already provided results.

        >>> obj.precincts_reporting
        10

.. attribute:: obj.precincts_reporting_percent

    The percentage of precincts that have already provided results.

        >>> obj.precincts_reporting_percent
        100.0

.. attribute:: obj.results

    Returns a list of result objects sorted by total votes (highest first). If no votes are in, it returns the candidates in alphabetical order.

    >>> obj.results
    [<Result: Rick Santorum, Iowa (state), 29839>, <Result: Mitt Romney, Iowa (state), 29805>, <Result: Ron Paul, Iowa (state), 26036>, <Result: Newt Gingrich, Iowa (state), 16163>, <Result: Rick Perry, Iowa (state), 12557>, <Result: Michele Bachmann, Iowa (state), 6046>, <Result: Jon Huntsman, Iowa (state), 739>, <Result: No Preference, Iowa (state), 147>, <Result: Other, Iowa (state), 107>, <Result: Herman Cain, Iowa (state), 45>, <Result: Buddy Roemer, Iowa (state), 17>]

.. attribute:: obj.is_state

    Returns `True` if the reporting unit is a state, rather than some other unit like a county.

.. attribute:: obj.electoral_votes_total

    Returns the number of presidential electors this area controls. Typically only found on states.


Candidates
----------

A choice for voters in a race. In the presidential race, a person, like Barack Obama. In a ballot measure, a direction, like Yes or No.

.. attribute:: obj.abbrev_name

    Candidate's abbreviated name, usually last name with some vowels removed if too long.

        >>> obj.abbrev_name
        'Bchmnn'

.. attribute:: obj.ap_natl_number

    Unique ID to identify this politician across states and races.

        >>> obj.ap_natl_number
        '302'

.. attribute:: obj.ap_pol_number

    Unique ID within a state for this candidate.

        >>> obj.ap_pol_number
        '18538'

.. attribute:: obj.ap_polra_number

    Unique ID within a state for this candidate for this race for their party.

        >>> obj.ap_polra_number
        '21304'

.. attribute:: obj.ap_race_number

    Unique ID within a state for the race object this candidate object is linked to.

        >>> obj.ap_race_number
        '16957'

.. attribute:: obj.delegates

    The number of delegates the candidate has won in this state, according to AP's estimates. Warning: AP has told The Times that it stops updating these totals after they decide a race has "closed" following the election. That means that if you want to track changes to these totals between the vote and the eventual nomination, you should use the nationwide delegate methods detailed below.

        >>> obj.delegates
        0

.. attribute:: obj.first_name

    The first name of the candidate.

        >>> obj.first_name
        'Michele'

.. attribute:: obj.is_winner

    Returns `True` if the candidate has won the race.

.. attribute:: obj.is_runoff

    Returns `True` is the candidate is advancing to a runoff.

.. attribute:: obj.last_name

    The last name of the candidate.

        >>> obj.last_name
        'Bachmann'

.. attribute:: obj.middle_name

    The middle name of the candidate. Might not always exist.

        >>> obj.middle_name
        'J.'

.. attribute:: obj.name

    The full name of candidate.

        >>> obj.name
        u'Michele Bachmann'

.. attribute:: obj.party

    Candidate's party abbreviation.

        >>> obj.party
        'GOP'

.. attribute:: obj.suffix

    The suffix to the candidate's name. Might not exist.

        >>> obj.suffix
        'Jr.'

.. attribute:: obj.use_suffix

    Returns `True` if you should use the suffix with the name.


Result
------

The vote count for a candidate in a race in a particular reporting unit.

.. attribute:: obj.candidate

    The candidate this result is for.

        >>> obj.candidate
        <Candidate: Rick Santorum>

.. attribute:: obj.reporting_unit

    The reporting unit this result is for.

        >>> obj.reporting_unit
        <ReportingUnit: Iowa (state)>

.. attribute:: obj.vote_total

    The number of votes the candidate has collected in this reporting unit.

        >>> obj.vote_total
        29839

.. attribute:: obj.vote_total_percent

    The percentage of the tpta; votes the candidate has collected in this reporting unit.

        >>> obj.vote_total_percent
        24.558645607855077

.. attribute:: obj.electoral_votes_total

    Returns the number of presidential electors awarded by this result.



Presidential Summary Collections
================================

Calling presidential methods, like `get_presidential_summary` will return a slightly different, and simpler, result collection.

.. attribute:: obj.nationwide

    Returns only the nationwide reporting unit.

        >>> obj.nationwide
        <ReportingUnit: US>

.. attribute:: obj.states

    Returns only the state-level reporting units

        >>> obj.states
        [<ReportingUnit: South Carolina (state)>, <ReportingUnit: North Carolina (state)>, <ReportingUnit: Delaware (state)>, <ReportingUnit: Florida (state)>, <ReportingUnit: District of Columbia (state)>, <ReportingUnit: Indiana (state)>, <ReportingUnit: New Mexico (state)>, <ReportingUnit: Washington (state)>, <ReportingUnit: Oregon (state)>, <ReportingUnit: New Hampshire (state)>, <ReportingUnit: Nebraska (state)>, <ReportingUnit: North Dakota (state)>, ...]

.. attribute:: obj.counties

    Returns only the county-level reporting units

        >>> obj.counties
        [<ReportingUnit: Abbeville>, <ReportingUnit: Aiken>, <ReportingUnit: Allendale>, <ReportingUnit: Anderson>, <ReportingUnit: Bamberg>, <ReportingUnit: Barnwell>, <ReportingUnit: Beaufort>, <ReportingUnit: Berkeley>, <ReportingUnit: Calhoun>, <ReportingUnit: Charleston>, <ReportingUnit: Cherokee>, <ReportingUnit: Chester>, <ReportingUnit: Chesterfield>, <ReportingUnit: Clarendon>, <ReportingUnit: Colleton>, <ReportingUnit: Darlington>, <ReportingUnit: Dillon>, <ReportingUnit: Dorchester>, <ReportingUnit: Edgefield>, <ReportingUnit: Fairfield>...]

.. attribute:: obj.districts

    Returns only Congressional district-level results in the two states that break out their presidential electors: Maine and Nebraska. This feature only works if `districts` is set to True and passed into the `get_presidential_summary` model.

        >>> prez = client.get_presidential_summary(districts=True)
        >>> prez.districts
        [<ReportingUnit: ME District 2>, <ReportingUnit: ME District 1>, <ReportingUnit: NE District 2>, <ReportingUnit: NE District 3>, <ReportingUnit: NE District 1>]



Delegate Summary Collections
============================

Calling delegate related methods, like `get_delegate_summary` will return a slightly different, and simpler, result collection. To start, you should receive a list containing two Nomination objects.


Nominations
-----------

A contest to be the presidential nominee of one of the two major parties.

.. attribute:: obj.candidates

    The list of candidates participating in the race.

        >>> obj.candidates
        [<Candidate: Michele Bachmann>, <Candidate: Herman Cain>, <Candidate: Newt Gingrich>, <Candidate: Jon Huntsman>, <Candidate: No Preference>, <Candidate: Other>, <Candidate: Ron Paul>, <Candidate: Rick Perry>, <Candidate: Buddy Roemer>, <Candidate: Mitt Romney>, <Candidate: Rick Santorum>]

.. attribute:: obj.delegates_needed

    The number of delegates needed to capture the nomination.

.. attribute:: obj.delegates_total

    The total number of delegates available.

.. attribute:: obj.delegates_chosen

    The total number of delegates that have been awarded.

.. attribute:: obj.delegates_chosen_percent

    The percentage of the total delegates that have been awarded.

.. attribute:: obj.party

    Candidate's party abbreviation.

        >>> obj.party
        'GOP'

.. attribute:: obj.states

      Returns a list of all the state delegates we have counts for.

        >>> obj.states
        [<StateDelegation: AK>, <StateDelegation: AL>, <StateDelegation: AR>, <StateDelegation: AS>, <StateDelegation: AZ>, <StateDelegation: CA>, <StateDelegation: CO>, <StateDelegation: CT>, <StateDelegation: DC>, <StateDelegation: DE>, <StateDelegation: FL>, <StateDelegation: GA>, <StateDelegation: GU>, <StateDelegation: HI>, <StateDelegation: IA>, <StateDelegation: ID>, <StateDelegation: IL>, <StateDelegation: IN>, ...]


State Delegations
-----------------

A state's delegation and who they choose to be a party's presidential nominee.

.. attribute:: obj.candidates

    The list of candidates participating in the race.

        >>> obj.candidates
        [<Candidate: Michele Bachmann>, <Candidate: Herman Cain>, <Candidate: Newt Gingrich>, <Candidate: Jon Huntsman>, <Candidate: No Preference>, <Candidate: Other>, <Candidate: Ron Paul>, <Candidate: Rick Perry>, <Candidate: Buddy Roemer>, <Candidate: Mitt Romney>, <Candidate: Rick Santorum>]

.. attribute:: obj.name

    The name of the state. The AP only provides the postal code.

        >>> obj.name
        'IA'

