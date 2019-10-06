import os
import time

import pandas as pd
import requests

from secrets import username, password


def sync_set(session, set_number, sync_directory, save_response=True):
    data = {
        "itemType": "S",
        "selYear": "Y",
        "selWeight": "Y",
        "selDim": "Y",
        "viewType": "4",
        "itemTypeInv": "S",
        "itemNo": set_number,
        "downloadType": "T",
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0"
    }

    res = session.post(
        url="https://www.bricklink.com/catalogDownload.asp?a=a",
        data=data,
        headers=headers,
    )

    if res.status_code == 200:
        if save_response:
            with open(
                f"{sync_directory}/{set_number}.tsv", "w+", encoding="utf-8"
            ) as file:
                file.write(res.text)

    else:
        print(f"sync failed with status code {res.status_code} for set {set_number}")


def get_session():
    session = requests.Session()

    data = {
        "userid": username,
        "password": password,
        "override": "false",
        "keepme_loggedin": "false",
        "mid": "16b44759b6f00000-293bd8adde9ee65b",
        "pageid": "MAIN",
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0"
    }

    res = session.post(
        "https://www.bricklink.com/ajax/renovate/loginandout.ajax",
        data=data,
        headers=headers,
    )

    print(f"logged in status code {res.status_code}")

    return session


if __name__ == "__main__":
    # get relevant sets to sync
    df_sets = pd.read_csv("sets-brickset.csv")
    df_sets["number"] = [
        f"{number}-{variant}"
        for number, variant in zip(df_sets["Number"], df_sets["Variant"])
    ]
    df_sets = df_sets.dropna(subset=["USPrice"])

    # get sets that have not been synced yet
    sync_directory = "set-inventories"
    synced_sets = {s.split(".")[0] for s in os.listdir(sync_directory)}
    sets_to_sync = {s for s in df_sets["number"] if s not in synced_sets}

    # init session
    session = get_session()

    # load page so the rest are tsvs
    sync_set(session, "", "", save_response=False)

    # save tsvs of sets
    num_synced = 0
    for set_number in sets_to_sync:
        sync_set(session, set_number, sync_directory)

        num_synced += 1
        if num_synced % 50 == 0:
            print(f"synced {num_synced} of {len(sets_to_sync)}")

        # crude rate limit
        time.sleep(0.05)
