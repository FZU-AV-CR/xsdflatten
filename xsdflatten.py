#!/usr/bin/env python3
import sys
import re
import copy
import os
import argparse
from lxml import etree

def get_includes_from_file(filename):
	"""Return list of included XSD files from a file."""
	pattern = re.compile('(<xs:include schemaLocation)')
	try:
		with open(filename, 'r', encoding='utf-8') as f:
			lines = [line.strip() for line in f.readlines()]
	except UnicodeDecodeError:
		# Fallback to default encoding if UTF-8 fails
		with open(filename, 'r') as f:
			lines = [line.strip() for line in f.readlines()]
	
	includes = [line.split('=')[1].split('"')[1] for line in lines if pattern.match(line)]

	# sanity check
	for inc in includes:
		if not inc.endswith('.xsd'):
			pass  # print('There is a problem with include %s in file %s' % (inc, filename))

	return includes

def get_includes_recurse(filename, include_set):
	"""Recursively collect all included XSD files."""
	includes = get_includes_from_file(filename)

	base_dir = os.path.dirname(os.path.abspath(filename))
	absolute_includes = []
	for inc in includes:
		if not os.path.isabs(inc):
			absolute_inc = os.path.join(base_dir, inc)
		else:
			absolute_inc = inc
		absolute_includes.append(absolute_inc)
		include_set.add(absolute_inc)
	
	for inc in absolute_includes:
		get_includes_recurse(inc, include_set)

def get_xml_tree_from_file(filename):
	"""Parse XML file and return root element."""
	tree = etree.parse(filename)
	return tree.getroot()

def remove_includes_and_imports(root):
	"""Remove xs:include and xs:import elements from root."""
	# Find and remove the includes and imports
	includes = root.findall('xs:include', root.nsmap)
	for inc in includes:
		root.remove(inc)
	
	# Also remove imports to avoid duplicates later
	imports = root.findall('xs:import', root.nsmap)
	for imp in imports:
		root.remove(imp)
	
	return root

def collect_imports(root, import_set):
	"""Collect all xs:import statements and add to import_set."""
	# Collect all import statements
	imports = root.findall('xs:import', root.nsmap)
	for imp in imports:
		namespace = imp.get('namespace')
		schema_location = imp.get('schemaLocation')
		if namespace and schema_location:
			import_set.add((namespace, schema_location))
		elif namespace:
			# Import without schemaLocation (like XML namespace)
			import_set.add((namespace, None))

def add_elements(target_root, source_root, processed_types):
	"""Add elements and types from source_root to target_root, skipping duplicates."""
	# Add elements from source to target, skipping duplicates
	for child in source_root:
		if child.tag.endswith('complexType') or child.tag.endswith('simpleType'):
			type_name = child.get('name')
			if type_name and type_name in processed_types:
				continue  # Skip duplicate type
			if type_name:
				processed_types.add(type_name)
		
		elif child.tag.endswith('element'):
			element_name = child.get('name')
			if element_name and f'element:{element_name}' in processed_types:
				continue  # Skip duplicate element
			if element_name:
				processed_types.add(f'element:{element_name}')
		
		target_root.append(copy.deepcopy(child))

def flatten_file(filename):
	"""Flatten XSD file by merging includes and imports into a single file."""
	include_set = set()
	import_set = set()
	processed_types = set()  # Track processed type names to avoid duplicates
	get_includes_recurse(filename, include_set)

	# Get the main document
	root = get_xml_tree_from_file(filename)
	
	# Collect all imports from main and included files
	collect_imports(root, import_set)
	for inc_file in include_set:
		inc_root = get_xml_tree_from_file(inc_file)
		collect_imports(inc_root, import_set)
	
	# Remove includes and imports from main document
	root = remove_includes_and_imports(root)
	
	# Note: We rely on import statements to provide namespace context
	
	# Add all unique imports at the beginning (after schema element)
	schema_ns = '{http://www.w3.org/2001/XMLSchema}'
	insert_position = 0
	for namespace, schema_location in sorted(import_set):
		import_elem = etree.Element(f'{schema_ns}import')
		import_elem.set('namespace', namespace)
		if schema_location:
			import_elem.set('schemaLocation', schema_location)
		# Add proper indentation and newline
		import_elem.tail = '\n  '
		root.insert(insert_position, import_elem)
		insert_position += 1
	
	# Process main file types first to establish baseline
	main_root_copy = copy.deepcopy(root)
	for child in main_root_copy:
		if child.tag.endswith('complexType') or child.tag.endswith('simpleType'):
			type_name = child.get('name')
			if type_name:
				processed_types.add(type_name)
		elif child.tag.endswith('element'):
			element_name = child.get('name')
			if element_name:
				processed_types.add(f'element:{element_name}')
	
	# Merge in the elements of the includes without duplicates
	for inc_file in include_set:
		inc_root = get_xml_tree_from_file(inc_file)
		inc_root = remove_includes_and_imports(inc_root)
		root.append(etree.Comment('Imported from %s' % inc_file))
		add_elements(root, inc_root, processed_types)

	# Serialize the result
	result = etree.tostring(root, pretty_print=True, encoding='unicode')
	
	# Post-process to add missing namespace prefixes
	if any(ns == 'http://www.opengis.net/gml/3.2' for ns, _ in import_set):
		# Add gml namespace prefix to schema element
		result = result.replace(
			'<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"',
			'<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:gml="http://www.opengis.net/gml/3.2"'
		)
	
	return result

def main():
	"""Command-line interface for flattening XSD files."""
	parser = argparse.ArgumentParser(
		description='Flatten XSD files by merging includes into a single file',
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog="""Examples:
  %(prog)s schema.xsd
  %(prog)s --output flattened.xsd input_schema.xsd"""
	)
	
	parser.add_argument('input_file', 
					   help='Input XSD file to flatten')
	parser.add_argument('-o', '--output',
					   help='Output file (if not specified, prints to stdout)',
					   metavar='FILE')
	
	try:
		args = parser.parse_args()
	except SystemExit:
		# argparse calls sys.exit() on error, we catch it to provide custom behavior if needed
		raise
	
	# Validate input file exists
	if not os.path.isfile(args.input_file):
		parser.error(f"Input file '{args.input_file}' does not exist or is not a file")
	
	# Validate input file is XSD
	if not args.input_file.lower().endswith('.xsd'):
		parser.error(f"Input file '{args.input_file}' does not have .xsd extension")
	
	try:
		flattened_content = flatten_file(args.input_file)

		if args.output:
			with open(args.output, 'w', encoding='utf-8') as f:
				f.write(flattened_content)
		else:
			print(flattened_content)
			
	except FileNotFoundError as e:
		parser.error(f"File not found: {e}")
	except etree.XMLSyntaxError as e:
		parser.error(f"XML parsing error: {e}")
	except Exception as e:
		parser.error(f"Unexpected error: {e}")

if __name__ == "__main__":
	main()
