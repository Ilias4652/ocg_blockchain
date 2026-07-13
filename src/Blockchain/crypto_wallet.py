import digital_signature

class CryptoWallet:
    def __init__(self, blockchain):
        self.blockchain = blockchain
        if not digital_signature.private_key_exists() or not digital_signature.public_key_exists():
            digital_signature.create_key_pair()
            
        self.private_key = digital_signature.load_private_key()
        self.public_key = digital_signature.load_public_key()
        # Store the string representation of the key for JSON transfers
        self.address = digital_signature.get_address(self.public_key)
    
    def get_balance(self):
        balance = 0
        for block in self.blockchain.chain:
            for transaction in block.get('transactions', []):
                if transaction['recipient'] == self.address:
                    balance += transaction['amount']
                elif transaction['sender'] == self.address:
                    balance -= transaction['amount']
                    
        for transaction in self.blockchain.current_transactions:
            if transaction['recipient'] == self.address:
                balance += transaction['amount']
            elif transaction['sender'] == self.address:
                balance -= transaction['amount']
                
        return balance
    
    def create_transaction(self, recipient, amount):
        if self.get_balance() < amount:
            raise ValueError("Insufficient balance.")
            
        return self.blockchain.new_transactions(
            sender=self.address,
            recipient=recipient,
            amount=amount
        )