# MySQL DBA Assistant

## Description
MySQL DBA Assistant est une application de bureau développée en Python qui fournit une interface graphique conviviale pour interagir avec les bases de données MySQL. Elle offre diverses fonctionnalités pour faciliter la gestion et l'analyse des bases de données MySQL.

## Fonctionnalités principales
- Connexion à des bases de données MySQL
- Affichage et navigation dans les tables de la base de données
- Exécution de requêtes SQL personnalisées
- Visualisation des résultats des requêtes dans un tableau
- Exportation des résultats au format Excel
- Filtrage et tri des tables
- Historique des commandes exécutées
- Aperçu de la structure de la base de données
- Assistant IA pour l'aide à la rédaction de requêtes SQL

## Prérequis
- Python 3.x
- Bibliothèques Python : 
  - customtkinter
  - mysql-connector-python
  - requests
  - openpyxl

## Installation
1. Clonez ce dépôt sur votre machine locale.
2. Installez les dépendances nécessaires :
   ```
   pip install customtkinter mysql-connector-python requests openpyxl
   ```

## Utilisation
1. Lancez l'application en exécutant le script principal :
   ```
   python main.py
   ```
2. Utilisez le bouton "Connexion" dans la barre latérale pour vous connecter à votre base de données MySQL.
3. Une fois connecté, vous pouvez naviguer dans les tables, exécuter des requêtes et utiliser les différentes fonctionnalités de l'interface.


## Fonctionnalités détaillées
- **Connexion à la base de données** : Permet de se connecter à une base de données MySQL en spécifiant l'hôte, l'utilisateur, le mot de passe et le nom de la base de données.
- **Affichage des tables** : Liste toutes les tables de la base de données connectée.
- **Exécution de requêtes** : Permet d'exécuter des requêtes SQL personnalisées et d'afficher les résultats.
- **Pagination** : Navigation dans les résultats de requêtes volumineuses.
- **Filtrage et tri** : Possibilité de filtrer et trier les tables et les résultats.
- **Historique des commandes** : Garde une trace des commandes SQL exécutées.
- **Aperçu de la base de données** : Fournit une vue d'ensemble de la structure de la base de données.
- **Assistant IA** : Aide à la rédaction de requêtes SQL complexes.

## Contribution
Les contributions à ce projet sont les bienvenues. N'hésitez pas à ouvrir une issue ou à soumettre une pull request pour proposer des améliorations ou corriger des bugs.

## Licence
...
