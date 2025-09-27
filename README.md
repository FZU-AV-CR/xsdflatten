# xsdflatten

Python 3 script to flatten an XSD schema into a single document by merging all included schemas. The flattened schema is printed to the console.

## Installation

Install directly from source:
```bash
pip3 install .
```

Or for development:
```bash
pip3 install -e .
```

After installation, you can use the `xsdflatten` command directly.

## Dependencies

If installing manually, install dependencies using:
```bash
pip3 install -r requirements.txt
```

## Usage

After installation via pip:
```bash
xsdflatten input_schema.xsd
xsdflatten --output flattened.xsd input_schema.xsd
```

Or run directly without installation:
```bash
python3 xsdflatten.py input_schema.xsd
python3 xsdflatten.py --output flattened.xsd input_schema.xsd
```

### Options

- `input_file` - Input XSD file to flatten (required)
- `-o, --output FILE` - Output file (if not specified, prints to stdout)
- `-h, --help` - Show help message

The script processes the main XSD file and all its includes (recursively), then outputs a single flattened XSD schema. Use `-o` parameter to save to a file or redirect stdout with `>`.

## Attribution

This project is based on the original tool [esunder/xsdflatten](https://github.com/esunder/xsdflatten) and is further developed and extended.
