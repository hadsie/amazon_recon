import pandas as pd

def parse_example_csv(file_path):
    """
    Parses a CSV statement.
    Returns a list of dictionaries with:
        - date: Date of the transaction
        - description: Description of the transaction
        - amount: Transaction amount
    """
    transactions = []
    data = pd.read_csv(file_path)
    for _, row in data.iterrows():
        transactions.append({
            "date": pd.to_datetime(row["Transaction Date"]),
            "description": row["Description"],
            "amount": float(row["Amount"])
        })
    return transactions
