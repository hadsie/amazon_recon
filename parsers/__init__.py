from parsers.rbc_pdf_parser import parse_rbc_pdf
from parsers.example_csv_parser import parse_example_csv

#from . import parse_rbc_pdf, parse_example_csv

# Registry of supported parsers
PARSERS = {
    "rbc_pdf": parse_rbc_pdf,  # RBC PDF credit card statement parser
    "example_csv": parse_example_csv,  # Example CSV parser
}

def get_parser(parser_name: str) -> callable:
    """
    Retrieve the parser function corresponding to the specified machine name.

    Args:
        parser_name (str): The machine name of the parser (e.g., 'rbc_pdf').

    Returns:
        callable: A parser function that takes a file path as input and returns a 
        list of transactions.
    
    Raises:
        ValueError: If the parser name is not recognized.
    """
    if parser_name not in PARSERS:
        raise ValueError(f"Parser '{parser_name}' not found. Available parsers: {', '.join(PARSERS.keys())}")
    return PARSERS[parser_name]