
from pathlib import Path
import requests

CACHE_FILE = Path("ansible_commits_cache.txt")

def refresh_ansible_commits():
    print("Refreshing Ansible commits ...")
    url = "https://api.github.com/repos/ai4os/ai4-ansible/commits"
    response = requests.get(url)
    commits = response.json()
    shas = [c["sha"][:7] for c in commits]

    CACHE_FILE.write_text("\n".join(shas))

    return shas


def compute_ansible_delta(ansible_commits):
    """
    Receives a list of commits and returns a list of how far those commits are with
    respect to latest (0: latest, 1, 2, ...)
    """
    if CACHE_FILE.exists():
        shas = CACHE_FILE.read_text().splitlines()
    else:
        shas = []

    refreshed = False

    delta = []
    for i in ansible_commits:
        if i not in shas:
            if not refreshed:
                shas = refresh_ansible_commits()
                refreshed = True

        if i not in shas:
            delta.append(None)
        else:
            delta.append(shas.index(i))

    return delta
