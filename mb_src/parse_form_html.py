import json
import os
from bs4 import BeautifulSoup
import re

class GenericFormParser:
    def __init__(self):
        self.form_data = []
    
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
    
    def extract_table_context(self, table):
        """Extract text that appears before the table to provide context"""
        context = []
        prev_element = table.find_previous_sibling()
        
        # Look for text elements before the table
        while prev_element and prev_element.name in ['p', 'div', 'li']:
            text = prev_element.get_text().strip()
            if text and not text.startswith('□'):  # Skip checkbox markers
                context.append(text)
            prev_element = prev_element.find_previous_sibling()
        
        return ' '.join(reversed(context))  # Return context in original order
    
    def process_element(self, element):
        """Process a single HTML element and extract its data"""
        data = {}
        text = element.get_text().strip()
        
        # Skip empty elements
        if not text:
            return None
            
        # Process list items
        if element.name == 'li':
            if ':' in text:
                field_name = text.split(':', 1)[0].strip()
                value = self.extract_field_value(text)
                if value:
                    data['type'] = 'field'
                    data['name'] = field_name
                    data['value'] = value
                    return data
        
        # Process table cells
        elif element.name in ['td', 'th']:
            # Check if this is a header cell
            if element.name == 'th' or element.parent.name == 'tr' and element.parent.find('th'):
                data['type'] = 'header'
                data['value'] = text
            else:
                data['type'] = 'cell'
                data['value'] = text
            return data
        
        # Process text nodes
        else:
            # Look for SSNs
            ssn = self.extract_ssn(text)
            if ssn:
                data['type'] = 'ssn'
                data['value'] = ssn
                return data
            
            # Look for amounts
            amount = self.extract_amount(text)
            if amount:
                data['type'] = 'amount'
                data['value'] = amount
                return data
            
            # If it's just text with a colon, treat it as a field
            if ':' in text:
                field_name = text.split(':', 1)[0].strip()
                value = self.extract_field_value(text)
                if value:
                    data['type'] = 'field'
                    data['name'] = field_name
                    data['value'] = value
                    return data
        
        return None
    
    def process_table(self, table):
        """Process a table and maintain its structure"""
        table_data = {
            'context': self.extract_table_context(table),
            'headers': [],
            'rows': []
        }
        
        # Get headers
        headers = table.find_all('th')
        if not headers:
            headers = table.find('tr').find_all('td')
        
        header_texts = [h.get_text().strip() for h in headers]
        table_data['headers'] = header_texts
        
        # Process rows
        rows = table.find_all('tr')[1:] if headers else table.find_all('tr')
        for row in rows:
            row_data = {'cells': []}
            cells = row.find_all('td')
            
            for i, cell in enumerate(cells):
                cell_text = cell.get_text().strip()
                if cell_text:  # Only add non-empty cells
                    cell_data = {
                        'value': cell_text,
                        'header': header_texts[i] if i < len(header_texts) else None
                    }
                    row_data['cells'].append(cell_data)
            
            if row_data['cells']:
                table_data['rows'].append(row_data)
        
        return table_data
    
    def parse_html(self, html_file):
        """Parse HTML file and extract table data with context"""
        # Read HTML file
        with open(html_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        # Process tables
        for table in soup.find_all('table'):
            table_data = self.process_table(table)
            if table_data['rows']:  # Only add tables with data
                self.form_data.append(table_data)
        
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
        
        # Print sample of extracted data
        print("\nExtracted tables:")
        for table in result:
            print(f"\nContext: {table['context']}")
            print("Headers:", table['headers'])
            print("First row:", table['rows'][0] if table['rows'] else "No rows")
    else:
        print("\nFailed to parse form data")

if __name__ == "__main__":
    main() 