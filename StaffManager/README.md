# StaffManager

Application pédagogique de gestion des employés avec authentification et rôles.

## Prérequis
- Docker Desktop
- Docker Compose (inclus dans Docker Desktop)

## Démarrage sous Windows PowerShell

1. Copier `.env.example` vers `.env` :
   ```powershell
   Copy-Item .env.example .env
   ```
2. Modifier `.env` et définir une vraie clé secrète ainsi qu'un mot de passe administrateur fort (12 caractères minimum).
3. Construire et démarrer :
   ```powershell
   docker compose up --build
   ```
4. Ouvrir http://localhost:5000

Les identifiants administrateur sont ceux définis dans `.env`.

## Arrêter
```powershell
docker compose down
```

Les données SQLite sont conservées dans le volume Docker `staffmanager_data`.
Pour supprimer aussi les données (ATTENTION : suppression définitive) :
```powershell
docker compose down -v
```

## Rôles
- `admin` : accès au tableau de bord, employés et création de comptes.
- `hr` : accès au tableau de bord et à la gestion des employés.
- `employee` : accès au tableau de bord et à son profil.

## Limites connues du prototype
- Le compte créé par l'administrateur n'est pas encore associé automatiquement à une fiche employé.
- Pas encore de procédure de réinitialisation de mot de passe, de limitation des tentatives de connexion ni de journal d'audit.
- Pour une mise en production, utiliser HTTPS, `COOKIE_SECURE=true`, une base de données adaptée et une gestion de secrets dédiée.
- La création de compte ne remplace pas un processus complet d'administration RH.

## Première étape DevSecOps
Après validation du fonctionnement local, ajouter progressivement les tests Pytest, Bandit, pip-audit, Gitleaks et Trivy dans la pipeline CI/CD.
