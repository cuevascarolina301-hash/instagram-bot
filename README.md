# Robot Instagram — @carolina.cuevas.libros

Ce dossier contient un **robot** qui fabrique **123 Reels** (environ 31 jours) puis **les publie tout seul, 4 fois par jour**. C'est gratuit et ton ordinateur n'a pas besoin d'être allumé.

Tu installes une fois (environ 1 heure, dont 15 minutes où tu attends), ensuite tu n'as plus rien à faire.

---

## Le principe, en une phrase

GitHub, un site gratuit, fabrique tes vidéos, les garde, et réveille le robot 4 fois par jour. Le robot prend la vidéo suivante et la donne à Instagram.

---

## ÉTAPE 1 — Préparer Instagram (5 min, sur ton téléphone)

1. Ouvre Instagram sur le compte **carolina.cuevas.libros**.
2. Va sur ton profil, touche les **3 traits** en haut à droite.
3. Va dans **Type de compte et outils**, puis **Passer à un compte professionnel**, choisis **Créateur** et suis jusqu'au bout.
4. Retourne sur ton profil et touche **Modifier le profil**.
5. Dans **Liens**, remplace le lien par exactement :
   `https://www.amazon.com/dp/B0HJ564B3W`
6. Ouvre chacun des 8 anciens posts, touche les **3 points**, puis **Archiver**. Ne les supprime pas.

✅ Fini quand ton profil est vide et que le lien Amazon fonctionne quand tu cliques dessus.

---

## ÉTAPE 2 — Créer ton compte GitHub (5 min, sur l'ordinateur)

1. Va sur **github.com** et clique sur **Sign up**.
2. Utilise une adresse e-mail réservée à Carolina Cuevas, pas ton e-mail personnel. Tes vidéos seront publiques sur GitHub et le nom du compte se voit.
3. Choisis un nom simple, par exemple `carolinacuevaslibros`. Note-le : on l'appelle **TON-NOM** dans la suite.

✅ Fini quand tu es connecté sur github.com.

---

## ÉTAPE 3 — Envoyer ce dossier sur GitHub (10 min)

1. Télécharge et installe **GitHub Desktop** : desktop.github.com
2. Ouvre-le et connecte-toi avec le compte de l'étape 2.
3. Dézippe `instagram-bot.zip`. Tu obtiens un dossier **instagram-bot**.
4. Dans GitHub Desktop : menu **File**, puis **Add local repository**, puis choisis le dossier **instagram-bot**.
5. Il affiche « This directory does not appear to be a Git repository ». Clique sur le lien bleu **create a repository**, puis sur le bouton **Create repository**.
6. Clique en haut sur **Publish repository**.
7. ⚠️ **Décoche** la case **Keep this code private**. Le dossier doit être public pour qu'Instagram puisse lire les vidéos.
8. Clique sur **Publish repository** et attends quelques secondes.

✅ Fini quand tu vois tes fichiers sur `github.com/TON-NOM/instagram-bot`.

---

## ÉTAPE 4 — Fabriquer les Reels (2 min + 15 min d'attente)

1. Sur `github.com/TON-NOM/instagram-bot`, clique sur l'onglet **Actions** (en haut).
2. S'il affiche un message pour activer les workflows, clique sur le bouton vert pour accepter.
3. À gauche, clique sur **Fabricar los Reels**, puis à droite sur **Run workflow**, puis sur le bouton vert **Run workflow**.
4. Une ligne apparaît avec un rond jaune qui tourne. Attends environ 15 minutes qu'il devienne une **coche verte ✅**. Tu peux faire l'étape 6 pendant ce temps.

✅ Fini quand la coche est verte et qu'un dossier **posts** rempli de vidéos est apparu dans ton dépôt.

---

## ÉTAPE 5 — Mettre les vidéos en ligne (3 min)

1. Dans ton dépôt, clique sur **Settings** (la roue dentée en haut).
2. Dans le menu de gauche, clique sur **Pages**.
3. Sous **Branch**, choisis **main**, laisse **/ (root)**, puis clique sur **Save**.
4. Attends 2 minutes, puis ouvre dans ton navigateur :
   `https://TON-NOM.github.io/instagram-bot/posts/0001.mp4`

✅ Fini quand la vidéo de la première phrase se lance dans le navigateur.

---

## ÉTAPE 6 — Obtenir la clé Instagram (15 min, la seule étape un peu longue)

Cette « clé » (un jeton) permet au robot de publier sur ton compte. Tu la crées chez Meta, la société d'Instagram.

1. Va sur **developers.facebook.com** et connecte-toi avec Facebook.
   La première fois, il te demande de t'enregistrer comme développeur : accepte et réponds aux questions.
2. Clique sur **Mes apps**, puis **Créer une app**.
3. Nom de l'app : `Carolina Reels`. Clique sur **Suivant**.
4. À l'écran des cas d'usage, choisis **Gérer les messages et le contenu sur Instagram**, puis continue jusqu'à **Créer l'app**.
5. Dans l'app, ouvre **Configuration de l'API avec connexion Instagram** (en anglais : *API setup with Instagram login*).
6. Dans la partie **Générer des tokens d'accès**, clique sur **Ajouter un compte**, connecte-toi avec **carolina.cuevas.libros** et accepte tout.
7. Une fois le compte ajouté, clique sur **Générer un token** à côté de lui. Une longue suite de lettres et de chiffres apparaît : c'est la clé.
8. Copie-la dans un fichier texte provisoire. Ne la montre à personne.

Si Meta te dit que le compte doit accepter une invitation : dans Instagram, va dans **Paramètres → Applications et sites web → Invitations de testeur**, puis **Accepter**, et recommence le point 6.

Les menus de Meta changent parfois de nom. L'idée reste toujours la même : produit Instagram, puis connexion Instagram, puis générer un token.

✅ Fini quand tu as la longue clé copiée.

---

## ÉTAPE 7 — Donner les clés au robot (5 min)

**A. La clé Instagram**
1. Sur `github.com/TON-NOM/instagram-bot`, va dans **Settings**.
2. À gauche, ouvre **Secrets and variables**, puis **Actions**.
3. Clique sur **New repository secret**.
4. Name : `IG_TOKEN`. Secret : colle la clé de l'étape 6. Clique sur **Add secret**.

**B. La clé qui permet au robot de prolonger la clé Instagram tout seul**
La clé Instagram expire au bout de 60 jours. Le robot la prolonge chaque lundi, mais il a besoin de cette deuxième clé pour ça.
1. Clique sur ta photo en haut à droite, puis **Settings**.
2. Tout en bas à gauche : **Developer settings**, puis **Personal access tokens**, puis **Fine-grained tokens**.
3. Clique sur **Generate new token**.
4. Token name : `robot`. Expiration : choisis la plus longue proposée et **note la date dans ton agenda**.
5. Repository access : **Only select repositories**, puis choisis **instagram-bot**.
6. Permissions : clique sur **Add permissions**, coche **Secrets**, puis mets **Read and write**.
7. Clique sur **Generate token** et copie la clé (elle commence par `github_pat_`).
8. Retourne dans ton dépôt, puis **Settings**, **Secrets and variables**, **Actions**, **New repository secret**.
   Name : `GH_PAT`. Secret : colle la clé. Clique sur **Add secret**.

✅ Fini quand tu vois deux secrets dans la liste : `IG_TOKEN` et `GH_PAT`.

---

## ÉTAPE 8 — Tester, puis lancer (5 min)

1. Dans ton dépôt, clique sur l'onglet **Actions**.
2. À gauche, clique sur **Publicar en Instagram**, puis à droite sur **Run workflow**.
   Laisse **1** dans la case, puis clique sur le bouton vert **Run workflow**. C'est un essai, rien n'est publié.
3. Attends que le rond devienne une **coche verte ✅** (environ 30 secondes).
4. Recommence le point 2, mais **remplace 1 par 0**. Cette fois c'est pour de vrai.
5. Attends 1 à 3 minutes : ton premier Reel apparaît sur Instagram.
6. À gauche, clique sur **Renovar token de Instagram**, puis **Run workflow**. Il doit finir en ✅.

✅ **C'est fini.** Le robot publie seul à 8h07, 12h07, 17h07 et 21h07, heure de Chicago.

---

## BONUS — Ajouter de la musique (facultatif, 10 min)

Le robot ne peut pas ajouter les musiques à la mode d'Instagram : l'outil officiel ne le permet pas. Par défaut, les Reels sont silencieux. Tu peux leur ajouter des musiques libres de droits :

1. Va sur **pixabay.com/music**, cherche par exemple « calm piano » ou « soft acoustic ».
2. Télécharge **3 à 5 musiques douces** en MP3. La licence Pixabay permet de les utiliser sans citer l'auteur.
3. Mets-les dans le dossier **musica** à l'intérieur de **instagram-bot** sur ton ordinateur.
4. Dans GitHub Desktop : écris un petit mot en bas à gauche (par exemple « musique »), clique sur **Commit to main**, puis en haut sur **Push origin**.

Le robot ajoute alors la musique à tous les Reels pas encore publiés, en alternant les morceaux. Ça prend environ 5 minutes et ça se voit dans l'onglet **Actions**.

---

## Au quotidien

| Situation | Ce qui se passe / ce que tu fais |
|---|---|
| Une publication rate | GitHub t'envoie un e-mail. Le Reel repart au créneau suivant, rien à faire. Si ça rate 3 fois de suite, ouvre l'onglet **Actions** et clique sur la ligne rouge : la raison est écrite. |
| Mettre en pause | **Actions**, puis **Publicar en Instagram**, puis **⋯** (en haut à droite), puis **Disable workflow**. Même chemin et **Enable** pour relancer. |
| Il reste moins de 3 jours de Reels | Un avertissement jaune apparaît dans **Actions**. Quand il n'y a plus rien, l'Action échoue et tu reçois un e-mail. Demande-moi le lot suivant. |
| Retirer un Reel avant sa publication | Dans GitHub, ouvre `cola.json`, clique sur le crayon ✏️, supprime son bloc `{ ... }`, puis **Commit changes**. |
| La clé `GH_PAT` arrive à expiration | Refais l'étape 7B (à la date notée dans ton agenda). |

Le robot vérifie avant chaque publication qu'il n'a pas déjà publié le même Reel, donc pas de doublon possible.

---

## Pour les curieux : ce qu'il y a dans le dossier

- `posts/` : les 123 Reels (1080×1920, 7 à 14 secondes), créés à l'étape 4.
- `cola.json` : la liste d'attente, avec chaque légende et la date de publication une fois publiée.
- `publicar.py` : publie le Reel suivant.
- `poner_musica.py` : ajoute la musique du dossier `musica`.
- `.github/workflows/` : les réveils automatiques (fabrication, publication, renouvellement de la clé, musique).
- `fabrica/` : la machine à fabriquer de nouveaux Reels et la banque de phrases.
