.. epigraph::

    A Python wrapper for the Associated Press' U.S. election data service

Features
========

* Easy access to AP election results for races in U.S. states and counties.

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
* `Washington Times <http://www.washingtontimes.com/campaign-2012/FL/live-map/>`_ 
* `Palm Beach Post <http://www.palmbeachpost.com/news/see-results-from-every-florida-county-on-our-2140533.html>`_ 

.. raw:: html

   <hr>


Getting Started
===============

**Installation**  

Provided that you have `pip <http://pypi.python.org/pypi/pip>`_ installed, you can install the library like so.

.. code-block:: bash

    $ pip install python-elections

If you'd rather work on the source code, you can clone it from GitHub using the usual methods.

.. code-block:: bash

    $ git clone https://github.com/datadesk/python-elections.git

.. raw:: html

   <hr>

**Creating a client**

Before you can interact with AP's data, you first must import the library and initialize a client to talk with the FTP on your behalf. ::

    >>> from elections import AP
    >>> client = AP(USERNAME, PASSWORD)

.. raw:: html

   <hr>

**Some basics**

Request all the data available for a particular state by providing its postal code. This will return a state object.

.. code-block:: python

    >>> iowa = client.get_state('IA')
    >>> iowa
    <State: IA>

Among other things, the state has a list of races.

.. code-block:: python

    >>> iowa.races
    [<Race: GOP Caucus - President>]

The race contains a list of candidates.

.. code-block:: python

    >>> iowa.races[0].candidates
    [<Candidate: Other>, <Candidate: Jon Huntsman>, <Candidate: Newt Gingrich>, <Candidate: Herman Cain>, <Candidate: Rick Santorum> ... 

You can find results for the whole state.

.. code-block:: python

    >>> iowa.races[0].state.results
    [<Result: Newt Gingrich, Iowa (state), 896249>, <Result: Michele Bachmann, Iowa (state), 879444>, <Result: Rick Perry, Iowa (state), 65426>, ...

You can get all counties in the state.

.. code-block:: python

    >>> iowa.races[0].counties
    [<ReportingUnit: Adair>, <ReportingUnit: Adams>, <ReportingUnit: Allamakee>, <ReportingUnit: Appanoose>, <ReportingUnit: Audubon>, ...

And, of course, the results in each county.

.. code-block:: python

    >>> iowa.races[0].counties[0].results
    [<Result: Michele Bachmann, Adair, 2496>, <Result: Newt Gingrich, Adair, 2219>, <Result: Rick Santorum, Adair, 191>, ...

.. raw:: html

   <hr>

**A working example**

Let’s say the GOP is hold­ing its caucuses in Iowa, and your news or­gan­iz­a­tion bought ac­cess to the AP’s FTP ser­vice. Your boss wants you to write a simple wid­get that will sit on the homepage and out­put live res­ults. All you need are the can­did­ate names, their vote totals and per­cent­ages, the num­ber of pre­cincts re­port­ing, the num­ber of del­eg­ates won and wheth­er the AP has called a win­ner yet. How do you feed it? Here's how.

.. code-block:: python

    from elections import AP
    try:
        import json
    except ImportError:
        import simplejson as json

    client = AP(uname, pwd)
    iowa = client.get_state('IA') 
    # Now the iowa variable holds all of the AP result data
    caucus = iowa.filter_races(office_name='President', party='GOP')[0] 
    # caucus is a Race object containing the results of the GOP caucuses

    # Set up the main data dict and set the percent of precincts reporting
    data = {
        'precincts_reporting_percent': caucus.state.precincts_reporting_percent,
        'candidates': []
    }

    # Loop through the statewide candidate results, and append them
    # in a format we like into the data dict's candidate list.
    for result in caucus.state.results:
        data['candidates'].append({
            'name': result.candidate.last_name,
            'vote_total': result.vote_total,
            'vote_percent': result.vote_total_percent,
            'delegate_total': result.candidate.delegates,
            'is_winner': result.candidate.is_winner,
        })

    # Then dump the data dict out as JSON
    print json.dumps(data, indent=4)

There you have it: a simple JSON dump in about 20 lines of code. From here, you can set this script to up­load the JSON file every few minutes to Amazon S3 or a sim­il­ar file-serving ser­vice. Then point your front-end wid­get to pull from there.

.. raw:: html

   <hr>
