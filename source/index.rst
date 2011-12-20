.. epigraph::

    A Python wrapper for the Associated Press' U.S. election data service

Features
========

* Easy access to AP election results for races in U.S. states and counties.

Requirements
============

In order to use this library, you must pay AP for access to the data. More information can be found on `the AP’s web site <http://www.apdigitalnews.com/ap_elections.html>`_ or by contacting Anthony Marquez at `amarquez@ap.org <mailto:amarquez@ap.org>`_.

Getting Started
===============

Install the library from PyPI.

.. code-block:: bash

    $ pip install python-elections

Once it's installed you can immediately begin accessing data with your AP login credentials. Here is quick example.

.. code-block:: python

    >>> from elections import AP
    >>> client = AP(uname, pwd)
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
    [<ReportingUnit: Adair>, <ReportingUnit: Adams>, <ReportingUnit: Allamakee>, <ReportingUnit: Appanoose>, <ReportingUnit: Audubon>, ...]
    >>> # And, of course, the results in each county.
    >>> iowa.races[0].counties[0].results
    [<Result: Michele Bachmann, Adair, 2496>, <Result: Newt Gingrich, Adair, 2219>, <Result: Rick Santorum, Adair, 191>, ...

