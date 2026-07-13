# Python P2P Blockchain

A functional, decentralized, peer-to-peer blockchain prototype built from scratch in Python using Flask. This project implements cryptographic identity, a transaction mempool, network consensus, and non-blocking node synchronization.

## Features

*   **Asymmetric Cryptography:** Uses 2048-bit RSA key pairs via the `cryptography` library. Public keys serve as wallet addresses. All transactions require a valid digital signature to prevent fraud.
*   **Asynchronous Propagation:** Block and transaction broadcasting are handled on background threads using Python's `threading` library, ensuring network latencies do not block the node's HTTP API.
*   **Secured Proof of Work:** Mining utilizes a SHA-256 algorithm requiring four leading zeros. The mining puzzle binds the current proof, the previous proof, and the `previous_hash` together to prevent pre-computation attacks.
*   **Decentralized Consensus:** Implements a Longest Chain Rule mechanism. Nodes query neighbors and automatically replace their local chain if a longer, valid chain is discovered.

## Prerequisites

*   Python 3.x
*   Flask
*   cryptography
*   requests

Install dependencies:
```bash
pip install Flask cryptography requests