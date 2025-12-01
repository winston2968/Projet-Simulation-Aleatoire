# ⚛️ Simulation Stochastique de Réacteur Nucléaire

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-En_Développement-orange)

Ce projet implémente une simulation numérique d'un cœur de réacteur nucléaire en 2D. Il combine une approche **stochastique** (Monte-Carlo) pour la neutronique et une approche **déterministe** pour la thermohydraulique et le pilotage automatique.

L'objectif est d'étudier le comportement dynamique d'une population de neutrons, la stabilité du réacteur et l'efficacité des systèmes de régulation (Barres de contrôle, SCRAM).

## 📋 Table des Matières
- [Fonctionnalités](#-fonctionnalités)
- [Modélisation Physique](#-modélisation-physique)
- [Installation](#-installation)
- [Utilisation](#-utilisation)
- [Structure du Projet](#-structure-du-projet)
- [Auteurs](#-auteurs)

## ✨ Fonctionnalités

### 1. Simulation Neutronique (Monte-Carlo)
* Simulation individuelle d'agents **Neutrons** sur une grille 2D.
* Gestion des interactions probabilistes : **Fission**, **Absorption**, **Diffusion**.
* Modélisation de différents matériaux modérateurs (Eau légère, Eau lourde, Graphite) influençant les sections efficaces.
* Cycle de vie des neutrons (Rapides $\to$ Épithermiques $\to$ Thermiques).

### 2. Thermohydraulique
* Calcul de la **Puissance Thermique** (MW) basée sur le nombre de fissions.
* Calcul de la **Température du Cœur** (K) via le bilan énergétique et la **Loi de Refroidissement de Newton**.
    * *Équation :* $C \frac{dT}{dt} = P_{fission} - h(T - T_{eau})$

### 3. Contrôle-Commande (Pilotage)
* **Régulateur PI (Proportionnel-Intégral) :** Ajuste automatiquement la position des barres de contrôle pour maintenir la puissance de consigne.
* **Système de Sécurité (SCRAM) :** Arrêt d'urgence automatique (chute des barres) en cas de dépassement de seuil critique.
* **Interlocks :** Sécurités logiques empêchant les mouvements de barres dangereux (ex: retrait de barre si $T > 1550K$).

### 4. Analyse de Données
* Visualisation en temps réel dans le terminal (librairie `rich`).
* **Export Automatique :** Génération de fichiers CSV horodatés pour post-traitement (RStudio/Excel) :
    * Historique global (Puissance, Température, Position des barres).
    * Trajectoires des neutrons.
    * Statistiques de fission (Distribution de Poisson).

## 🚀 Installation

1.  **Cloner le dépôt :**
    ```bash
    git clone [https://github.com/votre-nom/projet-simulation-nucleaire.git](https://github.com/votre-nom/projet-simulation-nucleaire.git)
    cd projet-simulation-nucleaire
    ```

2.  **Créer un environnement virtuel (recommandé) :**
    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # Mac/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Installer les dépendances :**
    ```bash
    pip install numpy pandas rich matplotlib
    ```

## 🎮 Utilisation

Pour lancer une simulation avec les paramètres par défaut :

```bash
python src/main.py
```

Configuration

Tous les paramètres sont modifiables dans le dictionnaire config du fichier src/main.py

```Python

config = {
    'n_initial': 200,       # Neutrons at startup
    'l': 1.1,               # Multiplication factor (k)
    'moderator': 'heavy_water', 
    'rod_active': True,     # Enable control bars
    'scram_threshold': 1.5, # Emergency stop threshold (150% P_nom)
    # ...
}
```
## 📂 Structure du Projet

 ```bash
.

├── src/

│   ├── main.py           # Entry Point and Configuration

│   ├── ReactorV2.py      # Core of the simulation (Logic, PID, Physics)

│   ├── Neutron.py        # Neutron Agent Class

│   ├── controlRod.py     # Agent Class Control Bar

│   └── utils.py          # Utility functions (CSV export, Maths)

├── statistics/           # Data output folder

└── README.md             # Documentation
```

Résultats
À la fin de la simulation, un dossier est créé dans statistics/ :

```bash
statistics/

└── 2023_10_27_14_30_00/

    ├── settings_*.csv          # Configuration used
    
    ├── reactor_history_*.csv   # Time data (for plotting curves)
    
    └── fission_stats_*.csv     # Statistics of the Poisson distribution
```

## 👥 Auteurs
Ce projet a été réalisé dans le cadre du M1 IMA/RO en UE Simulation aléatoire :

-  PIGEON Axel
-  SANFILIPPO Marco
-  FRANCINE-HABAS Mathis
