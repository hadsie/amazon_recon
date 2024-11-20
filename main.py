#!/usr/bin/env python3

import os
import sys
import logging
import argparse

from reconciliation import (
    parse_bank_statements,
    preprocess_amazon_orders,
    process_refunds,
    reconcile_amazon_orders,
)

def confirm_overwrite(file_path: str) -> bool:
    """
    Checks if a file exists and prompts the user for confirmation to overwrite it.

    Args:
        file_path (str): Path to the file to check.

    Returns:
        bool: True if the file doesn't exist or the user confirms overwriting, False otherwise.
    """
    if os.path.exists(file_path):
        while True:
            response = input(f"Warning: {file_path} already exists. Overwrite? (Y/n): ").strip().lower()
            if response == "n" or response == "N":
                print("Operation cancelled.")
                return False
            elif response != "y" and len(response) != 0:
                print("Invalid input. Please enter 'y' for yes or 'n' for no.")
            else:
                return True
    return True

def main():
    """
    Parse any arguments and run the statement parser + reconciler.
    """
    parser = argparse.ArgumentParser(description="Reconcile Amazon orders with bank statements.")
    parser.add_argument("parser_name", help="Machine name of the bank statement parser (e.g., 'rbc_pdf').")
    parser.add_argument("statement", help="Path to the bank statement file or a glob pattern (e.g., '*.pdf').")
    parser.add_argument("amazon_csv", help="Path to the Amazon orders CSV.")
    parser.add_argument("--output", default="matched_transactions.csv",
                        help="Path to save the reconciled transactions CSV. Defaults to 'matched_transactions.csv'.")
    parser.add_argument("--quiet", action="store_true", help="Suppress output of messages.")
    parser.add_argument("-f", "--force", action="store_true", help="Overwrite output CSV without confirmation.")

    args = parser.parse_args()

    if not args.force and not confirm_overwrite(args.output):
        sys.exit(1)

    logging.basicConfig(level=logging.INFO if not args.quiet else logging.ERROR, format="%(message)s")

    logging.info(f"Running statement parser on {args.statement}...")
    cc_transactions, statement_refunds = parse_bank_statements(args.statement, args.parser_name)

    logging.info(f"Found {len(cc_transactions)} matching statement line items and {len(statement_refunds)} refunds.")

    logging.info(f"\nReconciling bank statement(s) against amazon order data in {args.amazon_csv}...")
    matched_data, unmatched_cc, unmatched_amazon = reconcile_amazon_orders(cc_transactions, args.amazon_csv)

    logging.info(f"\nProcessing refunds...")
    matched_refunds, unmapped_amazon_refunds = process_refunds(args.amazon_csv, statement_refunds)

    if not unmapped_amazon_refunds.empty:
        logging.info("\nUnmapped Amazon Refunds:")
        logging.info(unmapped_amazon_refunds[['order id', 'refund', 'date']].to_string(index=False))

    if unmatched_cc:
        logging.info("\nUnmatched Bank Statement Transactions:")
        for row in unmatched_cc:
            logging.info(row["description"])
    if not unmatched_amazon.empty:
        logging.info("\nUnmatched Amazon Orders:")
        logging.info(unmatched_amazon[['order id', 'date', 'total']]
            .sort_values(by="date", ascending=True)
            .to_string(index=False))
    if unmapped_amazon_refunds.empty and not unmatched_cc:
        logging.info("\nAll Transactions Reconciled")

    matched_data.sort_values(by="amazon_date", ascending=True).to_csv(args.output, index=False)
    logging.info(f"\nReconciled transactions saved to: {args.output}")


if __name__ == "__main__":
    main()
