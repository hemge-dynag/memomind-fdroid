#!/usr/bin/env python3
"""Genere l'index F-Droid v2 (index-v2.json + entry.json) du depot memomind-fdroid.

Usage: python3 gen_index_v2.py <repo_dir>

Ecrit repo_dir/index-v2.json (IndexV2) et repo_dir/entry.json (Entry).
L'APK et les icones doivent etre presents dans <repo_dir>.
Tous les FileV2 portent sha256 + size et un nom absolu (commencant par /),
comme l'exige DbV2StreamReceiver.
"""
import hashlib
import json
import pathlib
import sys

REPO_ADDRESS = "https://hemge-dynag.github.io/memomind-fdroid/repo"

APPS = {
    "com.dynag.cardio": {
        "name": "MemoMind Cardio",
        "summary": "Cardio BPM on MemoMind glasses",
        "license": "Proprietary",
        "categories": ["Health & Fitness"],
        "sourceCode": "https://github.com/hemge-dynag/memomind-cardio",
        "icon": "com.dynag.cardio.48.png",
        "fr": (
            "Cardio BPM sur les lunettes MemoMind",
            "Application cardio native : frequence cardiaque BLE, temps, vitesse et "
            "distance sur les lunettes MemoMind. Sports : course, marche, autre sport "
            "(BPM + temps seulement).",
        ),
        "apks": [
            ("1.2.17", 20, "memomind-cardio-1.2.17.apk", 26, 34,
             "f08b0a25bf0d06ee17b7bd39d03349aa531d6ae49fa61bac6a63b99157ffaaeb"),
        ],
    },
    "com.dynag.memoonly": {
        "name": "MemoOnly",
        "summary": "Cardio + music on MemoMind glasses",
        "license": "Proprietary",
        "categories": ["Health & Fitness", "Multimedia"],
        "sourceCode": "https://github.com/hemge-dynag/memomind-memoonly",
        "icon": "com.dynag.memoonly.48.png",
        "fr": (
            "Cardio et musique sur les lunettes MemoMind",
            "Application native unique pour les lunettes MemoMind, en deux onglets : "
            "Cardio (frequence cardiaque BLE, temps, vitesse et distance) et Musique "
            "(titre, artiste, pochette et progression de la musique du telephone). "
            "Bouton des lunettes : lecture/pause en onglet Musique.",
        ),
        "apks": [
            ("1.0.0", 1, "memoonly-1.0.0.apk", 26, 34,
             "f08b0a25bf0d06ee17b7bd39d03349aa531d6ae49fa61bac6a63b99157ffaaeb"),
        ],
    }
}


def file_v2(repo: pathlib.Path, name: str) -> dict:
    data = (repo / name).read_bytes()
    return {
        "name": "/" + name,
        "sha256": hashlib.sha256(data).hexdigest(),
        "size": len(data),
    }


def main(repo: pathlib.Path) -> int:
    packages = {}
    newest_ts = 0
    for pkg, meta in APPS.items():
        icon = file_v2(repo, meta["icon"])
        versions = {}
        newest = max(meta["apks"], key=lambda a: a[1])
        for vname, code, apk_name, min_sdk, target_sdk, signer_hex in meta["apks"]:
            apk = repo / apk_name
            data = apk.read_bytes()
            sha = hashlib.sha256(data).hexdigest()
            added = int(apk.stat().st_mtime * 1000)
            newest_ts = max(newest_ts, added)
            versions[sha] = {
                "added": added,
                "file": {"name": "/" + apk_name, "sha256": sha, "size": len(data)},
                "manifest": {
                    "versionName": vname,
                    "versionCode": code,
                    "usesSdk": {"minSdkVersion": min_sdk, "targetSdkVersion": target_sdk},
                    "signer": {"sha256": [signer_hex]},
                    "usesPermission": [],
                    "nativecode": [],
                },
                "releaseChannels": [],
                "antiFeatures": {},
                "whatsNew": {},
            }
        packages[pkg] = {
            "metadata": {
                "name": {"en": meta["name"], "fr": meta["name"]},
                "summary": {"en": meta["summary"], "fr": meta["fr"][0]},
                "description": {"fr": meta["fr"][1]},
                "added": newest_ts,
                "lastUpdated": newest_ts,
                "license": meta["license"],
                "sourceCode": meta["sourceCode"],
                "categories": meta["categories"],
                "icon": {"en": icon},
            },
            "versions": versions,
        }

    num_packages = sum(len(p["versions"]) for p in packages.values())
    ts = newest_ts
    index = {
        "repo": {
            "name": {"en": "MemoMind", "fr": "MemoMind"},
            "description": {
                "en": "MemoMind F-Droid repository (native APKs: Cardio, MemoOnly).",
                "fr": "Depot F-Droid MemoMind (apps APK natives : Cardio, MemoOnly).",
            },
            "address": REPO_ADDRESS,
            "timestamp": ts,
            "mirrors": [],
        },
        "packages": packages,
    }
    index_bytes = (json.dumps(index, ensure_ascii=False) + "\n").encode()
    (repo / "index-v2.json").write_bytes(index_bytes)

    entry = {
        "timestamp": ts,
        "version": 20001,
        "index": {
            "name": "/index-v2.json",
            "sha256": hashlib.sha256(index_bytes).hexdigest(),
            "size": len(index_bytes),
            "numPackages": num_packages,
        },
        "diffs": {},
    }
    (repo / "entry.json").write_text(json.dumps(entry, indent=2) + "\n")

    print(f"index-v2.json: {len(index_bytes)} o, {num_packages} version(s)")
    print(f"entry.json: timestamp={ts}, sha256={entry['index']['sha256']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "repo")))
