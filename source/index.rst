.. epigraph::

    A Python wrapper for the Associated Press' U.S. election data service

Features
========

* Easy access to AP election results for races in U.S. states and counties.
* Easy access to presidential election results for the nation, the 50 states and all U.S. counties.
* Easy access to AP’s delegate estimates in presidential nomination contests.

.. raw:: html

   <hr>

Requirements
============

In order to use this library, you must pay AP for access to the data. More information can be found on `the AP’s web site <http://www.apdigitalnews.com/ap_elections.html>`_ or by contacting Anthony Marquez at `amarquez@ap.org <mailto:amarquez@ap.org>`_.

.. raw:: html

   <hr>

In The Wild
===========

* `Los Angeles Times <http://graphics.latimes.com/2012-election-gop-primary-overview/>`_ 
* `Chicago Tribune <http://media.apps.chicagotribune.com/2012-elections/nh-primary.html>`_
* `Chicago Tribune, again <http://elections.chicagotribune.com/results/>`_
* `Washington Times <http://www.washingtontimes.com/campaign-2012/FL/live-map/>`_ 
* `Palm Beach Post <http://www.palmbeachpost.com/news/see-results-from-every-florida-county-on-our-2140533.html>`_ 
* `Tampa Bay Times <http://www.tampabay.com/specials/2012/reports/2012FloridaElectionResults/presidential_primary.shtml>`_ 
* `Spokane Spokesman-Review <http://www.spokesman.com/elections/2012/idaho-primary-2012/>`_

.. raw:: html

   <hr>

Getting Started
===============

Provided that you have `pip <http://pypi.python.org/pypi/pip>`_ installed, you can install the library like so.

.. code-block:: bash

    $ pip install python-elections

If you'd rather work on the source code, you can clone it from GitHub using the usual methods.

.. code-block:: bash

    $ git clone https://github.com/datadesk/python-elections.git

.. raw:: html

   <hr>

Creating a client
-----------------

Before you can interact with AP's data, you first must import the library and initialize a client to talk with the FTP on your behalf. ::

    >>> from elections import AP
    >>> client = AP(USERNAME, PASSWORD)

.. raw:: html

   <hr>

Some basics
-----------

Request all the data available for a particular state by providing its postal code. This will return a state object.

.. code-block:: python

    >>> ca = client.get_state('CA')
    >>> ca
    <State: CA>

Among other things, the state has a list of races.

.. code-block:: python

    >>> ca.races
    [<Race: District Attorney Los Angeles>, <Race: U.S. House District 49 - Carlsbad>, <Race: U.S. House District 50 - Escondido>, <Race: U.S. House District 51 - El Centro>, <Race: U.S. House District 53 - El Cajon>, <Race: State Senate District 1 - Redding>, <Race: State Senate District 5 - Stockton>, <Race: State Senate District 7 - Concord>, <Race: State Senate District 9 - Oakland>, <Race: State Senate District 11 - San Francisco>, <Race: State Assembly District 59 - Los Angeles>, <Race: State Assembly District 58 - Norwalk>, <Race: State Assembly District 61 - Riverside>, <Race: State Assembly District 60 - Riverside>, <Race: State Assembly District 63 - Lakewood>, <Race: State Assembly District 62 - Inglewood>, <Race: State Assembly District 65 - Anaheim>, <Race: State Assembly District 64 - Compton>, <Race: State Assembly District 67 - Murrieta>, <Race: State Assembly District 66 - Torrance>,  ...]
    >>> prez = ca.filter_races(office_name='President')[0]
    >>> prez
    <Race: President>

The race contains a list of candidates.

    >>> prez.candidates
    [<Candidate: Roseanne Barr>, <Candidate: Thomas Hoefling>, <Candidate: Gary Johnson>, <Candidate: Barack Obama>, <Candidate: Mitt Romney>, <Candidate: Jill Stein>]

You can find results for the whole state.

.. code-block:: python

    >>> prez.state.results
    [<Result: Barack Obama, California (state), 3698001>, <Result: Mitt Romney, California (state), 3469304>, <Result: Roseanne Barr, California (state), 657614>, <Result: Jill Stein, California (state), 585121>, <Result: Thomas Hoefling, California (state), 110465>, <Result: Gary Johnson, California (state), 109602>]

You can get all counties in the state.

.. code-block:: python

    >>> prez.counties
    [<ReportingUnit: Alameda>, <ReportingUnit: Alpine>, <ReportingUnit: Amador>, <ReportingUnit: Butte>, <ReportingUnit: Calaveras>, <ReportingUnit: Colusa>, <ReportingUnit: Contra Costa>, <ReportingUnit: Del Norte>, <ReportingUnit: El Dorado>, <ReportingUnit: Fresno>, <ReportingUnit: Glenn>, <ReportingUnit: Humboldt>, <ReportingUnit: Imperial>, <ReportingUnit: Inyo>, <ReportingUnit: Kern>, <ReportingUnit: Kings>, <ReportingUnit: Lake>, <ReportingUnit: Lassen>, <ReportingUnit: Los Angeles>, <ReportingUnit: Madera>, <ReportingUnit: Marin>, <ReportingUnit: Mariposa>, <ReportingUnit: Mendocino>, <ReportingUnit: Merced>, <ReportingUnit: Modoc>, <ReportingUnit: Mono>, <ReportingUnit: Monterey>, <ReportingUnit: Napa>, <ReportingUnit: Nevada>, <ReportingUnit: Orange>, <ReportingUnit: Placer>, <ReportingUnit: Plumas>, <ReportingUnit: Riverside>, <ReportingUnit: Sacramento>, <ReportingUnit: San Benito>, <ReportingUnit: San Bernardino>, <ReportingUnit: San Diego>, <ReportingUnit: San Francisco>, <ReportingUnit: San Joaquin>, <ReportingUnit: San Luis Obispo>, <ReportingUnit: San Mateo>, <ReportingUnit: Santa Barbara>, <ReportingUnit: Santa Clara>, <ReportingUnit: Santa Cruz>, <ReportingUnit: Shasta>, <ReportingUnit: Sierra>, <ReportingUnit: Siskiyou>, <ReportingUnit: Solano>, <ReportingUnit: Sonoma>, <ReportingUnit: Stanislaus>, <ReportingUnit: Sutter>, <ReportingUnit: Tehama>, <ReportingUnit: Trinity>, <ReportingUnit: Tulare>, <ReportingUnit: Tuolumne>, <ReportingUnit: Ventura>, <ReportingUnit: Yolo>, <ReportingUnit: Yuba>]


And, of course, the results in each county.

.. code-block:: python

    >>> prez.counties[0].results
    [<Result: Barack Obama, Alameda, 160048>, <Result: Mitt Romney, Alameda, 152934>, <Result: Roseanne Barr, Alameda, 29060>, <Result: Jill Stein, Alameda, 26147>, <Result: Thomas Hoefling, Alameda, 4966>, <Result: Gary Johnson, Alameda, 4912>]

.. raw:: html

   <hr>

A working example
-----------------

Let’s say, hypothetically, that the United States is electing a president for the next four years, and your news or­gan­iz­a­tion bought ac­cess to the AP’s FTP ser­vice for California results. Your boss wants you to write a simple wid­get that will sit on the homepage and out­put live res­ults. All you need are the can­did­ate names, their vote totals and per­cent­ages, the num­ber of pre­cincts re­port­ing and wheth­er the AP has called a win­ner yet. How do you feed it? Here's how.

.. code-block:: python

    from elections import AP
    try:
        import json
    except ImportError:
        import simplejson as json

    client = AP(uname, pwd)
    calif = client.get_state('CA') 
    # Now the calif variable holds all of the AP result data
    prez = iowa.filter_races(office_name='President')[0] 
    # prez is a Race object containing the results of the presidential race

    # Set up the main data dict and set the percent of precincts reporting
    data = {
        'precincts_reporting_percent': prez.state.precincts_reporting_percent,
        'candidates': []
    }

    # Loop through the statewide candidate results, and append them
    # in a format we like into the data dict's candidate list.
    for result in prez.state.results:
        data['candidates'].append({
            'name': result.candidate.last_name,
            'vote_total': result.vote_total,
            'vote_percent': result.vote_total_percent,
            'is_winner': result.candidate.is_winner,
        })

    # Then dump the data dict out as JSON
    print json.dumps(data, indent=4)

There you have it: a simple JSON dump in about 20 lines of code. From here, you can set this script to up­load the JSON file every few minutes to Amazon S3 or a sim­il­ar file-serving ser­vice. Then point your front-end wid­get to pull from there.

.. raw:: html

   <hr>


The AP Client
=============

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

..   function:: client.get_presidential_summary()

    Returns a summary of presidential election results at three levels: nationwide popular vote and electoral vote; state-level popular vote and electoral vote; county-level popular vote.

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

.. raw:: html

   <hr>

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

.. raw:: html

   <hr>

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

.. raw:: html

   <hr>

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

.. raw:: html

   <hr>

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

.. raw:: html

   <hr>


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

.. raw:: html

   <hr>


Delegate Summary Collections
============================

Calling delegate related methods, like `get_delegate_summary` will return a slightly different, and simpler, result collection. To start, you should receive a list containing two Nomination objects.

.. raw:: html

   <hr>

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

.. raw:: html

   <hr>

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

.. raw:: html

   <hr>

Changelog
=========

0.30
----

* Added delegate summary method thanks to contributions of David Eads.

0.20
----

* Added `get_topofticket` methods thanks to contributions by Corey Oordt.

beta
----

* Added all the basic features for the first release

.. raw:: html

   <hr>

Authors
=======

* Ken Schwencke
* `Ben Welsh <http://palewire.com/who-is-ben-welsh/>`_
* Corey Oordt
* David Eads

