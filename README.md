# Viral Digitale Academy — Site Python bilingue

Site web complet en **Python pur** (aucune bibliothèque externe obligatoire) avec :

- Français + العربية (choix depuis le menu)
- Support RTL automatique en arabe
- Accueil
- Formation
- Programme 6 mois
- Projets
- À propos
- Contact
- Pré-inscription
- Espace admin
- Export CSV des inscriptions et messages

## Lancer le site sous Windows

Ouvrez PowerShell dans le dossier `viral_digitale_academy`, puis :

```powershell
python app.py
```

Ou double-cliquez sur `start.bat`.

Ensuite ouvrez :

```text
http://127.0.0.1:8000
```

## Langues

Le visiteur peut cliquer sur **FR** ou **العربية** dans le menu. Le choix est mémorisé dans le navigateur.

## Administration

```text
http://127.0.0.1:8000/admin
```

Mot de passe par défaut :

```text
viral2026
```

Pour un déploiement public, changez le mot de passe admin et la clé secrète avec les variables d'environnement `ADMIN_PASSWORD` et `SECRET_KEY`.
