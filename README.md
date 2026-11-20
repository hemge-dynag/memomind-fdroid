# Dépôt F-Droid MemoMind

Dépôt F-Droid secondaire pour les APK natifs MemoMind (ex. MemoMind Cardio).

## Ajouter le dépôt dans F-Droid

1. Ouvrir **F-Droid** → **Paramètres** → **Dépôts** → **+** (Ajouter un dépôt).
2. Saisir l'URL :

   ```
   https://hemge-dynag.github.io/memomind-fdroid/repo
   ```

3. Valider, puis lancer **Mettre à jour** (tirer vers le bas dans l'onglet Derniers).
4. Les applications MemoMind apparaissent dans F-Droid, prêtes à installer/mettre à jour.

Empreinte de signature du dépôt (SHA-256) :

```
0E:7A:8A:A3:6F:33:07:95:8F:91:80:2E:9C:BA:27:90:60:8B:EE:2D:83:A2:E5:CF:01:55:C9:03:7A:67:9E:5F
```

## Applications

- **MemoMind Cardio** (`com.dynag.cardio`) — Cardio BPM sur les lunettes MemoMind.
- **MemoMind Music** (`com.dynag.music`) — Musique en cours (titre, artiste, pochette, progression) sur les lunettes MemoMind.

## Détails techniques

- Index F-Droid **v2 natif** : `repo/entry.jar` (signé) + `repo/index-v2.json`.
- Ancien index v1 conservé : `repo/index-v1.jar` + `repo/index-v1.json` (rétro-compatibilité).
- APK et icônes dans `repo/`.
- Index généré par `tools/gen_index_v2.py`, signé par `tools/sign_index.py`
  (Python + `cryptography`, sans JDK).
