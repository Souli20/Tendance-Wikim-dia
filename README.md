# Analyse des tendances Wikimédia en temps réel — Wikimedia Pulse

Projet Big Data qui collecte les événements du flux Wikimedia, les publie dans Kafka, les traite avec Spark Structured Streaming, stocke les événements et agrégations dans MongoDB et les présente dans un dashboard Streamlit. Les services sont orchestrés par Docker Compose.

## Architecture

```text
Wikimedia EventStreams -> producteur Python -> Kafka (wiki-changes)
                                               |              |
                                               v              v
                                    consommateur Python   Spark Streaming
                                               |              |
                                               v              v
                                     MongoDB events_raw  MongoDB trends_per_minute
                                                              |
                                                              v
                                                       Dashboard Streamlit
```

## Prérequis

- Windows 10/11 : Docker Desktop avec moteur Linux et backend WSL 2; Git recommandé.
- Linux Ubuntu : Docker Engine et Docker Compose v2.
- Internet pour télécharger les images/dépendances et recevoir le flux Wikimedia.
- Configuration recommandée : 16 Go de RAM et au moins 15 Go d’espace disque libre. Si la machine est moins puissante, fermer les applications non essentielles.
- Installer séparément Python, Java, Kafka, Spark ou MongoDB sur l’hôte n’est pas nécessaire : ils fonctionnent dans les conteneurs.

## Cloner le dépôt sur une autre machine

Dans un terminal, à l’emplacement où le projet doit être installé :

```bash
git clone https://github.com/Souli20/Tendance-Wikim-dia.git Projet_Big_Data_Nouveau
cd Projet_Big_Data_Nouveau
docker compose config -q
```

Si l’adresse du dépôt change, copier l’URL de clonage affichée sur GitHub. La commande de validation doit se terminer sans erreur.

## Première installation sous Windows 10/11

1. Installer WSL 2 depuis PowerShell administrateur si nécessaire :

   ```powershell
   wsl --install
   ```

   Redémarrer si Windows le demande.
2. Installer Docker Desktop, activer le moteur WSL 2 et l’intégration de la distribution Ubuntu utilisée.
3. Dans Docker Desktop > Settings > General, activer **Start Docker Desktop when you sign in to your computer** (le libellé peut varier).
4. Démarrer Docker Desktop et attendre que son moteur soit prêt.
5. Dans PowerShell, se placer dans le dossier du projet, puis construire les images et démarrer :

   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\start.ps1 -Build
   ```

   Pour les démarrages suivants, exécuter `powershell -ExecutionPolicy Bypass -File scripts\start.ps1`.

Pour utiliser le terminal Ubuntu/WSL, naviguer jusqu’au dossier réel du projet (exemple à adapter) :

```bash
cd "/mnt/c/Users/$USER/Desktop/Projet_Big_Data_Nouveau"
bash scripts/start.sh --build
```

Sur WSL, les chemins Windows contenant des espaces doivent être entourés de guillemets. Le premier build peut prendre plusieurs minutes.

## Première installation sous Ubuntu Linux natif

Installer Docker Engine et le plugin Compose v2 en suivant la documentation officielle Docker correspondant à la version d’Ubuntu. Vérifier l’installation :

```bash
docker --version
docker compose version
docker run --rm hello-world
```

Pour utiliser Docker sans `sudo`, ajouter l’utilisateur au groupe `docker`, puis fermer et rouvrir la session :

```bash
sudo usermod -aG docker "$USER"
```

Depuis le dossier du projet :

```bash
bash scripts/start.sh --build
```

Pour les démarrages suivants : `bash scripts/start.sh`.

## Lancer, ouvrir et arrêter

### Démarrer sous Windows

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start.ps1
```

Reconstruction des images après une modification de code/Dockerfile :

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start.ps1 -Build
```

Démarrer et ouvrir le dashboard automatiquement :

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start.ps1 -OpenDashboard
```

### Démarrer sous Linux ou WSL

```bash
bash scripts/start.sh
```

Avec reconstruction : `bash scripts/start.sh --build`. Pour tenter d’ouvrir le navigateur depuis l’environnement courant : `bash scripts/start.sh --open`.

### Arrêter

Windows PowerShell :

```powershell
powershell -ExecutionPolicy Bypass -File scripts\stop.ps1
```

Linux/WSL :

```bash
bash scripts/stop.sh
```

L’arrêt utilise `docker compose stop` : il arrête les conteneurs mais conserve les volumes et les données persistantes. **Ne pas exécuter `docker compose down -v` si les données doivent être conservées.**

## Démarrage automatique à la prochaine connexion Windows

Le démarrage automatique nécessite que Docker Desktop se lance lui-même à l’ouverture de session. Ensuite, une tâche planifiée peut lancer le projet et ouvrir le dashboard.

1. Activer le démarrage de Docker Desktop à la connexion (voir la section Windows).
2. Dans PowerShell, depuis le dossier du projet, exécuter :

   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\install_autostart.ps1
   ```
3. À la prochaine ouverture de session Windows, la tâche `WikimediaPulse-Start` attend environ une minute, attend la disponibilité de Docker via le script, démarre Compose et ouvre le dashboard.
4. Tester sans redémarrer Windows :

   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\start.ps1 -OpenDashboard
   ```
5. Pour désactiver le démarrage automatique :

   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\uninstall_autostart.ps1
   ```

Cette tâche n’allume pas un PC éteint et ne réveille pas nécessairement un PC en veille. Si Docker Desktop n’est pas prêt, consulter le Planificateur de tâches et relancer le script manuellement.

## Adresses et ports — configuration actuelle

| Composant | Adresse depuis l’hôte |
|---|---|
| Dashboard Streamlit | http://localhost:8502 |
| UI Spark (si active) | http://localhost:4041 |
| MongoDB | `localhost:27018` |
| Kafka | `localhost:29094` |

Entre conteneurs, utiliser les noms DNS Compose et les ports internes, par exemple `kafka:9092` et `mongo:27017`. Les ports hôtes peuvent être différents selon la configuration de `docker-compose.yml`; si elle change, mettre à jour ce tableau.

## Vérifier l’état et consulter les journaux

```bash
docker compose ps
docker compose logs --tail=100 producer
docker compose logs --tail=100 consumer
docker compose logs --tail=100 spark
docker compose logs --tail=100 dashboard
```

Compter les documents MongoDB :

```bash
docker compose exec mongo mongosh wiki_db --quiet --eval 'db.events_raw.countDocuments()'
docker compose exec mongo mongosh wiki_db --quiet --eval 'db.trends_per_minute.countDocuments()'
```

Les premières visualisations agrégées ne s’affichent qu’après le démarrage du job Spark et l’arrivée de données traitées. Si la page Streamlit s’ouvre mais que les graphiques sont vides, examiner les journaux Spark et le compteur `trends_per_minute`.

## Dépannage

| Symptôme | Vérification / solution |
|---|---|
| `Cannot connect to the Docker daemon` | Démarrer Docker Desktop/Engine, attendre que le moteur soit prêt, puis relancer le script. |
| `localhost:8502` ne répond pas | `docker compose ps`, puis `docker compose logs --tail=100 dashboard`. Vérifier le mapping de port dans `docker-compose.yml`. |
| Dashboard vide | Vérifier que Spark tourne et lire `docker compose logs --tail=200 spark`; vérifier le nombre d’agrégats MongoDB. |
| Spark s’arrête ou redémarre | Lire les journaux Spark et rechercher une erreur de connecteur Kafka, de réseau ou d’écriture MongoDB. |
| `port is already allocated` | Identifier le processus utilisant le port, l’arrêter si approprié ou modifier le port hôte à gauche de `:` dans `docker-compose.yml`. |
| Premier démarrage très long | Les images et dépendances doivent être téléchargées. Garder Internet actif et attendre la fin du build. |
| Démarrage automatique sans effet | Vérifier Docker Desktop au démarrage, puis le Planificateur de tâches Windows et la tâche `WikimediaPulse-Start`. |

## Publier les changements sur GitHub

### 1. Vérifier le dépôt et les changements

```bash
git remote -v
git branch --show-current
git status --short
```

Confirmer que le remote correspond bien au dépôt de l’équipe et que les fichiers modifiés sont ceux attendus.

### 2. Vérifier les secrets et les données

Ne jamais publier `.env`, mots de passe, clés API, jetons, journaux volumineux, fichiers de données ni volumes MongoDB/Kafka. Ajouter `.env` au `.gitignore` si le projet en utilise un. Un `.env.example` ne doit contenir que des valeurs fictives. Si `.env` a déjà été suivi par Git, `git rm --cached .env` le retire de l’index sans effacer la copie locale, mais ne l’efface pas de l’historique passé.

### 3. Examiner, committer et pousser

```bash
git diff
git status
# Ajouter explicitement les fichiers validés
git add README.md scripts/
git diff --cached
git commit -m "Add startup scripts and deployment documentation"
git push
```

Si le dépôt n’a pas de branche distante configurée, vérifier le nom de la branche avec `git branch --show-current` et consulter `git push --help`; ne pas supposer que la branche s’appelle `main`.

### 4. Récupérer les changements sur une autre machine

```bash
git pull
```

Puis lancer le script adapté au système. Git partage le code et la documentation, pas les volumes Docker : les données MongoDB/Kafka restent locales à chaque machine.

## Bonnes pratiques

- Versionner les scripts, Dockerfiles, `docker-compose.yml`, documentation et fichiers d’exemple.
- Ne jamais versionner les secrets, les volumes de base de données ou des exports de données inutiles.
- Utiliser les scripts d’arrêt pour une pause et préserver les données.
- Après modification du code ou d’un Dockerfile, utiliser l’option `--build`.
- Le démarrage automatique fonctionne seulement si le PC est allumé, la session Windows est ouverte et Docker Desktop démarre correctement.
