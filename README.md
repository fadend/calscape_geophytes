# Geophytes in Calscape

This project is not affiliated with [Calscape](https://calscape.org) but uses data
provided by [Calscape](https://calscape.org).

It aims to generate a list of all geophytes in California based on the description
given by Philip Rundel in his article "Making Sense of Geophyte Diversity" in
Fremontia, Volume 44, Number 3, 2016, available online here:
https://cnps.org/wp-content/uploads/2018/03/FremontiaV44.3.pdf.

The inputs can be downloaded starting from https://calscape.org/search
and https://www.inaturalist.org/pages/developers.

## Usage

```
# Install
python -m venv geophytesenv
cd geophytesenv
bin/pip3 install git+https://github.com/fadend/calscape_geophytes

# Run
bin/python -m calscape_geophytes.calscape_geophytes \
  "--calscape_xlsx=$HOME/Downloads/calscape_geophytes/Native To California.xlsx" \
  --inat_taxa_csv=$HOME/Downloads/calscape_geophytes/inaturalist-taxonomy.dwca/taxa.csv \
  --output_csv geophytes_with_cultivars.csv
```

## Acknowledgments

Thank you, CNPS, for Calscape! Thanks to iNaturalist for the taxa data (and everything else)!

Thank you to Philip Rundel for the fascinating article.

Thank you, Eric Gazoni and Charlie Clark, for the super helpful
[openpyxl](https://pypi.org/project/openpyxl/) package!

Code was formatted using [black](https://github.com/psf/black).
