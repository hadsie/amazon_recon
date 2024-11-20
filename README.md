# Amazon Order Reconciliation Tool

## Overview

Amazon removed their download order feature a while back but I still needed a way to reconcile orders against my credit card statement to identify fraud, so I built this tool.

To get your order history, you’ll need to use the Amazon Order History Reporter Chrome extension which screenscrapes your amazon order listing.

## Features

- Matches Amazon orders with credit card charges based on amounts and transaction dates.
- Handles refunds and ensures they are matched with credit card statements.
- Supports multiple bank or credit card formats via plugins (well, maybe someday :)).
- Generates outputs for:
  - Reconciled transactions.
  - Unmatched credit card transactions.
  - Unmapped Amazon refunds.

---

## Setup Instructions

### Prerequisites

- Python 3
- Chrome with the **[Amazon Order History Reporter](https://chrome.google.com/webstore/detail/amazon-order-history-repo/lbfehkoinhhcknnbdgnnmjhiladcgbol)** extension installed.

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/amazon-order-reconciliation.git
   cd amazon-order-reconciliation
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

```bash
$ ./main.py --help
usage: main.py [-h] [--output OUTPUT] [--quiet] [-f] parser_name statement amazon_csv

Reconcile Amazon orders with credit card transactions.

positional arguments:
  parser_name      Machine name of the bank statement parser (e.g., 'rbc_pdf').
  statement        Path to the credit card statement file or a glob pattern (e.g., '*.pdf').
  amazon_csv       Path to the Amazon orders CSV.

options:
  -h, --help       show this help message and exit
  --output OUTPUT  Path to save the reconciled transactions CSV. Defaults to 'reconciled_amazon_transactions.csv'.
  --quiet          Suppress output of messages.
  -f, --force      Overwrite output CSV without confirmation.
```

### Example Commands

#### Reconciling Orders
1. Export your Amazon orders using the Amazon Order History Reporter.
2. Run the tool with your bank statement and Amazon CSV:
   ```bash
   python main.py my_parser path/to/statement.pdf path/to/amazon_orders.csv --output reconciled.csv
   ```
   or for multiple statements:
   ```bash
   python main.py my_parser "/path/to/statements/*.pdf" path/to/amazon_orders.csv --output reconciled.csv
   ```

   This will generate a `reconciled.csv` file containing matched transactions. `my_parser` is the custom parser for your bank or credit card statements.

---

## Limitations

1. **Archived Orders**: The Amazon Order History Reporter does not include "archived" orders, so check that first if you're seeing unreconciled transactions.
2. **Data Integrity**: The data is a bit of a mess, so again, if you run into issues it could just be an error parsing the data. There may also be some issues with timezones, though I've tried to account for that by allowing order matching within a couple days between the statement and the amazon order date.
3. **Limited statement parsers**: I've only written in support for RBC as that was the bank I was using at the time of writing. Non-supported statement formats require writing a custom parser plugin. But this should be straight forward enough, check the README in the plugins folder.

---

## Contributing

Feel free to submit pull requests for additional bank or credit card formats, new features, or bug fixes.
"""