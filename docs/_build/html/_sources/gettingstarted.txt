Getting Started
===============

Provided that you have `pip <http://pypi.python.org/pypi/pip>`_ installed, you can install the library like so.

.. code-block:: bash

    $ pip install python-elections

If you'd rather work on the source code, you can clone it from GitHub using the usual methods.

.. code-block:: bash

    $ git clone https://github.com/datadesk/python-elections.git


Creating a client
-----------------

Before you can interact with AP's data, you first must import the library and initialize a client to talk with the FTP on your behalf. ::

    >>> from elections import AP
    >>> client = AP(USERNAME, PASSWORD)


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

