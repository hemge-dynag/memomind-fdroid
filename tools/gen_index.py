#!/usr/bin/env python3
"""Regenere l'index F-Droid (v1) du depot hemge-dynag/fdroid.

Usage: python3 gen_index.py <chemin vers le dossier fdroid/repo>

Le dossier doit contenir les APK, les icones <package>.<size>.png et
metadata/<package>.yml. L'index est ecrit dans fdroid/repo/index-v1.json.
"""
import hashlib, json, pathlib, sys

FDROID = pathlib.Path(__file__).resolve().parents[2] / 'repos' / 'memomind-cardio-android'

APPS = {
    'com.dynag.cardio': {
        'name': 'MemoMind Cardio',
        'summary': 'Cardio BPM on MemoMind glasses',
        'license': 'Proprietary',
        'categories': ['Health & Fitness'],
        'sourceCode': 'https://github.com/hemge-dynag/memomind-cardio',
        'fr': ('Cardio BPM sur les lunettes MemoMind',
               'Application cardio native : frequence cardiaque BLE, temps, vitesse et '
               'distance sur les lunettes MemoMind. Sports : course, marche, autre sport '
               '(BPM + temps seulement).'),
        'apks': [('1.2.17', 20, 'memomind-cardio-1.2.17.apk', 26, 34)],
    },
    'com.dynag.memoonly': {
        'name': 'MemOnly',
        'summary': 'Cardio + music on MemoMind glasses',
        'license': 'Proprietary',
        'categories': ['Health & Fitness', 'Multimedia'],
        'sourceCode': 'https://github.com/hemge-dynag/memomind-memoonly',
        'fr': ('Cardio et musique sur les lunettes MemoMind',
               'Application native unique pour les lunettes MemoMind, en trois onglets (Cardio, Config, Musique) avec une connexion unique des lunettes : '
               'Cardio (frequence cardiaque BLE, temps, vitesse et distance) et Musique '
               '(titre, artiste, pochette et progression de la musique du telephone). '
               'Bouton des lunettes : lecture/pause en onglet Musique.'),
        'apks': [
            ('1.1.1', 12, 'memoonly-1.1.1.apk', 26, 34),
            ('1.1.0', 11, 'memoonly-1.1.0.apk', 26, 34),
            ('1.0.9', 10, 'memoonly-1.0.9.apk', 26, 34),
            ('1.0.8', 9, 'memoonly-1.0.8.apk', 26, 34),
            ('1.0.7', 8, 'memoonly-1.0.7.apk', 26, 34),
            ('1.0.6', 7, 'memoonly-1.0.6.apk', 26, 34),
            ('1.0.5', 6, 'memoonly-1.0.5.apk', 26, 34),
            ('1.0.4', 5, 'memoonly-1.0.4.apk', 26, 34),
            ('1.0.3', 4, 'memoonly-1.0.3.apk', 26, 34),
            ('1.0.2', 3, 'memoonly-1.0.2.apk', 26, 34),
            ('1.0.1', 2, 'memoonly-1.0.1.apk', 26, 34),
            ('1.0.0', 1, 'memoonly-1.0.0.apk', 26, 34),
        ],
    },
}


def main(repo: pathlib.Path) -> int:
    apps, packages = [], []
    for pkg, meta in APPS.items():
        newest = max(meta['apks'], key=lambda a: a[1])
        apps.append({
            'packageName': pkg,
            'icon': f'{pkg}.48.png',
            'license': meta['license'],
            'categories': meta['categories'],
            'sourceCode': meta['sourceCode'],
            'suggestedVersionCode': str(newest[1]),
            'suggestedVersionName': newest[0],
            'localized': {
                'en': {'name': meta['name'], 'summary': meta['summary']},
                'fr': {'name': meta['name'], 'summary': meta['fr'][0],
                       'description': meta['fr'][1]},
            },
        })
        for version_name, code, apk_name, min_sdk, target_sdk in meta['apks']:
            apk = repo / apk_name
            data = apk.read_bytes()
            packages.append({
                'packageName': pkg,
                'versionName': version_name,
                'versionCode': code,
                'apkName': apk_name,
                'size': len(data),
                'hash': hashlib.sha256(data).hexdigest(),
                'hashType': 'sha256',
                'minSdkVersion': min_sdk,
                'targetSdkVersion': target_sdk,
                'nativecode': [],
                'added': int(apk.stat().st_mtime * 1000),
            })
    packages_by_name = {}
    for p in packages:
        packages_by_name.setdefault(p['packageName'], []).append(p)
    ts_ms = max(p['added'] for p in packages)
    for app in apps:
        app['added'] = ts_ms
        app['lastUpdated'] = ts_ms
    index = {
        'repo': {
            'timestamp': ts_ms,
            'version': 1,
            'name': 'MemoMind',
            'icon': 'com.dynag.cardio.48.png',
            'address': 'https://hemge-dynag.github.io/memomind-fdroid/repo',
            'mirrors': [],
            'description': 'Depot F-Droid MemoMind (apps APK natives, ex. Cardio).',
        },
        'requests': {'install': [], 'uninstall': []},
        'apps': apps,
        'packages': packages_by_name,
    }
    out = repo / 'index-v1.json'
    out.write_text(json.dumps(index, indent=1, ensure_ascii=False) + '\n')
    print(f'{out}: {len(apps)} app(s), {len(packages)} APK')
    return 0


if __name__ == '__main__':
    sys.exit(main(pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'fdroid/repo')))
