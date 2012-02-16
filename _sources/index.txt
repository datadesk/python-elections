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


Once it's installed you can immediately begin accessing data with your AP login credentials.

.. code-block:: python

    >>> # Request all the data available for a particular state by providing its postal code. This will return a state object.
    >>> iowa = client.get_state('IA')
    >>> iowa
    <State: IA>
    >>> # Among other things, the state has a list of races.
    >>> iowa.races
    [<Race: GOP Caucus - President>]
    >>> # The race contains a list of candidates.
    >>> iowa.races[0].candidates
    [<Candidate: Other>, <Candidate: Jon Huntsman>, <Candidate: Newt Gingrich>, <Candidate: Herman Cain>, <Candidate: Rick Santorum> ... 
    >>> # You can find results for the whole state.
    >>> iowa.races[0].state.results
    [<Result: Newt Gingrich, Iowa (state), 896249>, <Result: Michele Bachmann, Iowa (state), 879444>, <Result: Rick Perry, Iowa (state), 65426>, ...
    >>> # You can get all counties in the state.
    >>> iowa.races[0].counties
    [<ReportingUnit: Adair>, <ReportingUnit: Adams>, <ReportingUnit: Allamakee>, <ReportingUnit: Appanoose>, <ReportingUnit: Audubon>, ...
    >>> # And, of course, the results in each county.
    >>> iowa.races[0].counties[0].results
    [<Result: Michele Bachmann, Adair, 2496>, <Result: Newt Gingrich, Adair, 2219>, <Result: Rick Santorum, Adair, 191>, ...


