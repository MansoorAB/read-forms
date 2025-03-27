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
    
    def extract_section_title(self, element):
        """Extract section title (like 'Part II') from text"""
        text = element.get_text().strip()
        if text.startswith('Part '):
            return text
        return None
    
    def extract_table_context(self, table):
        """Extract text that appears before the table to provide context"""
        context = []
        prev_element = table.find_previous_sibling()
        
        # Look for text elements before the table
        while prev_element and len(context) < 3:  # Limit to 3 previous elements for relevant context
            if prev_element.name in ['p', 'div', 'li']:
                text = prev_element.get_text().strip()
                if text and not text.startswith('□'):  # Skip checkbox markers
                    # Skip if text is just a number or empty
                    if not re.match(r'^\d+\.?\s*$', text):
                        context.append(text)
            prev_element = prev_element.find_previous_sibling()
        
        return ' '.join(reversed(context))  # Return context in original order
    
    def process_form_field(self, element):
        """Process a form field (numbered items like '2. Add the amounts...')"""
        text = element.get_text().strip()
        
        # Look for numbered fields (e.g., "2. Add the amounts...")
        field_match = re.match(r'^\d+\.?\s+(.+)', text)
        if field_match:
            field_text = field_match.group(1).strip()
            # Look for amount after the field text
            amount_match = re.search(r'\d{1,3}(?:,\d{3})*(?:\.\d+)?$', text)
            return {
                'type': 'form_field',
                'text': field_text,
                'value': amount_match.group(0) if amount_match else None
            }
        return None
    
    def process_table(self, table):
        """Process a table and maintain its structure"""
        table_data = {
            'type': 'table',
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
        """Parse HTML file and extract all form data including fields and sections"""
        # Read HTML file
        with open(html_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        current_section = None
        current_section_data = None
        
        # Process all elements in order
        for element in soup.find_all(['p', 'div', 'table', 'li']):
            # Skip empty elements
            if not element.get_text().strip():
                continue
            
            # Check for section titles (Part I, Part II, etc.)
            section_title = self.extract_section_title(element)
            if section_title:
                if current_section_data:
                    self.form_data.append(current_section_data)
                current_section = section_title
                current_section_data = {
                    'type': 'section',
                    'title': section_title,
                    'fields': []
                }
                continue
            
            # Process tables
            if element.name == 'table':
                table_data = self.process_table(element)
                if table_data['rows']:
                    if current_section_data:
                        current_section_data['fields'].append(table_data)
                    else:
                        self.form_data.append(table_data)
                continue
            
            # Process form fields
            field_data = self.process_form_field(element)
            if field_data:
                if current_section_data:
                    current_section_data['fields'].append(field_data)
                else:
                    self.form_data.append(field_data)
        
        # Add the last section if exists
        if current_section_data:
            self.form_data.append(current_section_data)
        
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
        print("\nExtracted data:")
        for item in result:
            if item.get('type') == 'section':
                print(f"\nSection: {item['title']}")
                print("Fields:", len(item['fields']))
            elif item.get('type') == 'form_field':
                print(f"\nField: {item['text']}")
                if item.get('value'):
                    print(f"Value: {item['value']}")
            elif item.get('type') == 'table':
                print(f"\nTable with {len(item['rows'])} rows")
                print("Context:", item['context'])
    else:
        print("\nFailed to parse form data")

if __name__ == "__main__":
    main() 