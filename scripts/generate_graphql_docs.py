#!/usr/bin/env python3
"""
GraphQL API Documentation Generator

This script generates structured documentation from the Saleor GraphQL schema,
leveraging existing @doc(category: "...") directives to organize content.
"""

import re
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set


class GraphQLDocGenerator:
    def __init__(self, schema_path: str, docs_path: str):
        self.schema_path = schema_path
        self.docs_path = docs_path
        self.categories = defaultdict(list)
        self.schema_content = ""
        
    def load_schema(self):
        """Load the GraphQL schema file."""
        with open(self.schema_path, 'r') as f:
            self.schema_content = f.read()
    
    def extract_categories(self) -> Dict[str, List[str]]:
        """Extract all fields organized by their @doc categories."""
        # Pattern to match fields with @doc(category: "...") in Query, Mutation, and Subscription types
        
        # Find the main operation types
        query_section = self._extract_type_section("Query")
        mutation_section = self._extract_type_section("Mutation") 
        subscription_section = self._extract_type_section("Subscription")
        
        # Extract fields from each section
        self._extract_fields_from_section(query_section, "Query")
        self._extract_fields_from_section(mutation_section, "Mutation")
        self._extract_fields_from_section(subscription_section, "Subscription")
        
        return dict(self.categories)
    
    def _extract_type_section(self, type_name: str) -> str:
        """Extract the content of a specific GraphQL type."""
        pattern = rf'type {type_name}\s*{{([^}}]+)}}'
        match = re.search(pattern, self.schema_content, re.DOTALL)
        return match.group(1) if match else ""
    
    def _extract_fields_from_section(self, section: str, operation_type: str):
        """Extract fields with categories from a type section."""
        # Pattern to match field definitions with @doc category
        pattern = r'(\w+)(?:\([^)]*\))?\s*:\s*[^@\n]*@doc\(category:\s*"([^"]+)"\)'
        
        matches = re.finditer(pattern, section)
        
        for match in matches:
            field_name = match.group(1)
            category = match.group(2)
            field_key = f"{operation_type}.{field_name}"
            
            # Avoid duplicates
            if field_key not in [item.get('key') for item in self.categories[category]]:
                self.categories[category].append({
                    'name': field_name,
                    'operation_type': operation_type,
                    'key': field_key
                })
    
    def extract_field_info(self, field_name: str) -> Dict[str, str]:
        """Extract detailed information about a specific field."""
        # Look for the field definition with description
        pattern = rf'"""([^"]*?)"""\s*{re.escape(field_name)}\s*(\([^)]*\))?\s*:\s*([^@\n]+)(@[^{{\n]*)?'
        
        match = re.search(pattern, self.schema_content, re.DOTALL)
        
        if match:
            description = match.group(1).strip()
            args = match.group(2) or ""
            return_type = match.group(3).strip()
            directives = match.group(4) or ""
            
            return {
                'description': description,
                'arguments': args,
                'return_type': return_type,
                'directives': directives
            }
        
        return {}
    
    def generate_category_docs(self):
        """Generate documentation for each category."""
        categories = self.extract_categories()
        
        # Category mapping for better documentation organization
        category_info = {
            'Products': {
                'title': 'Products API',
                'description': 'Manage product catalog, variants, types, and inventory operations.'
            },
            'Orders': {
                'title': 'Orders API', 
                'description': 'Handle order processing, fulfillment, and management operations.'
            },
            'Users': {
                'title': 'Users API',
                'description': 'Manage customer accounts, staff users, and user-related operations.'
            },
            'Discounts': {
                'title': 'Discounts API',
                'description': 'Configure sales, vouchers, promotional campaigns, and discount rules.'
            },
            'Payments': {
                'title': 'Payments API',
                'description': 'Process payments, manage gateways, and handle payment-related operations.'
            },
            'Attributes': {
                'title': 'Attributes API',
                'description': 'Define and manage product attributes, attribute values, and metadata.'
            },
            'Checkout': {
                'title': 'Checkout API',
                'description': 'Handle cart management, checkout process, and order creation.'
            },
            'Taxes': {
                'title': 'Taxes API',
                'description': 'Configure tax rates, tax classes, and tax calculation settings.'
            },
            'Pages': {
                'title': 'Pages API',
                'description': 'Manage CMS pages, page types, and content management operations.'
            },
            'Shipping': {
                'title': 'Shipping API',
                'description': 'Configure shipping methods, zones, and shipping-related operations.'
            },
            'Menu': {
                'title': 'Menu API',
                'description': 'Create and manage navigation menus and menu items.'
            },
            'Webhooks': {
                'title': 'Webhooks API',
                'description': 'Configure event-driven integrations and webhook notifications.'
            },
            'Apps': {
                'title': 'Apps API',
                'description': 'Manage third-party applications and app integrations.'
            },
            'Gift cards': {
                'title': 'Gift Cards API',
                'description': 'Handle gift card creation, management, and redemption operations.'
            },
            'Channels': {
                'title': 'Channels API',
                'description': 'Configure multi-channel setup and channel-specific settings.'
            },
            'Authentication': {
                'title': 'Authentication API',
                'description': 'Handle user authentication, tokens, and permission management.'
            },
            'Shop': {
                'title': 'Shop API',
                'description': 'Manage global shop settings, configuration, and shop information.'
            },
            'Miscellaneous': {
                'title': 'Miscellaneous API',
                'description': 'Utility operations and other miscellaneous functionality.'
            }
        }
        
        for category, fields in categories.items():
            if not fields:
                continue
                
            info = category_info.get(category, {
                'title': f'{category} API',
                'description': f'Operations related to {category.lower()}.'
            })
            
            # Create filename-safe category name
            filename = category.lower().replace(' ', '-').replace('&', 'and')
            filepath = os.path.join(self.docs_path, 'categories', f'{filename}.md')
            
            with open(filepath, 'w') as f:
                f.write(f"# {info['title']}\n\n")
                f.write(f"{info['description']}\n\n")
                f.write(f"## Available Operations\n\n")
                f.write(f"This category includes {len(fields)} operations:\n\n")
                
                # Group by operation type
                queries = [f for f in fields if f.get('operation_type') == 'Query']
                mutations = [f for f in fields if f.get('operation_type') == 'Mutation'] 
                subscriptions = [f for f in fields if f.get('operation_type') == 'Subscription']
                
                if queries:
                    f.write("### Queries\n\n")
                    for field in sorted(queries, key=lambda x: x['name']):
                        field_info = self.extract_field_info(field['name'])
                        f.write(f"#### `{field['name']}`\n\n")
                        if field_info.get('description'):
                            f.write(f"{field_info['description']}\n\n")
                        if field_info.get('return_type'):
                            f.write(f"**Returns:** `{field_info['return_type']}`\n\n")
                
                if mutations:
                    f.write("### Mutations\n\n")
                    for field in sorted(mutations, key=lambda x: x['name']):
                        field_info = self.extract_field_info(field['name'])
                        f.write(f"#### `{field['name']}`\n\n")
                        if field_info.get('description'):
                            f.write(f"{field_info['description']}\n\n")
                        if field_info.get('return_type'):
                            f.write(f"**Returns:** `{field_info['return_type']}`\n\n")
                
                if subscriptions:
                    f.write("### Subscriptions\n\n")
                    for field in sorted(subscriptions, key=lambda x: x['name']):
                        field_info = self.extract_field_info(field['name'])
                        f.write(f"#### `{field['name']}`\n\n")
                        if field_info.get('description'):
                            f.write(f"{field_info['description']}\n\n")
                        if field_info.get('return_type'):
                            f.write(f"**Returns:** `{field_info['return_type']}`\n\n")
                
                f.write("## Usage Examples\n\n")
                f.write("*Coming soon - specific examples for this category.*\n\n")
                f.write("## Related Types\n\n")
                f.write("*Coming soon - related GraphQL types and inputs.*\n")
    
    def generate_overview_stats(self):
        """Generate an overview with statistics about the API."""
        categories = self.extract_categories()
        
        stats_content = f"""# API Statistics

## Category Overview

The Saleor GraphQL API contains {sum(len(fields) for fields in categories.values())} operations across {len(categories)} categories:

"""
        
        # Sort categories by number of operations
        sorted_categories = sorted(categories.items(), key=lambda x: len(x[1]), reverse=True)
        
        for category, fields in sorted_categories:
            # Count by operation type
            queries = len([f for f in fields if f.get('operation_type') == 'Query'])
            mutations = len([f for f in fields if f.get('operation_type') == 'Mutation'])
            subscriptions = len([f for f in fields if f.get('operation_type') == 'Subscription'])
            
            stats_content += f"- **{category}**: {len(fields)} operations"
            if queries or mutations or subscriptions:
                breakdown = []
                if queries: breakdown.append(f"{queries} queries")
                if mutations: breakdown.append(f"{mutations} mutations") 
                if subscriptions: breakdown.append(f"{subscriptions} subscriptions")
                stats_content += f" ({', '.join(breakdown)})"
            stats_content += "\n"
        
        stats_content += "\n## Schema Metrics\n\n"
        
        # Count different schema elements
        lines = self.schema_content.split('\n')
        stats_content += f"- Total schema lines: {len(lines)}\n"
        stats_content += f"- Directives: {len(re.findall(r'@doc\(category:', self.schema_content))}\n"
        stats_content += f"- Deprecated fields: {len(re.findall(r'@deprecated', self.schema_content))}\n"
        
        with open(os.path.join(self.docs_path, 'stats.md'), 'w') as f:
            f.write(stats_content)
    
    def run(self):
        """Run the documentation generation process."""
        print("Loading GraphQL schema...")
        self.load_schema()
        
        print("Generating category documentation...")
        self.generate_category_docs()
        
        print("Generating API statistics...")
        self.generate_overview_stats()
        
        print(f"Documentation generated in {self.docs_path}")


def main():
    script_dir = Path(__file__).parent
    schema_path = script_dir.parent / "saleor" / "graphql" / "schema.graphql"
    docs_path = script_dir.parent / "docs" / "graphql"
    
    generator = GraphQLDocGenerator(str(schema_path), str(docs_path))
    generator.run()


if __name__ == "__main__":
    main()