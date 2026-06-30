import hashlib
import json
from time import time
class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        if not self.chain:  # creates genesis block
            self.new_block(previous_hash=1, proof=100)

    def new_block(self, proof, previous_hash=None):
        #initiates a new block to the blockchain
        block ={
            'index':len(self.chain) +1, #index
            'timestamp':time(), #time of creatin
            'proof':proof, #proof of instance
            'previous_hash': previous_hash or self.hash(self.chain[-1]), #pointer to previous block
        }
        #resets the current list of transactions
        self.current_transactions = []
        #appends latest block to the chain
        self.chain.append(block)
        return block
    
    def new_transactions(self,sender,recipient,ammount):
        """
        Creates a new transaction to go into the next mined Block
        :param sender: <str> Address of the Sender
        :param recipient: <str> Address of the Recipient
        :param amount: <int> Amount
        :return: <int> The index of the Block that will hold this transaction
        """
         
        #adds a new transaction to the list of transactions
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'ammount': ammount
        })
        return self.last_block['index']+1


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
    

    def proof_of_work(self, last_proof):
        """
        Simple Proof of Work Algorithm:
         - Find a number p' such that hash(pp') contains leading 4 zeroes, where p is the previous p'
         - p is the previous proof, and p' is the new proof
        :param last_proof: <int>
        :return: <int>
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof
    

    def valid_proof(last_proof, proof):
        """
        Validates the Proof: Does hash(last_proof, proof) contain 4 leading zeroes?
        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :return: <bool> True if correct, False if not.
        """

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"