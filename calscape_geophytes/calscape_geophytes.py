"""Find the geophytes in Calscape's database of California native plants.

Based on Philip Rundel's article "Making Sense of Geophyte Diversity" in
Fremontia, Volume 44, Number 3, 2016.
"""

import argparse
import csv
import collections

import openpyxl

# See https://www.mobot.org/mobot/research/APweb/genera/themidaceaegen.html
# and https://en.wikipedia.org/wiki/Brodiaeoideae
BRODIAE_SUBFAMILY_GENUSES = [
    "Androstephium",
    "Bessera",
    "Bloomeria",
    "Brodiaea",
    "Dandya",
    "Dichelostemma",
    "Milla",
    "Muilla",
    "Petronymphe",
    "Triteleia",
    "Triteleiopsis",
]

# See https://www.pacificbulbsociety.org/pbswiki/index.php/Agavaceae
AGAVE_SUBFAMILY_GEOPHYTE_GENUSES = [
    "Camassia",
    "Chlorogalum",
    "Hesperocallis",
    "Leucocrinum",
]


def get_column(
    sheet: openpyxl.worksheet.worksheet.Worksheet,
    expected_name: str = "",
    start_row: int = 6,
    column: str = "A",
) -> list[str]:
    first = sheet[f"{column}{start_row}"].value
    assert (
        first == expected_name
    ), f"Expected {column}{start_row} = {expected_name}; got {first}"
    return [
        row[0].value
        for row in sheet[f"{column}{start_row + 1}" :f"{column}{sheet.max_row}"]
    ]


class CalscapePlants:
    """Wrapper for a Calscape search Excel export."""
    def __init__(self, calscape_xlsx_path: str):
        workbook = openpyxl.load_workbook(calscape_xlsx_path)
        sheet = workbook.active
        species = get_column(sheet, expected_name="Botanical Name", column="A")
        common_names = get_column(sheet, expected_name="Common Name", column="B")
        urls = get_column(sheet, expected_name="Plant Url", column="AW")
        self.genus_to_species = collections.defaultdict(set)
        for x in species:
            self.genus_to_species[x.split(" ")[0]].add(x)
        self.species_to_url = dict(zip(species, urls))
        self.species_to_common_name = dict(zip(species, common_names))

    def genuses(self) -> set[str]:
        return set(self.genus_to_species.keys())

    def species_for_genus(self, genus: str) -> set[str]:
        return set(self.genus_to_species.get(genus, ()))

    def common_name_for_species(self, species: str) -> str:
        return self.species_to_common_name[species]

    def url_for_species(self, species: str) -> str:
        return self.species_to_url[species]


class InatPlantTaxa:
    """Wrapper for iNaturalist taxa data."""
    def __init__(self, inat_taxa_csv_path: str):
        self.family_to_genus = collections.defaultdict(set)
        self.genus_to_family = {}
        with open(inat_taxa_csv_path, "rt", encoding="utf8") as f:
            for row in csv.DictReader(f):
                if row["kingdom"] == "Plantae" and row["taxonRank"] == "genus":
                    self.family_to_genus[row["family"]].add(row["scientificName"])
                    self.genus_to_family[row["scientificName"]] = row["family"]

    def genuses_for_family(self, family: str) -> set[str]:
        return set(self.family_to_genus.get(family, ()))

    def family_for_genus(self, genus: str) -> str:
        return self.genus_to_family[genus]


class CalscapeGeophytes:
    """Find California geophytes based on family and subfamily/genus."""
    def __init__(self, calscape_plants: CalscapePlants, inat_taxa: InatPlantTaxa):
        self.calscape_plants = calscape_plants
        self.inat_taxa = inat_taxa
        self.calscape_genuses = calscape_plants.genuses()
        self.geophytes = set()
        self.add_family("Liliaceae")
        for genus in BRODIAE_SUBFAMILY_GENUSES:
            self.add_genus(genus)
        self.add_genus("Allium")
        self.add_family("Iridaceae")
        for genus in AGAVE_SUBFAMILY_GEOPHYTE_GENUSES:
            self.add_genus(genus)
        self.add_family("Tecophilaeaceae")
        self.family_tree = collections.defaultdict(lambda: collections.defaultdict(set))
        for species in self.geophytes:
            genus = species.split(" ")[0]
            family = self.inat_taxa.family_for_genus(genus)
            self.family_tree[family][genus].add(species)

    def add_family(self, family: str):
        in_calscape = self.calscape_genuses & self.inat_taxa.genuses_for_family(family)
        for genus in in_calscape:
            self.add_genus(genus)

    def add_genus(self, genus: str):
        self.geophytes.update(self.calscape_plants.species_for_genus(genus))

    def print_summary(self):
        num_geophytes = len(self.geophytes)
        num_no_cultivars = sum(1 for x in self.geophytes if "'" not in x)
        num_genera = sum(len(x) for x in self.family_tree.values())
        print(
            f"Found {num_geophytes} geophytes, {num_no_cultivars} excluding cultivars"
        )
        print(f"{num_genera} genera across {len(self.family_tree)} families")

    def write_csv(self, path: str, exclude_cultivars=False):
        families = sorted(self.family_tree.keys())
        rows = []
        for family in families:
            genuses = sorted(self.family_tree[family].keys())
            for genus in genuses:
                species = sorted(self.family_tree[family][genus])
                for name in species:
                    if exclude_cultivars and "'" in name:
                        continue
                    rows.append(
                        {
                            "family": family,
                            "genus": genus,
                            "species": name,
                            "common_name": self.calscape_plants.common_name_for_species(
                                name
                            ),
                            "url": self.calscape_plants.url_for_species(name),
                        }
                    )
        if not rows:
            return
        with open(path, "wt", encoding="utf8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="calscape_geophytes")
    parser.add_argument(
        "--calscape_xlsx",
        required=True,
        help="Path to .xlsx file with a listing of the plants in Calscape",
    )
    parser.add_argument(
        "--inat_taxa_csv", required=True, help="Path to iNaturalist taxa CSV"
    )
    parser.add_argument(
        "--exclude_cultivars",
        help="Whether to exclude cultivars",
        action="store_true",
    )
    parser.add_argument(
        "--output_csv", default="", help="Path at which to write geophytes CSV"
    )
    args = parser.parse_args()
    calscape_plants = CalscapePlants(args.calscape_xlsx)
    inat_taxa = InatPlantTaxa(args.inat_taxa_csv)
    geophytes = CalscapeGeophytes(calscape_plants=calscape_plants, inat_taxa=inat_taxa)
    geophytes.print_summary()
    if args.output_csv:
        geophytes.write_csv(args.output_csv, exclude_cultivars=args.exclude_cultivars)
