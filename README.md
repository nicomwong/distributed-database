# Distributed Key-Value Store via Multi-Paxos

## TL;DR
This project implements the "Multi-Paxos" version of the Paxos Consensus protocol which is harder but more more efficient than basic Paxos. At a high level, the protocol gaurantees the consistent replication of some arbitrary data structure across a distributed system as long as a majority of the servers are alive.

This implementation maintains a key-value store among *N* servers being consumed by *M* clients. Clients can issue 'put' or 'get' requests to the K-V store. The two distributed data structures in this implementation are a key-value store and a blockchain. The key-value store is stored as multiple instances across the servers and must be managed by the distributed protocol. The blockchain is a transaction log replicated on every server used to validate consistency of the key-value store.

One of the difficulties is that many clients can be sending many requests at a time. To handle this, the protocol implements some concept of server "leader"-ship, "nomination", and "election". When a key-value pair is sent to the leader, it goes through various phases to replicate the data while maintaining fault-tolerance and ensuring data consistency across the servers. 

## How to use it?

1. this implementation assumes a permissioned system, so the user must specify the number of servers. To do this:

* in **server.py**, set `Server.numServers` to the number of desired servers **N**.
* in **client.py**, set `Client.numServers` to **N**.

<br/>

2. start the servers and clients. Note that each server or client must be run in its own process (e.g. a separate bash process).

* start the servers by running `$ python3 server.py <serverID>` **N** times with `serverID = 1, 2, 3, ..., N`.
   * for example, if `numServers = 3`, then run `$ python3 server.py 1`, `$ python3 server.py 2`, and `$ python3 server.py 3` on seperate terminals.

* start the client(s) by running `$ python3 client.py <clientID>` once for each desired client and each with a unique `clientID` in the set `{1, 2, 3, ..., 999}`.
   * for example, if you want 2 clients, you can run `$ python3 client.py 1` and `$ python3 client.py 4` on separate terminals.

<br/>

3. initiate commands through a client! The available commands are as follows:
* `get <key>` where `key` is a Python literal such as `"a string"`, `'a string'`, `1`, `{'key1':'val1'}`, etc.
* `put <key> <value>` where `key` and `value` are Python literals.

<br/>

4. wait for a query response to be received.

## Data structures

#### Key-Value Store
The key-value (or K-V) store is the primary data structure being served to the clients.

#### Blockchain
The blockchain serves as a transaction log. At a conceptual level, it is a distributed, finite state machine whose main purpose is to maintain data consistency across the cluster. 

## Machines

#### Servers
The servers each have a key-value store whose contents reflect the current state of the server's blockchain, which is essentially a log of the transactions (that the server knows of at the moment).

The servers communicate with each other and propogate requests to the "leader" server. The "leader" server then initiates the next stage of the protocol (read more from the wiki page.) Which server is the "leader" fluctuates depending on the state of the system. More details can be found in the wikipedia page.

#### Clients
Clients can request transactions that conflict with each other in data or in time. For example, the same key could be getting modified; or, two different clients could be sending requests at the same time, but which one gets picked first?

## Misc. Notes
#### How is the network simulated?
Various timeout variables are used in the client and server classes. Timeout simulates a time delay when any message is passed across the network.

#### More understanding
The wikipedia page for the Paxos consensus protocol: https://en.wikipedia.org/wiki/Paxos_(computer_science)

#### Final Notes
Have fun, and play with it! It's really fun to play with, actually. You can set `debugMode` to `True` [here](https://github.com/nicomwong/paxosBlockChain/blob/main/client.py#L12) and [here](https://github.com/nicomwong/paxosBlockChain/blob/main/server.py#L45) to see the requests and responses in real-time. (They are output to stdout.)

###### Project of UCSB CS 171 Distributed Systems
