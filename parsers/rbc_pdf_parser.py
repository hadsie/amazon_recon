import pdfplumber
import re
from datetime import datetime

EXCLUDES = [
    "AMAZONWEBSERVICES",    # Exclude AWS
    "AMAZON.CAPRIMEMEMBER", # Exclude Amazon Prime
]

def parse_rbc_pdf(file_path: str) -> tuple[list[dict], list[dict]]:
    """
    Parse an RBC credit card statement PDF.

    Extracts transaction details, separating regular transactions and refunds.
    Filters out excluded entries based on predefined patterns.

    Args:
        file_path (str): Path to the RBC credit card statement PDF.

    Returns:
        tuple[list[dict], list[dict]]:
            - list[dict]: Regular transactions.
            - list[dict]: Refund transactions with negative amounts.
    """
    import pdfplumber
    import re
    from datetime import datetime

    transactions = []
    refunds = []

    # Define regex for matching transaction lines
    transaction_regex = re.compile(r'(\w{3}\d{1,2}) .* (?:AMZN|AMAZON)[^$]* (-?\$\d[.,\d]+)', re.IGNORECASE)

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            lines = text.split('\n')

            for line in lines:
                # Clean up special characters
                line = line.replace('\xa0', ' ').strip()

                match = transaction_regex.match(line)
                if not match:
                    continue

                date_str, amount = match.groups()

                try:
                    # Parse date and amount
                    date = datetime.strptime(date_str + ' 2024', "%b%d %Y")
                    amount = float(amount.replace('$', '').replace(',', ''))
                    # Check for exclusions
                    if any(excluded in line.upper() for excluded in EXCLUDES):
                        continue

                    # Separate regular transactions and refunds
                    if amount < 0:
                        refunds.append({
                            "date": date,
                            "description": line,
                            "amount": amount
                        })
                    else:
                        transactions.append({
                            "date": date,
                            "description": line,
                            "amount": amount
                        })
                except ValueError:
                    # Silently skip lines that fail parsing
                    continue

    return transactions, refunds