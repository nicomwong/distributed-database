# Paxos Block Chain

From UCSB CS 171 Distributed Systems

## The Concept

#### TL;DR
This project implements the "Multi-Paxos" version of Paxos Consensus protocol, which is a harder but more capable version of the basic protocol. At a high level, the protocol gaurantees the consistent replication of some arbitrary data structure across a distributed system as long as the majority of the servers are alive.

This implementation maintains a key-value store among *N* servers being consumed by *M* clients. Clients request that the K-V store be updated by a transaction. Many clients can be sending many requests at a time. To handle this, the protocol implements some concept of server "leader"-ship, "nomination" of the leader, and an "election" round, and the clients try to figure out who the leader is at any given moment. The key-value store is the primary data being served and the blockchain just serves as a transaction log for each server to maintain consistency.

#### Key-Value Store
The key-value (or K-V) store is the primary data structure being served to the clients.

#### Blockchain
The blockchain serves as a transaction log. At a conceptual level, it is a distributed, finite state machine whose main purpose is to maintain data consistency across the cluster. 

#### Servers
The servers each have a key-value store whose contents reflect the current state of the server's blockchain, which is essentially a log of the transactions (that the server knows of at the moment).

The servers communicate with each other and propogate requests to the "leader" server. The "leader" server then initiates the next stage of the protocol (read more from the wiki page.) Which server is the "leader" fluctuates depending on the state of the system. More details can be found in the wikipedia page.

#### Clients
Clients can request transactions that conflict with each other in data or in time. For example, the same key could be getting modified; or, two different clients could be sending requests at the same time, but which one gets picked first?

#### More Notes
The wikipedia page for the Paxos consensus protocol: https://en.wikipedia.org/wiki/Paxos_(computer_science)

## How do I use it?

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

## Final Notes
Have fun, and play with it! It's really fun to play with, actually. You can set `debugMode` to `True` [here](https://github.com/nicomwong/paxosBlockChain/blob/main/client.py#L12) and [here](https://github.com/nicomwong/paxosBlockChain/blob/main/server.py#L45) to see the requests and responses in real-time. (They are output to stdout.)
