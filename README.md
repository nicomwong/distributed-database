# Paxos Block Chain

From UCSB CS 171 Distributed Systems

This project implements the Paxos protocol for fault-tolerant consensus in a distributed system. This specific implementation gaurantees the consistency of a replicated, append-only block chain and key-value store.


# How to Use

First, this implementation assumes a permissioned system, so the user must specify the number of servers. To do this:

* In **server.py**, set `Server.numServers` to the number of desired servers **N**.
* In **client.py**, set `Client.numServers` to **N**.

<br/>

Second, start the servers and clients. Note that each server or client must be run in its own process (e.g. a separate bash process).

* Start the servers by running `$ python3 server.py <serverID>` **N** times with `serverID = 1, 2, 3, ..., N`.
   * For example, if `numServers = 3`, then run `$ python3 server.py 1`, `$ python3 server.py 2`, and `$ python3 server.py 3` on seperate terminals.

* Start the client(s) by running `$ python3 client.py <clientID>` once for each desired client and each with a unique `clientID` in the set `{1, 2, 3, ..., 999}`.
   * For example, if you want 2 clients, you can run `$ python3 client.py 1` and `$ python3 client.py 4` on separate terminals.

<br/>

Third, initiate commands through a client! The available commands are as follows:
* `get <key>` where `key` is a Python literal such as `"a string"`, `'a string'`, `1`, `{'key1':'val1'}`, etc.
* `put <key> <value>` where `key` and `value` are Python literals.

<br/>

Fourth, wait for a query response to be received.

# Fault-Tolerance

As long as at least a majority of servers is alive (> **N**/2), the three [Paxos properties](https://en.wikipedia.org/wiki/Paxos_(computer_science)#Safety_and_liveness_properties) hold.

To test this, you can pass the following commands to the _server_ processes:
* `failProcess` simulates a server crash
* `failLink <destinationPort>` breaks the link between the current server and the machine with the given destination port
* `fixLink <destinationPort>` fixes the link (_i.e._ undoes `failLink`)
