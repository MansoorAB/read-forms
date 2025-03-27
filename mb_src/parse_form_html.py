import json
import os
from bs4 import BeautifulSoup
import re

class GenericFormParser:
    def __init__(self):
        self.form_data = {}
    
    def extract_field_value(self, text):
        """Extract value from field text like 'Field name: value'"""
        if ':' in text:
            return text.split(':', 1)[1].strip()
        return text.strip()
    
    def extract_ssn(self, text):
        """Extract SSN pattern from text"""
        ssn_pattern = r'\d{3}-\d{2}-\d{4}'
        match = re.search(ssn_pattern, text)
        return match.group(0) if match else ""
    
    def extract_amount(self, text):
        """Extract monetary amounts from text"""
        amount_pattern = r'\$?\d{1,3}(?:,\d{3})*(?:\.\d+)?'
        match = re.search(amount_pattern, text)
        return match.group(0) if match else ""
    
    def parse_text_fields(self, soup):
        """Parse all text fields from list items"""
        text_fields = {}
        for item in soup.find_all('li'):
            text = item.get_text().strip()
            if ':' in text:
                field_name = text.split(':', 1)[0].strip()
                value = self.extract_field_value(text)
                if value:  # Only add non-empty values
                    text_fields[field_name] = value
        return text_fields
    
    def parse_tables(self, soup):
        """Parse all tables in the document"""
        tables_data = []
        for table in soup.find_all('table'):
            table_data = {
                'headers': [],
                'rows': []
            }
            
            # Get headers
            headers = table.find_all('th')
            if not headers:
                headers = table.find('tr').find_all('td')  # Use first row as headers if no th elements
            
            for header in headers:
                table_data['headers'].append(header.get_text().strip())
            
            # Get rows
            rows = table.find_all('tr')[1:] if headers else table.find_all('tr')  # Skip header row if headers exist
            for row in rows:
                row_data = {}
                cells = row.find_all('td')
                for i, cell in enumerate(cells):
                    if i < len(table_data['headers']):
                        row_data[table_data['headers'][i]] = cell.get_text().strip()
                if row_data:  # Only add non-empty rows
                    table_data['rows'].append(row_data)
            
            if table_data['rows']:  # Only add tables with data
                tables_data.append(table_data)
        
        return tables_data
    
    def parse_special_fields(self, soup):
        """Parse special fields like SSNs and amounts"""
        special_fields = {
            'ssns': [],
            'amounts': []
        }
        
        # Find all SSNs
        full_text = soup.get_text()
        ssns = re.finditer(r'\d{3}-\d{2}-\d{4}', full_text)
        special_fields['ssns'] = [ssn.group(0) for ssn in ssns]
        
        # Find all amounts
        amounts = re.finditer(r'\$?\d{1,3}(?:,\d{3})*(?:\.\d+)?', full_text)
        special_fields['amounts'] = [amount.group(0) for amount in amounts]
        
        return special_fields
    
    def parse_html(self, html_file):
        """Parse HTML file and extract all form data"""
        # Read HTML file
        with open(html_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        # Parse different types of data
        self.form_data = {
            'text_fields': self.parse_text_fields(soup),
            'tables': self.parse_tables(soup),
            'special_fields': self.parse_special_fields(soup)
        }
        
        return self.form_data

def main():
    # Create output directory if it doesn't exist
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize parser
    parser = GenericFormParser()
    
    # Parse the HTML file
    html_file = "data/_content_olmocr_sample_1040_1_pdf.html"
    print(f"\nParsing HTML file: {html_file}")
    
    result = parser.parse_html(html_file)
    
    if result:
        # Write to JSON file
        output_file = os.path.join(output_dir, "form_data.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\nSuccess! Data written to {output_file}")
        print("\nExtracted sections:")
        for section in result.keys():
            print(f"- {section}")
        
        # Print sample of extracted data
        print("\nSample of extracted data:")
        if "text_fields" in result:
            print("\nText Fields:")
            print(json.dumps(result["text_fields"], indent=2))
        if "tables" in result:
            print("\nTables:")
            print(json.dumps(result["tables"], indent=2))
        if "special_fields" in result:
            print("\nSpecial Fields:")
            print(json.dumps(result["special_fields"], indent=2))
    else:
        print("\nFailed to parse form data")

if __name__ == "__main__":
    main() 