import hashlib
import json
from time import time
from urllib.parse import urlparse
import requests
import digital_signature


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        if not self.chain:  # creates genesis block
            self.new_block(previous_hash=1, proof=100)
        self.nodes = set()
        
    def new_block(self, proof, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions, # <-- Don't forget to include them!
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        
        # Now it's safe to reset the pending transactions list
        self.current_transactions = []
        self.chain.append(block)
        return block
    
    def new_transactions(self,sender,recipient,ammount,signature=None):
     def new_transactions(self, sender, recipient, amount, signature=None):
        transaction = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        }
        
        tx_string = json.dumps(transaction, sort_keys=True) 
        
        if signature is None:
            private_key = digital_signature.load_private_key()
            signature = digital_signature.create_digital_signature(private_key, tx_string)
            is_valid = digital_signature.verify_digital_signature(digital_signature.load_public_key(), signature, tx_string)
        else:
            # Reconstruct the public key from the string address
            sender_pub_key = digital_signature.load_public_key_from_address(sender)
            is_valid = digital_signature.verify_digital_signature(sender_pub_key, signature, tx_string)
            
        if not is_valid:
            raise ValueError("Invalid transaction signature! Transaction rejected.")
            
        transaction['signature'] = signature
        self.current_transactions.append(transaction)
        return self.last_block['index'] + 1

    # --- UPDATED PROOF OF WORK ---
    def proof_of_work(self, last_proof, previous_hash):
        proof = 0
        while self.valid_proof(last_proof, proof, previous_hash) is False:
            proof += 1
        return proof
    
    @staticmethod
    def valid_proof(last_proof, proof, previous_hash):
        # Now secures the actual chain state, preventing pre-computation
        guess = f'{last_proof}{proof}{previous_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def register_node(self,address):
        """
        Add a new node to the list of nodes
        :param address: <str> Address of node. Eg. 'http://
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
    @staticmethod
    def hash(block):
        #hashes a block by creating a a SHA-256 hash of a Block
         # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()


    @property
    def last_block(self):
        #returns the last block of blockchain
        return self.chain[-1]
    


    
    def valid_chain(self,chain):
        """
        Determine if a given blockchain is valid
        :param chain: <list> A blockchain
        :return: <bool> True if valid, False if not
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True
    

    def resolve_conflicts(self):
        """
        This is our consensus algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.
        :return: <bool> True if our chain was replaced, False if not
        """
        neighbours = self.nodes
        new_chain = None

        max_length = len(self.chain)
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        if new_chain:
            self.chain = new_chain
            return True

        return False