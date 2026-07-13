
from textwrap import dedent
from time import time
from uuid import uuid4
import json
from flask import Flask, jsonify, request
import Blockchain
import requests
from urllib.parse import urlparse
from urllib.parse import urlparse
app = Flask(__name__)

node_identifier = str(uuid4()).replace('-','')

blockchain = Blockchain.Blockchain()

def broadcast_payload(endpoint, payload, nodes):
    for node in nodes:
        try:
            requests.post(f"http://{node}{endpoint}", json=payload, timeout=2)
        except requests.exceptions.RequestException:
            continue

@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    previous_hash = blockchain.hash(last_block)
    
    # Pass previous_hash to secure the proof
    proof = blockchain.proof_of_work(last_proof, previous_hash)
    
    blockchain.new_transactions(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )
    block = blockchain.new_block(proof, previous_hash)
    
    # Broadcast asynchronously
    threading.Thread(target=broadcast_payload, args=('/blocks/receive', block, list(blockchain.nodes))).start()

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200
 
@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    sender = values['sender']
    recipient = values['recipient']
    amount = values['amount']
    signature = values.get('signature')

    if signature:
        for tx in blockchain.current_transactions:
            if tx.get('signature') == signature:
                return jsonify({'message': 'Transaction already processed.'}), 200

    try:
        index = blockchain.new_transactions(sender, recipient, amount, signature=signature)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    full_tx = blockchain.current_transactions[-1]

    # Broadcast asynchronously
    threading.Thread(target=broadcast_payload, args=('/transactions/new', full_tx, list(blockchain.nodes))).start()

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')  # List of node URLs to register
    sender_node = values.get('sender_node')  # The address of the node sending this request

    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    # --- MUTUAL CALLBACK LOGIC ---
    # If a sender_node identifier accompanies the payload, Node B can call Node A back 
    # ONLY if Node A is not already recorded in Node B's tracking pool.
    if sender_node:
        parsed_sender = urlparse(sender_node).netloc
        if parsed_sender not in blockchain.nodes:
            # Add it locally first
            blockchain.register_node(sender_node)
            
            # Construct a callback payload containing Node B's own address.
            try:
                # Node B sends a registration payload back to Node A
                # We do not pass 'sender_node' in this callback to prevent an infinite recursive ping-pong.
                requests.post(f"{sender_node}/nodes/register", json={
                    'nodes': [f"http://localhost:5000"] 
                }, timeout=2)
            except requests.exceptions.RequestException:
                pass

    response = {
        'message': 'New nodes have been synchronized successfully',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200


@app.route('/blocks/receive', methods=['POST'])
def receive_block():
    block = request.get_json()
    if not block or not all(k in block for k in ['index', 'proof', 'previous_hash', 'transactions']):
        return "Invalid block format", 400

    last_block = blockchain.last_block
    
    # CASE 1: Incoming block is ahead of our current chain by exactly 1
    if block['index'] == last_block['index'] + 1:
        # Validation
        is_hash_valid = block['previous_hash'] == blockchain.hash(last_block)
        is_proof_valid = blockchain.valid_proof(last_block['proof'], block['proof'])
        
        if is_hash_valid and is_proof_valid:
            blockchain.chain.append(block)
            
            # Wipe out matching pending transactions from local mempool
            incoming_signatures = {tx.get('signature') for tx in block['transactions'] if tx.get('signature')}
            blockchain.current_transactions = [
                tx for tx in blockchain.current_transactions 
                if tx.get('signature') not in incoming_signatures
            ]
            
            return jsonify({'message': 'Block accepted and appended.'}), 200
        else:
            return jsonify({'message': 'Block validation failed.'}), 400

    # CASE 2: The node missed a few blocks (desynchronization)
    elif block['index'] > last_block['index'] + 1:
        # Trigger internal synchronization routine
        replaced = blockchain.resolve_conflicts()
        if replaced:
            return jsonify({'message': 'Chain out of date. Synced with neighbors.'}), 200
        return jsonify({'message': 'Out of sync block received, consensus fallback failed.'}), 400

    # CASE 3: Stale or old block
    return jsonify({'message': 'Block rejected; obsolete index.'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)




