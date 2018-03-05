NAT Conntracker
===============

.. image:: https://travis-ci.org/travis-ci/nat-conntracker.svg?branch=master
    :target: https://travis-ci.org/travis-ci/nat-conntracker

.. image:: https://codecov.io/gh/travis-ci/nat-conntracker/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/travis-ci/nat-conntracker

Tracking some conns!

Usage
-----

Pipe in some conntrack XML::

  conntrack -o xml -E conntrack | nat-conntracker -
