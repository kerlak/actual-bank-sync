"""Actual Budget synchronization module."""

import hashlib
import os
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

import pandas as pd
from actual import Actual
from actual.queries import create_transaction, get_accounts, get_transactions


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
        account_mapping: Custom account name mapping
        cert_path: Path to self-signed certificate (optional)

    Returns:
        SyncResult with import statistics
    """
    mapping = account_mapping or DEFAULT_ACCOUNT_MAPPING
    account_name = mapping.get(source)

    if not account_name:
        return SyncResult(
            success=False,
            message=f"No account mapping found for source: {source}"
        )

    if not os.path.exists(csv_path):
        return SyncResult(
            success=False,
            message=f"CSV file not found: {csv_path}"
        )

    print(f"[ACTUAL] Reading CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"[ACTUAL] Found {len(df)} transactions")

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

                    create_transaction(
                        actual.session,
                        date=tx_date,
                        account=account,
                        payee=payee_name,
                        notes=notes,
                        amount=amount,
                        imported_id=imported_id,
                        cleared=True  # Bank transactions are verified
                    )
                    imported += 1

                except Exception as e:
                    errors.append(f"Row {row.get('Nº Orden', '?')}: {str(e)[:50]}")

            # Apply categorization rules and commit changes
            if imported > 0:
                print(f"[ACTUAL] Running categorization rules...")
                actual.run_rules()
                actual.commit()
                print(f"[ACTUAL] Committed {imported} transactions")

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
    """Get the path to the latest CSV for a bank."""
    if bank == 'ibercaja':
        path = './downloads/ibercaja/ibercaja_movements.csv'
        return path if os.path.exists(path) else None

    elif bank in ('ing_nomina', 'ing_naranja'):
        # Find the most recent CSV for this account type
        downloads_dir = './downloads/ing'
        if not os.path.exists(downloads_dir):
            return None

        account_type = 'NÓMINA' if bank == 'ing_nomina' else 'NARANJA'
        csv_files = [
            f for f in os.listdir(downloads_dir)
            if f.endswith('.csv') and account_type in f
        ]

        if not csv_files:
            return None

        # Return the most recent one
        csv_files.sort(reverse=True)
        return os.path.join(downloads_dir, csv_files[0])

    return None
