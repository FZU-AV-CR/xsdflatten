#!/usr/bin/env python3
import sys
import re
import copy
import os
import argparse
from lxml import etree

def get_includes_from_file(filename):
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
			pass #print('There is a problem with include %s in file %s' % (inc, filename))

	return includes

def get_includes_recurse(filename, include_set):
	includes = get_includes_from_file(filename)
	# Convert relative paths to absolute paths based on the current file's directory
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
	tree = etree.parse(filename)
	return tree.getroot()

def remove_includes(root):
	# Find and remove the includes
	includes = root.findall('xs:include', root.nsmap)
	for inc in includes:
		root.remove(inc)
	return root

def flatten_file(filename):
	include_set = set()
	get_includes_recurse(filename, include_set)

	# Get the main document
	root = get_xml_tree_from_file(filename)
	root = remove_includes(root)
	
	# Merge in the elements of the includes
	for inc_file in include_set:
		inc_root = get_xml_tree_from_file(inc_file)
		inc_root = remove_includes(inc_root)
		root.append(etree.Comment('Imported from %s' % inc_file))
		for child in inc_root:
			root.append(copy.deepcopy(child))

	return etree.tostring(root, pretty_print=True, encoding='unicode')

def main():
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
