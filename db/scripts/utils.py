import pandas as pd
import yaml
import csv
from time import time
import neo4j


class Reformatter:
    def __init__(self, prefix: str):
        self.prefix = prefix

    def run(self, input: str, mode: str):
        if mode == "tf":
            return self.run_timeframes(input=input)

    def run_timeframes(self, input: str):
        s = input.replace(self.prefix, "").split(sep="_")
        return "-".join([p.replace("wt", "") for p in s])


def read_creds(credentials_path: str):
    with open(credentials_path, "rt", encoding="utf-8") as credentials_file:
        credentials = yaml.load(credentials_file, Loader=yaml.FullLoader)

    neo4j = credentials["neo4j"]
    return "neo4j://{}:{}".format(neo4j["host"], neo4j["port"]), (neo4j["username"], neo4j["password"])


def start_driver():
    uri, auth = read_creds(credentials_path=os.getenv("_DEFAULT_CREDENTIALS_PATH"))
    driver = neo4j.GraphDatabase.driver(uri, auth=auth)
    driver.verify_connectivity()
    return driver


def stop_driver(driver: neo4j.Driver):
    driver.close()


def execute_query(query: str, read: bool, driver: neo4j.Driver) -> pd.DataFrame:
    if os.getenv("_UPDATE_NEO4J") == str(True):
        with driver.session() as session:
            # TODO Remove if statement?
            if not read:
                tmp = session.run(query).values()
                return tmp
            else:
                tmp = session.run(query).values()
                return tmp
    else:
        return pd.DataFrame([0], columns=["id"])


def save_df_to_csv(file_name: str, df: pd.DataFrame, override_prod: bool = False):
    if _PRODUCTION or override_prod:
        df.to_csv(_NEO4J_IMPORT_PATH + file_name, index=False)
    else:
        df.iloc[:_DEV_MAX_REL].to_csv(_NEO4J_IMPORT_PATH + file_name, index=False)


def time_function(function, variables: dict = {}):
    start_time = time()
    result = function(**variables)
    end_time = time()

    with open(_FUNCTION_TIME_PATH, "a", newline="\n") as csvfile:
        writer = csv.writer(csvfile, delimiter="\t")
        writer.writerow([function.__name__, end_time - start_time])

    return result


def print_update(update_type: str, text: str, color: str):
    colors = {
        "red": "\033[0;31m",
        "orange": "\033[0;33m",
        "blue": "\033[0;34m",
        "pink": "\033[0;35m",
        "cyan": "\033[0;36m",
        "light-yellow": "\033[0;93m",
        "none": "\033[0m",
    }
    if os.getenv("_SILENT") != str(True):
        print("{}{}{}:{}{}".format(colors[color], update_type, colors["none"], " " * (16 - len(update_type)), text))
        if update_type == "Done":
            print("")


@time_function
def get_consistent_entries(comparing_genes: pd.DataFrame, complete: pd.DataFrame, mode: int):
    comparing_genes_filter = comparing_genes.filter(items=["ENSEMBL"]).drop_duplicates(ignore_index=True)
    ensembl_genes = complete.filter(items=["ENSEMBL"]).drop_duplicates(ignore_index=True)
    not_included = comparing_genes[
        comparing_genes["ENSEMBL"].isin(set(comparing_genes_filter["ENSEMBL"]).difference(ensembl_genes["ENSEMBL"]))
    ]
    not_included.to_csv(
        "../source/not_included_{}.csv".format("string" if mode == 0 else "exp"), mode="a", header=False, index=False
    )

    return comparing_genes[
        ~comparing_genes["ENSEMBL"].isin(set(comparing_genes["ENSEMBL"]).difference(ensembl_genes["ENSEMBL"]))
    ]


def remove_bidirectionality(df: pd.DataFrame, columns: tuple[str], additional: list[str]) -> pd.DataFrame:
    df_dict = dict()
    for _, row in df.iterrows():
        vals = [row[j] for j in additional]
        key = frozenset([row[columns[0]], row[columns[1]]])
        if key not in df_dict.keys():
            df_dict[key] = vals
    df_list = [[*list(i), *df_dict[i]] for i in df_dict.keys()]
    df_list = pd.DataFrame(df_list, columns=[columns[0], columns[1], *additional])
    df_list.to_csv("../source/misc/test.csv", index=False)
    return df_list


def generate_props(source: dict[str, list[tuple[str]]], item: str, reformat_values: dict[str], where: bool):
    """
    source -> Prop_name, Value, Comparison
    """
    tmp_query = ""
    for key in source.keys():
        tuples = source[key]
        tmp_query = "("
        for k, i in enumerate(tuples):
            front, back = (
                (reformat_values[i[0]][0], reformat_values[i[0]][1]) if i[0] in reformat_values.keys() else ("", "")
            )
            tmp_query += f"{item}.{i[0]} {i[2]} {front}{i[1]}{back} "
            if k < len(tuples) - 1:
                tmp_query += f"{key} "
        tmp_query += ") "
    if len(tmp_query) > 0 and where:
        props_query = "WHERE "
        where = not where
    elif len(tmp_query) > 0 and not where:
        props_query = "AND "
    else:
        props_query = ""

    props_query += tmp_query
    return props_query, where


def check_for_files(mode: int):
    if mode == 0:
        # Experiment
        return not (
            os.path.exists("../source/processed/tg_mean_count.csv")
            and os.path.exists("../source/processed/tf_mean_count.csv")
            and os.path.exists("../source/processed/de_values.csv")
            and os.path.exists("../source/processed/or_nodes.csv")
            and os.path.exists("../source/processed/or_mean_count.csv")
            and os.path.exists("../source/processed/da_values.csv")
            and os.path.exists("../source/processed/tf_tg_corr.csv")
            and os.path.exists("../source/processed/or_tg_corr.csv")
            and os.path.exists("../source/processed/motif.csv")
            and os.path.exists("../source/processed/distance.csv")
        )

    elif mode == 1:
        # STRING
        return not (
            os.path.exists("../source/processed/gene_gene_scores.csv")
            and os.path.exists("../source/processed/genes_annotated.csv")
        )

    elif mode == 2:
        # ENSEMBL
        return not (os.path.exists("../source/processed/complete.csv") and os.path.exists("../source/processed/tf.csv"))

    elif mode == 3:
        # Functional
        return not (
            os.path.exists("../source/processed/ft_nodes.csv")
            and os.path.exists("../source/processed/ft_gene.csv")
            and os.path.exists("../source/processed/ft_ft_overlap.csv")
        )
