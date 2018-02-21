NAT Conntracker
===============

.. image:: https://travis-ci.org/travis-ci/nat-conntracker.svg?branch=master
    :target: https://travis-ci.org/travis-ci/nat-conntracker

It does things!

Usage
-----

Pipe in some conntrack XML::

  conntrack -o xml -E conntrack | nat-conntracker -
