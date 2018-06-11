# Bakasable

Bakasable is a attempt to create a decentralized multiplayer game using [NDN](https://named-data.net/).

The project will focus on the following points:
 - distributed the game objects to the peers equally;
 - performing action on local or remote game objects;
 - broadcasting objects updates to peers that need them;
 - distributing the game logic between peers (computer controlled entities, reacting to player action);
 - prefetching of potential needed objects by a peer.

However the following points will not be covered:
 - preventing cheating;
 - reacting to unplanned peer disconnection (network fault or application killed).

The logic of the protocol used for this game has been inspired by the following papers :
 - B. Knutsson, Honghui Lu, Wei Xu and B. Hopkins, "Peer-to-peer support for massively multiplayer games," IEEE INFOCOM 2004, 2004, pp. 107.
 - Christophe Diot and Laurent Gautier, "A Distributed Architecture for Multiplayer Interactive Applications on the Internet", IEEE Networks magazine vol. 13, 1999, pp. 6-15.
 - Ashwin R. Bharambe and Jeff Pang and Srinivasan Seshan, "A Distributed Architecture for Interactive Multiplayer Games", 2005.
