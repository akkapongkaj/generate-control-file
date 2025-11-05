# generate-control-file

A small command-line utility that creates a ``.CTL`` control file for a given
text data file. The generated file follows the five-column, pipe-delimited
layout:

1. Processing/System date (``YYYYMMDD``)
2. Data date (``YYYYMMDD``)
3. Total number of data records
4. Data file name (with extension)
5. Checksum of the data file

The checksum defaults to the MD5 algorithm to match the reference example, but
SHA-256 and SHA-512 are also supported.

## Installation

The script is self-contained and only requires Python 3.9 or newer. Clone or
copy this repository and run the script directly with Python:

```bash
python3 generate_control_file.py --help
```

## Usage

```bash
python3 generate_control_file.py \
  --processing-date 20240125 \
  --data-date 20240125 \
  --checksum-algorithm md5 \
  --create-empty-data-file \
  --skip-header 0 \
  --skip-footer 0 \
  path/to/NCB_HPCHGREPOS.txt
```

The command above will create ``NCB_HPCHGREPOS.txt.CTL`` in the same directory
as the source file. The ``--data-date`` option defaults to the processing date,
and the header/footer arguments allow you to exclude leading or trailing lines
(such as report headers) from the record count. If the ``--create-empty-data-file``
flag is provided and the source file does not exist, the script will create an
empty placeholder file before generating the control file, resulting in a record
count of zero and the checksum of an empty file.

### Example

Assuming ``NCB_HPCHGREPOS.txt`` contains three data rows without headers:

```text
record-1
record-2
record-3
```

Running:

```bash
python3 generate_control_file.py --processing-date 20240125 NCB_HPCHGREPOS.txt
```

Produces ``NCB_HPCHGREPOS.txt.CTL`` with the following content:

```
20240125|20240125|3|NCB_HPCHGREPOS.txt|9c224837cb6023fdabb7e7b84052f49d
```

The checksum in the example is the MD5 digest of ``NCB_HPCHGREPOS.txt``.
