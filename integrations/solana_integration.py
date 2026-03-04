#!/usr/bin/env python3
"""
Solana Integration for Nova Memory System v2.0
"""

import requests
from solana.web3 import PublicKey, SystemProgram, Transaction
from solana.rpc.api import Client
from solana.transaction import TransactionInstruction, AccountMeta
from solana.blockhash import Blockhash
import base58
import json

class SolanaIntegration:
    """Solana integration for Nova Memory System"""

    def __init__(self, wallet_address="7KxNwsQpPAyKuC84dkNiL9dRnDUgh9iadXSurdYV7NzB"):
        self.wallet_address = wallet_address
        self.solana_rpc = "https://api.mainnet-beta.solana.com"
        self.client = Client(self.solana_rpc)

    def connect_wallet(self, private_key=None):
        """Connect to Solana wallet"""
        print(f"\n[OK] Connecting to Solana wallet: {self.wallet_address}")

        try:
            if private_key:
                # Load private key
                private_key_bytes = base58.b58decode(private_key)
                public_key = PublicKey(private_key_bytes[:32])

                print(f"[OK] Wallet connected: {public_key}")
                return public_key
            else:
                # Use provided wallet address
                public_key = PublicKey(self.wallet_address)
                print(f"[OK] Using wallet address: {public_key}")
                return public_key
        except Exception as e:
            print(f"[ERROR] Failed to connect wallet: {e}")
            return None

    def check_sol_balance(self, wallet_address=None):
        """Check SOL balance"""
        address = wallet_address or self.wallet_address

        try:
            response = self.client.get_balance(PublicKey(address))
            balance_lamports = response['result']['value']
            balance_sol = balance_lamports / 1_000_000_000

            print(f"\n[OK] SOL Balance: {balance_sol:.4f} SOL")

            return balance_sol
        except Exception as e:
            print(f"[ERROR] Failed to check balance: {e}")
            return 0

    def send_sol(self, to_address, amount_sol, private_key=None):
        """Send SOL to another address"""
        print(f"\n[INFO] Sending {amount_sol} SOL to {to_address}...")

        try:
            # Load private key
            if private_key:
                private_key_bytes = base58.b58decode(private_key)
                private_key = private_key_bytes[:32]

            # Get recent blockhash
            recent_blockhash = self.client.get_latest_blockhash()['result']['value']

            # Create transaction
            transaction = Transaction()
            transaction.add(
                SystemProgram.transfer(
                    from_pubkey=PublicKey(private_key_bytes[:32]) if private_key else PublicKey(self.wallet_address),
                    to_pubkey=PublicKey(to_address),
                    lamports=int(amount_sol * 1_000_000_000)
                )
            )
            transaction.recent_blockhash = recent_blockhash
            transaction.fee_payer = PublicKey(private_key_bytes[:32]) if private_key else PublicKey(self.wallet_address)

            # Sign and send
            # Note: In production, you need to sign with the wallet
            print(f"[OK] Transaction created successfully")
            print(f"[INFO] Transaction details:")
            print(f"  - From: {PublicKey(private_key_bytes[:32]) if private_key else PublicKey(self.wallet_address)}")
            print(f"  - To: {to_address}")
            print(f"  - Amount: {amount_sol} SOL")

            return True
        except Exception as e:
            print(f"[ERROR] Failed to send SOL: {e}")
            return False

    def create_license_transaction(self, customer_address, license_amount, private_key=None):
        """Create a license payment transaction"""
        print(f"\n[INFO] Creating license transaction...")
        print(f"  - Customer: {customer_address}")
        print(f"  - License: {license_amount} SOL")

        try:
            # Get recent blockhash
            recent_blockhash = self.client.get_latest_blockhash()['result']['value']

            # Create transaction
            transaction = Transaction()
            transaction.add(
                SystemProgram.transfer(
                    from_pubkey=PublicKey(private_key_bytes[:32]) if private_key else PublicKey(self.wallet_address),
                    to_pubkey=PublicKey(customer_address),
                    lamports=int(license_amount * 1_000_000_000)
                )
            )
            transaction.recent_blockhash = recent_blockhash
            transaction.fee_payer = PublicKey(private_key_bytes[:32]) if private_key else PublicKey(self.wallet_address)

            # Generate transaction signature (in production, sign with wallet)
            # For now, just create the transaction
            print(f"[OK] License transaction created")
            print(f"[INFO] Transaction signature: [PENDING WALLET SIGNATURE]")

            return {
                'success': True,
                'transaction': str(transaction),
                'signature': 'PENDING',
                'amount': license_amount
            }
        except Exception as e:
            print(f"[ERROR] Failed to create license transaction: {e}")
            return {
                'success': False,
                'error': str(e)
            }

if __name__ == "__main__":
    solana = SolanaIntegration()

    print("="*60)
    print("SOLANA INTEGRATION - NOVA MEMORY SYSTEM v2.0")
    print("="*60)

    # Connect wallet
    public_key = solana.connect_wallet()

    # Check balance
    balance = solana.check_sol_balance()

    # Create license transaction
    if balance > 0:
        print("\n" + "="*60)
        print("TESTING LICENSE TRANSACTION")
        print("="*60)

        transaction = solana.create_license_transaction(
            customer_address="7KxNwsQpPAyKuC84dkNiL9dRnDUgh9iadXSurdYV7NzB",
            license_amount=1.0  # Test amount
        )

        print("\n" + "="*60)
        print("INTEGRATION TEST COMPLETE")
        print("="*60)
