import ast
import io
import json
import os
import os.path
import sys
import time

import pandas as pd
from flask import Flask, Response, request, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix

import database
import enrichment
import enrichment_graph
import graph_utilities
import jar
import queries

app = Flask(__name__)

# ====================== Index page ======================

_SCRIPT_DIR = os.path.dirname(__file__)
_SERVE_DIR = "../../frontend/dist"
_INDEX_FILE = "index.html"
_BACKEND_JAR_PATH = "../gephi/target/gephi.backend-1.0-SNAPSHOT.jar"


@app.route("/")
def index():
    return send_from_directory(os.path.join(_SCRIPT_DIR, _SERVE_DIR), _INDEX_FILE)


# ====================== Other files ======================


@app.route("/<path:path>")
def files(path):
    return send_from_directory(os.path.join(_SCRIPT_DIR, _SERVE_DIR), path)


# @app.rooute("/api/subgraph/init")


# ====================== Functional Enrichment ======================
# ______functional_enrichment_STRING_________________________________
# TODO Refactor this
# Request comes from functional_enrichment.js
@app.route("/api/subgraph/enrichment", methods=["POST"])
def proteins_enrichment():
    driver = database.get_driver()
    proteins = request.form.get("proteins").split(",")
    species_id = request.form.get("species_id")

    # in-house functional enrichment
    list_enrichment = enrichment.functional_enrichment(driver, proteins, species_id)

    # STRING API functional enrichment
    """df_enrichment = stringdb.functional_enrichment(proteins, species_id)

    list_enrichment = list()
    for _, row in df_enrichment.iterrows():
        list_enrichment.append(dict(
            id=row["term"],
            proteins=row["inputGenes"].split(","),
            name=row["description"],
            category=row["category"],
            p_value=row["p_value"],
            fdr_rate=row["fdr"]
        ))"""

    json_str = json.dumps(list_enrichment.to_dict("records"), ensure_ascii=False, separators=(",", ":"))
    return Response(json_str, mimetype="application/json")


# ====================== Subgraph API ======================
# request comes from home.js
# TODO Refactor this
@app.route("/api/subgraph/proteins", methods=["POST"])
def proteins_subgraph_api():
    driver = database.get_driver()

    # Begin a timer to time
    t_begin = time.time()

    # Queried proteins
    if not request.files.get("file"):
        protein_names = request.form.get("proteins").split(";")
        protein_names = list(filter(None, protein_names))
    else:
        panda_file = pd.read_csv(request.files.get("file"))
        protein_names = panda_file["SYMBOL"].to_list()

    species_id = int(request.form.get("species_id"))
    # DColoumns
    selected_d = request.form.get("selected_d").split(",") if request.form.get("selected_d") else None
    threshold = int(float(request.form.get("threshold")) * 1000)

    protein_ids = queries.get_protein_ids_for_names(driver, protein_names, species_id)

    # Timer to evaluate runtime to setup
    t_setup = time.time()
    print("Time Spent (Setup):", t_setup - t_begin)

    if len(protein_ids) > 1:
        proteins, source, target, score = queries.get_protein_associations(driver, protein_ids, threshold)
    else:
        proteins, source, target, score = queries.get_protein_neighbours(driver, protein_ids, threshold)

    # Timer for Neo4j query
    t_neo4j = time.time()
    print("Time Spent (Neo4j):", t_neo4j - t_setup)

    nodes = pd.DataFrame(proteins).drop_duplicates(subset="external_id")

    edges = pd.DataFrame({"source": source, "target": target, "score": score})
    edges = edges.drop_duplicates(subset=["source", "target"])

    # Check if there is no data from database, return from here
    if edges.empty:
        return Response(json.dumps([]), mimetype="application/json")

    # Timer to evaluate runtime between cypher-shell and extracting data
    t_parsing = time.time()
    print("Time Spent (Parsing):", t_parsing - t_neo4j)
    # Creating only the main Graph and exclude not connected subgraphs
    nodes_sub = graph_utilities.create_nodes_subgraph(edges, nodes)

    # Timer to evaluate enrichments runtime
    t_dvalue = time.time()
    print("Time Spent (DValue):", t_dvalue - t_parsing)

    # D-Value categorize via percentage
    if not (request.files.get("file") is None):
        panda_file.rename(columns={"SYMBOL": "name"}, inplace=True)
        panda_file["name"] = panda_file["name"].str.upper()

    # #Timer to evaluate enrichments runtime
    t_enrich = time.time()
    print("Time Spent (Enrichment):", t_enrich - t_dvalue)

    if len(nodes.index) == 0:
        sigmajs_data = {"nodes": [], "edges": []}
    else:
        # Build a standard input string for Gephi's backend
        nodes_csv = io.StringIO()
        edges_csv = io.StringIO()

        # JAR accepts only id
        nodes["external_id"].to_csv(nodes_csv, index=False, header=True)

        # JAR accepts source, target, score
        edges.to_csv(edges_csv, index=False, header=True)

        stdin = f"{nodes_csv.getvalue()}\n{edges_csv.getvalue()}"
        stdout = jar.pipe_call(_BACKEND_JAR_PATH, stdin)

        sigmajs_data = json.loads(stdout)

    # Timer to evaluate runtime of calling gephi
    t_gephi = time.time()
    print("Time Spent (Gephi):", t_gephi - t_enrich)

    # Create a dictionary mapping ENSEMBL IDs to rows in `nodes`
    ensembl_to_node = dict(zip(nodes["external_id"], nodes.itertuples(index=False)))

    # Iterate over nodes in `sigmajs_data` and update their attributes
    for node in sigmajs_data["nodes"]:
        ensembl_id = node["id"]
        df_node = ensembl_to_node.get(ensembl_id)
        if df_node:
            node["attributes"]["Description"] = df_node.description
            node["attributes"]["Ensembl ID"] = df_node.external_id
            node["attributes"]["Name"] = df_node.name
            if not (request.files.get("file") is None):
                if selected_d != None:
                    for column in selected_d:
                        node["attributes"][column] = panda_file.loc[panda_file["name"] == df_node.name, column].item()
            node["label"] = df_node.name
            node["species"] = str(10090)

    # Identify subgraph nodes and update their attributes
    sub_proteins = []
    ensembl_sub = set(nodes_sub["external_id"])
    for node in sigmajs_data["nodes"]:
        if node["attributes"]["Ensembl ID"] in ensembl_sub:
            sub_proteins.append(node["attributes"]["Ensembl ID"])
        else:
            node["color"] = "rgb(255,255,153)"

    for edge in sigmajs_data["edges"]:
        if edge["source"] not in ensembl_sub and edge["target"] not in ensembl_sub:
            edge["color"] = "rgba(255,255,153,0.2)"

    # Update sigmajs_data with subgraph and other attributes as needed
    if request.form.get("selected_d"):
        sigmajs_data["dvalues"] = selected_d
    sigmajs_data["subgraph"] = sub_proteins

    # Timer for final steps
    t_end = time.time()
    print("Time Spent (End):", t_end - t_gephi)

    json_str = json.dumps(sigmajs_data)

    return Response(json_str, mimetype="application/json")


# =============== Functional Term Graph ======================


# TODO Refactor this
@app.route("/api/subgraph/terms", methods=["POST"])
def terms_subgraph_api():
    # Functional terms
    list_enrichment = ast.literal_eval(request.form.get("func-terms"))

    json_str = enrichment_graph.get_functional_graph(list_enrichment=list_enrichment)

    return Response(json_str, mimetype="application/json")


if __name__ == "__main__":
    if "--pid" in sys.argv:
        with open("process.pid", "w+") as file:
            pid = f"{os.getpid()}"
            file.write(pid)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    if "--server" in sys.argv:
        app.run(host="0.0.0.0", port=80)
    else:
        app.run()
