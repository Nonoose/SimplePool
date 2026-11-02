# SimplePool

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
Intégration Home Assistant pour piloter la pompe de filtration d'une piscine, livrée avec sa propre carte Lovelace en forme de **programmateur mécanique 24 h**.
Intégration créée avec l'aide de Claude

## Fonctionnalités

- **2 plages de filtration** réglables par pas de 30 min (passage de minuit géré).
- **Programmation** : son arrêt coupe tout, y compris la pompe.
- **Hors gel** : la pompe tourne en continu quand l'air passe sous le seuil, puis s'arrête à seuil + 1 °C. Activer le hors gel coupe la programmation et le Boost.
- **Boost** : marche forcée pendant une durée réglable (30 min à 12 h), conservée après un redémarrage.
- **Durée conseillée** selon la règle « température de l'eau ÷ 2 » (4 h sous 12 °C).
- **Turnover** : part du volume filtrée par jour.
- **Carte intégrée**, chargée automatiquement, sans dépendance (ni button-card, ni Mushroom, ni card-mod).

## Installation

### Avec HACS (recommandé)

1. HACS → menu ⋮ → **Dépôts personnalisés**.
2. URL : `https://github.com/Nonoose/SimplePool`, type **Intégration**.
3. Recherchez **SimplePool**, téléchargez-la, puis redémarrez Home Assistant.

### Manuelle

Copiez `custom_components/simplepool` dans `/config/custom_components/`, puis redémarrez.

## Configuration

*Paramètres → Appareils et services → Ajouter une intégration → SimplePool*, puis choisissez :

| Champ | Obligatoire | Exemple |
|---|---|---|
| Pompe (`switch`, `input_boolean` ou `light`) | Oui | `switch.pompe_piscine` |
| Température de l'eau | Non | `sensor.temperature_piscine` |
| Température extérieure (hors gel) | Non | `sensor.temperature_exterieure` |

Ces choix se modifient ensuite via **Configurer** sur l'intégration.

## Carte

Ajoutez une carte manuelle :

```yaml
type: custom:simplepool-card
```

Options :

```yaml
type: custom:simplepool-card
title: Ma piscine          # titre affiché
entities:                  # seulement si vous avez renommé des entités
  vol: number.mon_volume
```

Clés de `entities` : `prog`, `hg`, `boost`, `p1d`, `p1l`, `p2d`, `p2l`, `vol`, `deb`, `bdur`, `seuil`, `cons`, `turn`, `gel`, `plan`.

## Entités créées

| Entité | Rôle |
|---|---|
| `switch.piscine_programmation` | Programmation |
| `switch.piscine_hors_gel` | Hors gel |
| `switch.piscine_boost` | Boost (attribut `fin`) |
| `select.piscine_plage_1_debut` / `_duree` | Plage 1 |
| `select.piscine_plage_2_debut` / `_duree` | Plage 2 |
| `number.piscine_volume` | Volume (m³) |
| `number.piscine_debit_pompe` | Débit de la pompe (m³/h) |
| `number.piscine_boost_duree` | Durée du Boost (h) |
| `number.piscine_seuil_hors_gel` | Seuil du hors gel (°C) |
| `sensor.piscine_duree_conseillee` | Température de l'eau ÷ 2 (h) |
| `sensor.piscine_turnover` | Turnover (%) |
| `binary_sensor.piscine_gel_detecte` | Hors gel en action |
| `binary_sensor.piscine_pompe_planifiee` | Etat voulu de la pompe |

## Migration depuis le package YAML

Si vous utilisiez l'ancienne version en package (`piscine.yaml`) :

1. Notez vos réglages (plages, volume, débit).
2. Supprimez la ligne `piscine: !include piscine.yaml` de `configuration.yaml` et le fichier `piscine.yaml`.
3. Redémarrez, puis supprimez les entités orphelines `*.piscine_*` dans *Paramètres → Entités*.
4. Ajoutez l'intégration, puis remplacez votre carte par `custom:simplepool-card`.

Les deux versions ne doivent **pas** cohabiter : elles piloteraient la même pompe et certains identifiants seraient en conflit.

## Licence

MIT
