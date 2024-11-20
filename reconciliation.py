import logging
import pandas as pd
import re

from itertools import combinations
from collections import defaultdict

from parsers import get_parser

def parse_bank_statements(file_or_glob: str, parser_name: str) -> tuple[list[dict], list[dict]]:
    """
    Parse one or more bank statements using the specified parser.

    Args:
        file_or_glob (str): Path to a single file or a glob pattern (e.g., '*.pdf').
        parser_name (str): Machine name of the parser to use (e.g., 'rbc_pdf').

    Returns:
        tuple[list[dict], list[dict]]:
            - list[dict]: Regular transactions.
            - list[dict]: Refund transactions.
    """
    from glob import glob

    parser_func = get_parser(parser_name)
    transactions = []
    refunds = []

    # Expand glob pattern and parse each file
    file_paths = glob(file_or_glob) if "*" in file_or_glob else [file_or_glob]

    for file_path in file_paths:
        logging.info(f"Reading {file_path}...")
        parsed_data = parser_func(file_path)

        if isinstance(parsed_data, tuple) and len(parsed_data) == 2:
            # If the parser returns (transactions, refunds), unpack them
            file_transactions, file_refunds = parsed_data
            transactions.extend(file_transactions)
            refunds.extend(file_refunds)
        elif isinstance(parsed_data, list):
            # If the parser returns a single list, treat all as normal transactions
            transactions.extend(parsed_data)
        else:
            raise ValueError(f"Unexpected return format from parser {parser_name} for file {file_path}")

    return transactions, refunds

def preprocess_amazon_orders(amazon_csv_path: str) -> pd.DataFrame:
    """
    Preprocess the Amazon orders CSV to handle split payments.

    The generated Amazon CSV has a 'payments' column that lists any split
    payments that would be multiple records on the bank statement. This will
    expands rows with semicolon-separated entries in the 'payments' column into 
    individual rows. If the payments column doesn't match the format then
    the rows 'amount' column will be used.

    Args:
        amazon_csv_path (str): Path to the Amazon orders CSV file.

    Returns:
        pd.DataFrame: A DataFrame containing expanded rows with individual payment 
        entries. Each row includes all other fields duplicated, with 'date' and 
        'total' updated from the split 'payments' data.
    """
    amazon_orders = pd.read_csv(amazon_csv_path)

    # Parse 'date' column as datetime and skip rows with invalid dates
    amazon_orders['date'] = pd.to_datetime(amazon_orders['date'], errors='coerce')
    amazon_orders = amazon_orders.dropna(subset=['date'])

    # Prepare a list to store expanded rows
    expanded_rows = []

    for _, row in amazon_orders.iterrows():
        payments = row.get('payments', None)
        if pd.notna(payments) and isinstance(payments, str) and ';' in payments and ':' in payments:
            # Normalize text: replace \xa0 (non-breaking space) and other special characters
            payments = payments.replace('\xa0', ' ')

            # Split payments into individual entries, strip surrounding whitespace, and remove empty values.
            payment_entries = [entry.strip() for entry in payments.split(';') if entry.strip()]

            for payment_entry in payment_entries:
                # Extract date and amount from the payment entry
                match = re.search(r'(\w+ \d{1,2}, \d{4}):\s*\$([-\d,.]+)', payment_entry)
                if match:
                    payment_date, payment_amount = match.groups()
                    payment_date = pd.to_datetime(payment_date, errors='coerce')
                    payment_amount = float(payment_amount.replace(',', ''))

                    # Duplicate all other fields and update date and total
                    expanded_row = row.to_dict()
                    expanded_row['date'] = payment_date
                    expanded_row['total'] = payment_amount
                    expanded_rows.append(expanded_row)
        else:
            # Keep the original row if the payments column doesn't match.
            expanded_rows.append(row.to_dict())

    return pd.DataFrame(expanded_rows)


def reconcile_amazon_orders(cc_transactions: list[dict], amazon_csv_path: str) -> tuple[pd.DataFrame, list[dict], pd.DataFrame]:
    """
    Reconcile Amazon orders with bank statement / CC transactions.

    Matches each Amazon order to a bank statement transaction based on the payment 
    amount within a date range.

    Args:
        cc_transactions (list[dict]): List of statement transactions, each 
        represented as a dictionary with keys: 'date', 'description', and 
        'amount'.
        amazon_csv_path (str): Path to the preprocessed Amazon orders CSV file.

    Returns:
        tuple[pd.DataFrame, list[dict], pd.DataFrame]:
            - pd.DataFrame: A DataFrame containing reconciled transactions, including 
              matched Amazon orders and transactions.
            - list[dict]: A list of unmatched transactions.
            - pd.DataFrame: A DataFrame of unmatched Amazon orders.
    """
    # Preprocess the Amazon orders CSV
    amazon_orders = preprocess_amazon_orders(amazon_csv_path)

    matched_records = []
    unmatched_cc = cc_transactions.copy()
    unmatched_amazon = amazon_orders.copy()

    matched_ids = []

    # Match Amazon orders to bank statement transactions row by row
    for _, amazon_row in amazon_orders.iterrows():
        amazon_date = amazon_row['date']
        amazon_amount = float(amazon_row['total'])
        amazon_order_id = amazon_row['order id']

        for cc_row in unmatched_cc:
            cc_date = cc_row["date"]
            cc_amount = cc_row["amount"]

            # Check if date matches, is 1 day before, or is up to 2 days after, and amounts match
            if (cc_date >= amazon_date - pd.Timedelta(days=1)
                and cc_date <= amazon_date + pd.Timedelta(days=2)
                and abs(cc_amount - amazon_amount) < 0.01):

                # Match found, record the result
                matched_records.append({
                    "statement_transaction_date": cc_date,
                    "statement_description": cc_row["description"],
                    "statement_amount": cc_amount,
                    "amazon_date": amazon_date,
                    "amazon_amount": amazon_amount,
                    "amazon_order_id": amazon_order_id,
                })
                unmatched_cc.remove(cc_row)

                # If match found for this Amazon order; remove it from unmatched_amazon
                unmatched_amazon = unmatched_amazon[unmatched_amazon['order id'] != amazon_order_id]
                break

    # Create final DataFrame for matched records
    matched_df = pd.DataFrame(matched_records)

    return matched_df, unmatched_cc, unmatched_amazon

def process_refunds(amazon_csv_path: str, statement_refunds: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Process refunds by matching Amazon refunds to statement refund transactions.

    Args:
        amazon_csv_path (str): Path to the Amazon orders CSV.
        statement_refunds (list[dict]): List of refund transactions from the statement, each containing:
            - 'date' (datetime): The date of the refund.
            - 'amount' (float): The refund amount (negative value).

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]:
            - pd.DataFrame: Matched refunds.
            - pd.DataFrame: Unmapped Amazon refunds.
    """
    # Load the Amazon CSV and filter only rows with refunds
    amazon_orders = pd.read_csv(amazon_csv_path)
    amazon_orders['date'] = pd.to_datetime(amazon_orders['date'], errors='coerce')
    refund_rows = amazon_orders[amazon_orders['refund'].notna()]

    matched_refunds = []
    unmapped_amazon_refunds = refund_rows.copy()

    # Match Amazon refunds to statement refunds
    for _, refund_row in refund_rows.iterrows():
        amazon_date = refund_row['date']
        amazon_refund_amount = float(refund_row['refund'])

        for statement_refund in statement_refunds:
            statement_date = statement_refund['date']
            statement_amount = statement_refund['amount']

            # Match on amount and ensure the statement date is after Amazon date
            if (
                abs(amazon_refund_amount - abs(statement_amount)) < 0.01
                and statement_date >= amazon_date
            ):
                matched_refunds.append({
                    "amazon_order_id": refund_row['order id'],
                    "amazon_refund_amount": amazon_refund_amount,
                    "amazon_date": amazon_date,
                    "statement_refund_date": statement_date,
                    "statement_refund_amount": statement_amount,
                })
                unmapped_amazon_refunds = unmapped_amazon_refunds[
                    unmapped_amazon_refunds['order id'] != refund_row['order id']
                ]
                break

    return pd.DataFrame(matched_refunds), unmapped_amazon_refunds
