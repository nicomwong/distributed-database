# Paxos Block Chain

From UCSB CS 171 Distributed Systems

This project implements the Paxos protocol for consensus in a distributed system. This specific implementation gaurantees the consistency of a replicated, append-only block chain and key-value store.


# How to Use

First, This implementation assumes a permissioned system, so the user must specify the number of servers. To do this:

* In **server.py**, set `Server.numServers` to the number of desired servers.

* In **client.py**, set `Client.numServers` to the _same_ number.
