# Parsers

## Writing Your Own Bank Statement Parsers

This tool is designed to work with multiple bank and credit card statement formats by allowing custom parsers.

### Plugin Structure

1. Create a new Python file in the `parsers` directory (e.g., `my_bank.py`).

2. Write a parser function that matches the following structure:
   ```python
   def parse_my_bank(file_path: str) -> tuple[list[dict], list[dict]]:
       \"\"\"
       Parse a credit card statement file for MyBank.

       Args:
           file_path (str): Path to the statement file.

       Returns:
           tuple[list[dict], list[dict]]:
               - Regular transactions: Each transaction is a dictionary with:
                   - 'cc_date': Transaction date as a datetime object.
                   - 'cc_description': Description of the transaction.
                   - 'cc_amount': Amount of the transaction (positive for charges, negative for refunds).
               - Refund transactions: Same structure but separated as refunds.
       \"\"\"
       # Your parsing logic here
   ```

3. Add the parser to the `parsers/__init__.py` file:
   ```python
   from parsers.my_bank import parse_my_bank

   def get_parser(parser_name: str):
       if parser_name == "my_bank":
           return parse_my_bank
       raise ValueError(f"Unknown parser: {parser_name}")
   ```


## Requesting a Custom Parser for the Amazon Order Reconciliation Tool

If you need a custom parser for your bank or credit card statement format and you aren't able to write the code yourself, you can try getting an LLM to help you create one, because it's unlikely anyone else will have time to do it for you :). I've tried this and had some success.

### Step 1: Prepare Your Files

1. **Statement Sample**:
   - Provide a sample of your credit card / bank statement in the exact format you want to parse (e.g., PDF, CSV).
   - You may want to remove or hide any sensitive information prior to uploading the data.

2. **Statement Details**:
   - Describe the format of your statement:
     - What column contains the **transaction date**?
     - What column contains the **transaction description**?
     - What column contains the **amount**?
   - Specify if charges are positive or negative, and how refunds are indicated.

3. **Exclusions**:
   - Are there specific transactions you want to exclude (e.g., service fees or irrelevant charges)? Provide examples.

### Step 2: Use This Prompt

Here’s an example prompt you can use to try to request a parser:

```plaintext
I’m using a tool to reconcile my amazon orders with my bank statements and I need a custom parser for my bank's statement format. Here's the repository link for reference: https://github.com/hadsie/amazon_recon.

I’ve attached:
1. A sample of my statement file.
2. A description of the file structure:
   - The first column is the transaction date in the format YYYY-MM-DD.
   - The second column is the transaction description.
   - The last column is the transaction amount (negative for refunds).

Excluded transactions: Any line containing "AMAZON WEB SERVICES".

Could you create a Python function `parse_my_bank` to process this statement format and return two lists: regular transactions and refunds? Please also provide integration instructions for the tool. Refer to the GitHub page here for more details: https://github.com/hadsie/amazon_recon/parsers/README.md.

### Step 3: Submit the Request to the LLM

- Upload the sample statement file.
- Include the provided prompt, filling in any additional details about your statement format.
- The LLM will hopefully generate a parser and instructions for integrating it with the tool.
