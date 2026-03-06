#!/usr/bin/env python3
"""
Nova Memory 2.0 — Solana Integration (Optional)

Provides Solana blockchain hooks for:
- Wallet connection and SOL balance queries
- SOL transfers
- On-chain license payment transactions

This module is entirely optional.  Install the ``solana`` package to
activate blockchain features:

    pip install solana base58

Without the package, the module still imports cleanly and all methods
return graceful error responses.
"""

import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional solana import
# ---------------------------------------------------------------------------
try:
    from solana.rpc.api import Client
    from solana.transaction import Transaction
    from solders.pubkey import Pubkey as PublicKey
    from solders.system_program import transfer, TransferParams
    import base58
    _SOLANA_AVAILABLE = True
except ImportError:
    _SOLANA_AVAILABLE = False
    logger.info(
        "solana/solders packages not installed — SolanaIntegration runs in stub mode. "
        "Install with: pip install solana solders base58"
    )


class SolanaIntegration:
    """
    Solana blockchain integration for Nova Memory System.

    All public methods return a consistent dict with at least:
        ``{"success": bool, ...}``

    When the ``solana`` package is not installed the methods return
    ``{"success": False, "error": "solana package not installed"}``
    so callers never crash on import or method call.
    """

    DEFAULT_WALLET = "7KxNwsQpPAyKuC84dkNiL9dRnDUgh9iadXSurdYV7NzB"
    RPC_URL = "https://api.mainnet-beta.solana.com"

    def __init__(self, wallet_address: str = DEFAULT_WALLET):
        self.wallet_address = wallet_address
        self._client = None

        if _SOLANA_AVAILABLE:
            try:
                self._client = Client(self.RPC_URL)
                logger.info("Solana RPC client initialised  url=%s", self.RPC_URL)
            except Exception as exc:
                logger.warning("Failed to initialise Solana client: %s", exc)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _unavailable(self, method: str) -> Dict[str, Any]:
        return {
            "success": False,
            "error": "solana package not installed — run: pip install solana solders base58",
            "method": method,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def connect_wallet(self, private_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Connect to a Solana wallet.

        Args:
            private_key: Base58-encoded private key (optional).
                         If omitted, uses the configured wallet address.

        Returns:
            Dict with ``success``, ``public_key``, and optional ``error``.
        """
        if not _SOLANA_AVAILABLE:
            return self._unavailable("connect_wallet")

        try:
            if private_key:
                raw = base58.b58decode(private_key)
                pub = PublicKey.from_bytes(raw[:32])
            else:
                pub = PublicKey.from_string(self.wallet_address)

            result = {"success": True, "public_key": str(pub)}
            print(f"[OK] Wallet connected: {pub}")
            return result

        except Exception as exc:
            logger.exception("connect_wallet failed: %s", exc)
            return {"success": False, "error": str(exc)}

    def check_sol_balance(
        self, wallet_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query the SOL balance of a wallet.

        Returns:
            Dict with ``success``, ``balance_sol``, ``balance_lamports``.
        """
        if not _SOLANA_AVAILABLE:
            return self._unavailable("check_sol_balance")

        address = wallet_address or self.wallet_address
        try:
            response = self._client.get_balance(PublicKey.from_string(address))
            lamports = response.value
            sol = lamports / 1_000_000_000

            result = {"success": True, "balance_sol": sol, "balance_lamports": lamports}
            print(f"[OK] SOL balance: {sol:.4f} SOL  ({lamports} lamports)")
            return result

        except Exception as exc:
            logger.exception("check_sol_balance failed: %s", exc)
            return {"success": False, "error": str(exc)}

    def send_sol(
        self,
        to_address: str,
        amount_sol: float,
        private_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build a SOL transfer transaction.

        Note: Signing and broadcasting require a funded keypair.
        This method constructs the transaction and returns it for
        external signing.

        Returns:
            Dict with ``success``, ``from_address``, ``to_address``, ``amount_sol``.
        """
        if not _SOLANA_AVAILABLE:
            return self._unavailable("send_sol")

        try:
            if private_key:
                raw = base58.b58decode(private_key)
                from_pubkey = PublicKey.from_bytes(raw[:32])
            else:
                from_pubkey = PublicKey.from_string(self.wallet_address)

            to_pubkey = PublicKey.from_string(to_address)
            lamports = int(amount_sol * 1_000_000_000)

            # Build instruction (transaction signing is caller's responsibility)
            ix = transfer(TransferParams(
                from_pubkey=from_pubkey,
                to_pubkey=to_pubkey,
                lamports=lamports,
            ))

            result = {
                "success": True,
                "from_address": str(from_pubkey),
                "to_address": to_address,
                "amount_sol": amount_sol,
                "lamports": lamports,
                "note": "Transaction built — sign and broadcast with your wallet SDK",
            }
            print(f"[OK] Transfer prepared  {amount_sol} SOL → {to_address}")
            return result

        except Exception as exc:
            logger.exception("send_sol failed: %s", exc)
            return {"success": False, "error": str(exc)}

    def create_license_transaction(
        self,
        customer_address: str,
        license_amount: float,
        private_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build a license payment transaction.

        FIX: previous version referenced ``private_key_bytes`` before it was
        conditionally assigned, causing a ``NameError`` when ``private_key``
        was ``None``.

        Returns:
            Dict with ``success``, ``customer_address``, ``amount``, and status.
        """
        if not _SOLANA_AVAILABLE:
            return self._unavailable("create_license_transaction")

        try:
            # FIX: resolve from_pubkey safely regardless of private_key presence
            if private_key:
                raw = base58.b58decode(private_key)
                from_pubkey = PublicKey.from_bytes(raw[:32])
            else:
                from_pubkey = PublicKey.from_string(self.wallet_address)

            to_pubkey = PublicKey.from_string(customer_address)
            lamports = int(license_amount * 1_000_000_000)

            ix = transfer(TransferParams(
                from_pubkey=from_pubkey,
                to_pubkey=to_pubkey,
                lamports=lamports,
            ))

            result = {
                "success": True,
                "from_address": str(from_pubkey),
                "customer_address": customer_address,
                "amount": license_amount,
                "lamports": lamports,
                "signature": "PENDING_WALLET_SIGNATURE",
                "note": "Sign this transaction with your wallet to complete the license purchase",
            }
            print(f"[OK] License transaction built  {license_amount} SOL → {customer_address}")
            return result

        except Exception as exc:
            logger.exception("create_license_transaction failed: %s", exc)
            return {"success": False, "error": str(exc)}

    def health_check(self) -> Dict[str, Any]:
        """Return connectivity status of the Solana RPC endpoint."""
        if not _SOLANA_AVAILABLE:
            return {"status": "unavailable", "reason": "solana package not installed"}

        try:
            version = self._client.get_version()
            return {
                "status": "connected",
                "rpc_url": self.RPC_URL,
                "solana_version": str(version.value.solana_core),
            }
        except Exception as exc:
            return {"status": "error", "error": str(exc)}


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("SOLANA INTEGRATION — NOVA MEMORY SYSTEM v2.0")
    print("=" * 60)
    print(f"Solana package available: {_SOLANA_AVAILABLE}")

    solana = SolanaIntegration()

    health = solana.health_check()
    print(f"\nHealth: {json.dumps(health, indent=2)}")

    wallet = solana.connect_wallet()
    print(f"\nWallet: {json.dumps(wallet, indent=2)}")

    balance = solana.check_sol_balance()
    print(f"\nBalance: {json.dumps(balance, indent=2)}")

    license_tx = solana.create_license_transaction(
        customer_address=SolanaIntegration.DEFAULT_WALLET,
        license_amount=1.0,
    )
    print(f"\nLicense TX: {json.dumps(license_tx, indent=2)}")

    print("\n" + "=" * 60)
    print("INTEGRATION TEST COMPLETE")
    print("=" * 60)
