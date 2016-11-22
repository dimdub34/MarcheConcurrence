Ce programme correspond au projet de Beaud, Rosaz & Willinger (2016) sur les effets de 
la taxation sur un marché d'échanges de biens.  

C'est un programme qui fonctionne avec [le2m-v2.1](https://github.com/dimdub34/le2m-v2.1)

## Chargement du programme
* Lancer le serveur LE2M (serverrun.py)
* Fichier / Charger une partie puis sélectionner MarcheConcurrence
* Si c'est une session de test laisser la case "Test" cochée, sinon la décocher
* Choisir le dossier dans lequel enregistrer la base de données. Par défaut 
la base est enregistrée dans le dossier du programme. Il faudra toujours 
utiliser ce dossier afin que les données aillent toujours dans la même base
* Le nom de fichier (data.sqlite) peut être changé si besoin mais il est 
conseillé de le laisser inchangé
* Connecter les clients (clientrun.py)

### Remarque  
Une autre possibilité est de préparer un batch du type:
C:\Python27\python.exe C:\temp\le2m-v2.1\le2m\serverrun.py -e MarcheConcurrence -db c:\temp --no-test

où  
* C:\temp est l'endroit où se situe le2m-v2.1. Changer ce chemin s'il est ailleurs
* c:\temp est l'endroit où on veut stocker la base de données. Pareil, changer ce chemin si stockage ailleurs
* --no-test signifie que ce n'est pas un test. Enlever cet argument si c'est un test

Ainsi il suffit de double-cliquer sur le batch pour lancer le serveur et directement 
charger la partie MarcheConcurrence 

## Configuration de l'expérience: A FAIRE AU DEBUT DE CHAQUE PARTIE
* Menu Partie / Marché Concurrence, cliquer sur Configurer
* Définir le traitement et les autres paramètres puis cliquer sur Ok
* Penser qu'au lancement de la seconde partie il n'y a pas de période d'essai

## Afficher l'écran d'accueil
* Menu Expérience / Afficher l'accueil

## Démarrage de la partie
* Menu Partie / Marché Concurrence / Démarrer

## Lorsque la partie est terminée
* s'il s'agit de la première partie, distribuer les instructions de la seconde partie, configurer la seconde partie (traitement, période d'essai) ... i.e. repartir sur "Configuration de l'expérience" 
ci-dessus
* s'il s'agit de la seconde partie, lancer le questionnaire final: Menu Expérience / Afficher le questionnaire final sur les postes

## Après le questionnaire final
* Menu Parties / Marché - Concurrence / Afficher les gains sur les postes: cela informe les sujets de la période 
rémunérée à chacune des deux parties et de leur gain respectif.
* Lorsque tous les sujets ont cliqué sur le bouton Ok, cliquer sur Experience / Gains puis sur Imprimer puis après sur Afficher sur les postes clients.
Sur cet écran les sujets sont informés de leur gain pour l'expérience et ont à disposition une zone pour écrire des commentaires
