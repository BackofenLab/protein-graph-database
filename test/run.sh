#!/bin/bash

# Load the toy database
psql -U postgres -c "DROP DATABASE string;"
psql -U postgres -c "CREATE DATABASE string;"
psql -U postgres string < sql/dump.schema.psql
psql -U postgres string < sql/dump.test.psql

# Run the unit tests
export PYTHONPATH=$PYTHONPATH:$(pwd)
python test/test_kegg.py
python test/test_sql_queries.py
python translate_db.py --credentials test/credentials.test.json --kegg_organism_id "mmu" --species_name "Mus musculus"
python test/test_cypher_queries.py
