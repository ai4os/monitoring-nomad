"""
Retrieve Nomad cluster metrics from PAPI and preprocess them to put in a nice table format.
We enrich original PAPI stats with additional info like info on the Ansible commits.
"""
from datetime import datetime

from dotenv import load_dotenv
import nomad
import pandas as pd
import requests
import warnings


# Read Nomad envvars
load_dotenv()

Nomad = nomad.Nomad()

# Disable insecure requests warning from Nomad
warnings.filterwarnings("ignore")


def get_cluster_overview_df():
    # Get PAPI-processed stats
    r = requests.get(
        "https://api.cloud.ai4eosc.eu/v1/deployments/stats/cluster",
        headers={"accept": "application/json"},
    )
    r.raise_for_status()
    stats = r.json()


    # Get some additional node metadata directly from Nomad
    ansible_commits = []
    for _, d in stats["datacenters"].items():
        for nid, nstats in d["nodes"].items():
            node = Nomad.node.get_node(nid)

            # Add ansible commit
            nstats["ansible"] = node["Meta"]["ansible_version"][:7]
            ansible_commits.append(nstats["ansible"])

            # Add latest timestamp where tests were executed
            nstats["last_tested"] = node["Meta"].get("last_tested", None)


    # We retrieve commit information from github to flag as problematic all the nodes that
    # are running an ansible version that is older than the most updated node
    url = "https://api.github.com/repos/ai4os/ai4-ansible/commits"
    response = requests.get(url)
    commits = response.json()
    shas = [c["sha"][:7] for c in commits]
    sha_union = [sha for sha in shas if sha in ansible_commits] # sometimes can be empty if the most updated node is still running a very old commit that wasn't returned in the the first Github request

    # Outdated dict says what is the number of "steps" a given ansible commit is outdated
    # with respect to the most updated commit
    outdated = {}
    for k in ansible_commits:
        if k in sha_union:
            outdated[k] = sha_union.index(k)
        else:
            outdated[k] = len(sha_union)

    # Put everything in a Dataframe
    headers = [
        "datacenter",
        "id",
        "name",
        "namespaces",
        "status",
        "tags",
        "type",
        "eligibility",
        "job_num",
        "reallocations",
        "gpu_models",
    ]
    resources = ["gpu", "cpu", "ram", "disk"]
    for r in resources:
        headers += [f"{r}_used", f"{r}_total", f"{r}_%"]
    headers += [
        "last_tested",
        "ansible",
    ]
    out = {k: [] for k in headers}

    for did, datacenter in stats["datacenters"].items():
        for nid, node in datacenter["nodes"].items():
            out["datacenter"].append(did)
            out["id"].append(nid)
            out["name"].append(node["name"])
            out["namespaces"].append(node["namespaces"])
            out["status"].append(node["status"])
            out["tags"].append(node["tags"])
            out["type"].append(node["type"])
            out["eligibility"].append(node["eligibility"])
            out["job_num"].append(node["jobs_num"])
            out["reallocations"].append(node["reallocations"])
            out["last_tested"].append(node["last_tested"])
            out["ansible"].append(node["ansible"])

            if len(node["gpu_models"]) == 1:
                gpu_models = list(node["gpu_models"].keys())[0]
            elif len(node["gpu_models"]) > 1:
                gpu_models = node["gpu_models"]
            else:
                gpu_models = None
            out["gpu_models"].append(gpu_models)

            for r in resources:
                out[f"{r}_used"].append(node[f"{r}_used"])
                out[f"{r}_total"].append(node[f"{r}_total"])

                if node[f"{r}_total"]:
                    per = node[f"{r}_used"] / node[f"{r}_total"]
                    per = per
                else:
                    per = None
                out[f"{r}_%"].append(per)


    df = pd.DataFrame.from_dict(out)
    df = df.sort_values(by="name")

    # Convert columns to integer and rename
    df["ram_total"] = (df["ram_total"] / 10**3).astype(int)
    df["disk_total"] = (df["disk_total"] / 10**3).astype(int)
    df = df.rename(
        columns={
            "ram_total": "ram_total (GB)",
            "disk_total": "disk_total (GB)",
        }
    )

    return df

if __name__ == "__main__":
    df = get_cluster_overview_df()
    df.to_csv("cluster-overview.csv", index=False)
