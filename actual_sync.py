"""Actual Budget synchronization module."""

import hashlib
import os
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

import pandas as pd
from actual import Actual
from actual.queries import create_transaction, get_accounts, get_ruleset, get_transactions


# Account mapping: bank CSV source -> Actual Budget account name
DEFAULT_ACCOUNT_MAPPING = {
    'ibercaja': 'Ibercaja común',
    'ing_nomina': 'ING Nómina',
    'ing_naranja': 'ING Naranja',
}


@dataclass
class SyncResult:
    """Result of a sync operation."""
    success: bool
    imported: int = 0
    skipped: int = 0
    errors: list = None
    message: str = ""

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


def generate_imported_id(row: dict, source: str) -> str:
    """Generate a unique imported_id for a transaction to prevent duplicates."""
    # Create a hash from columns used in Actual Budget + Saldo for uniqueness
    unique_str = f"{source}|{row['Fecha Oper']}|{row['Concepto']}|{row['Descripción']}|{row['Importe']}|{row['Saldo']}"
    return hashlib.sha256(unique_str.encode()).hexdigest()[:32]


def parse_csv_date(date_str: str) -> datetime:
    """Parse date from CSV format (DD-MM-YYYY) to datetime."""
    return datetime.strptime(date_str, "%d-%m-%Y")


def parse_amount(amount) -> Decimal:
    """Convert amount to Decimal for Actual Budget."""
    # actualpy handles the conversion internally
    return Decimal(str(amount))


def get_account_by_name(session, account_name: str):
    """Find an account by name."""
    accounts = get_accounts(session)
    for account in accounts:
        if account.name == account_name:
            return account
    return None


def sync_csv_to_actual(
    csv_path: str,
    source: str,
    base_url: str,
    password: str,
    encryption_password: Optional[str],
    file_name: str,
    account_name: Optional[str] = None,
    account_mapping: Optional[dict] = None,
    cert_path: Optional[str] = None
) -> SyncResult:
    """
    Synchronize a CSV file to Actual Budget.

    Args:
        csv_path: Path to the CSV file
        source: Source identifier (ibercaja, ing_nomina, ing_naranja)
        base_url: Actual Budget server URL
        password: Server password
        encryption_password: File encryption password (optional)
        file_name: Budget file name in Actual
        account_name: Target account name (if not provided, uses account_mapping)
        account_mapping: Custom account name mapping (used if account_name not provided)
        cert_path: Path to self-signed certificate (optional)

    Returns:
        SyncResult with import statistics
    """
    # Use provided account_name, or fall back to mapping
    if not account_name:
        mapping = account_mapping or DEFAULT_ACCOUNT_MAPPING
        account_name = mapping.get(source)

    if not account_name:
        return SyncResult(
            success=False,
            message=f"No account name provided and no mapping found for source: {source}"
        )

    if not os.path.exists(csv_path):
        return SyncResult(
            success=False,
            message=f"CSV file not found: {csv_path}"
        )

    print(f"[ACTUAL] Reading CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"[ACTUAL] Found {len(df)} transactions")
    print(f"[ACTUAL] Columns: {list(df.columns)}")

    # Validate required columns
    required_cols = ['Fecha Oper', 'Concepto', 'Descripción', 'Importe']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        return SyncResult(
            success=False,
            message=f"CSV missing required columns: {missing_cols}. Found: {list(df.columns)}"
        )

    imported = 0
    skipped = 0
    errors = []

    try:
        print(f"[ACTUAL] Connecting to {base_url}...")
        # First connect without file to list available budgets
        with Actual(
            base_url=base_url,
            password=password,
            cert=False  # Skip SSL verification for self-signed certs
        ) as actual:
            # List available files
            files = actual.list_user_files()
            print(f"[ACTUAL] Available budgets:")
            for f in files.data:
                print(f"[ACTUAL]   - '{f.name}' (id: {f.file_id})")

        # Now connect with the specific file
        print(f"[ACTUAL] Opening budget: {file_name}")
        with Actual(
            base_url=base_url,
            password=password,
            encryption_password=encryption_password,
            file=file_name,
            cert=False  # Skip SSL verification for self-signed certs
        ) as actual:
            actual.download_budget()
            print("[ACTUAL] Budget downloaded")

            # Find account
            account = get_account_by_name(actual.session, account_name)
            if not account:
                return SyncResult(
                    success=False,
                    message=f"Account '{account_name}' not found in Actual Budget"
                )

            print(f"[ACTUAL] Found account: {account.name} (id: {account.id})")

            # Get existing transactions to check for duplicates
            existing_txs = get_transactions(actual.session)
            existing_ids = {t.financial_id for t in existing_txs if t.financial_id}

            # Import each transaction
            new_transactions = []
            for _, row in df.iterrows():
                try:
                    imported_id = generate_imported_id(row.to_dict(), source)

                    # Skip if already imported
                    if imported_id in existing_ids:
                        skipped += 1
                        continue

                    tx_date = parse_csv_date(row['Fecha Oper'])
                    amount = parse_amount(row['Importe'])

                    # Payee from Concepto (e.g., "TARJETA VISA", "Ventajas ING")
                    payee_name = str(row['Concepto'])[:50] if pd.notna(row['Concepto']) else None

                    # Notes from Descripción (e.g., "LM GETAFE MADRID", "Intereses a tu favor")
                    notes = str(row['Descripción']) if pd.notna(row['Descripción']) else None

                    tx = create_transaction(
                        actual.session,
                        date=tx_date,
                        account=account,
                        payee=payee_name,
                        notes=notes,
                        amount=amount,
                        imported_id=imported_id,
                        cleared=True  # Bank transactions are verified
                    )
                    new_transactions.append(tx)
                    imported += 1

                except Exception as e:
                    errors.append(f"Row {row.get('Nº Orden', '?')}: {str(e)[:50]}")

            # Apply rules only to new transactions
            if new_transactions:
                print(f"[ACTUAL] Applying rules to {len(new_transactions)} new transactions...", flush=True)
                ruleset = get_ruleset(actual.session)
                rules_applied = 0
                for tx in new_transactions:
                    for rule in ruleset.rules:
                        if rule.run(tx):
                            rules_applied += 1
                            actual.session.add(tx)
                if rules_applied > 0:
                    print(f"[ACTUAL] Applied {rules_applied} rule matches", flush=True)

            # Commit changes
            actual.commit()
            if imported > 0:
                print(f"[ACTUAL] Committed {imported} new transactions", flush=True)
            else:
                print("[ACTUAL] No new transactions to import", flush=True)

        return SyncResult(
            success=True,
            imported=imported,
            skipped=skipped,
            errors=errors,
            message=f"Synced to '{account_name}': {imported} imported, {skipped} skipped"
        )

    except Exception as e:
        return SyncResult(
            success=False,
            message=f"Connection error: {str(e)}"
        )


def get_latest_csv(bank: str) -> Optional[str]:
    """Get the path to the CSV for a bank."""
    paths = {
        'ibercaja': './downloads/ibercaja/ibercaja_movements.csv',
        'ing_nomina': './downloads/ing/ing_nomina.csv',
        'ing_naranja': './downloads/ing/ing_naranja.csv',
    }
    path = paths.get(bank)
    return path if path and os.path.exists(path) else None


def list_budget_files(base_url: str, password: str) -> list:
    """
    List available budget files in Actual Budget server.

    Args:
        base_url: Actual Budget server URL
        password: Server password

    Returns:
        List of dicts with 'name' and 'file_id' keys
    """
    try:
        with Actual(
            base_url=base_url,
            password=password,
            cert=False
        ) as actual:
            files = actual.list_user_files()
            return [{'name': f.name, 'file_id': f.file_id} for f in files.data]
    except Exception as e:
        print(f"[ERROR] Failed to list budget files: {str(e)}")
        return []


def list_accounts(base_url: str, password: str, file_name: str, encryption_password: Optional[str] = None) -> list:
    """
    List available accounts in a budget file.

    Args:
        base_url: Actual Budget server URL
        password: Server password
        file_name: Budget file name
        encryption_password: File encryption password (optional)

    Returns:
        List of dicts with 'name' and 'id' keys
    """
    try:
        with Actual(
            base_url=base_url,
            password=password,
            encryption_password=encryption_password,
            file=file_name,
            cert=False
        ) as actual:
            actual.download_budget()
            accounts = get_accounts(actual.session)
            return [{'name': account.name, 'id': account.id} for account in accounts if not account.closed]
    except Exception as e:
        print(f"[ERROR] Failed to list accounts: {str(e)}")
        return []
