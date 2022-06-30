# Grande Echelle

Version avec PyTorch, sans Coral

### Merci à
* [Ross Wightman](https://github.com/rwightman)
* [ rwightman posenet-pytorch](https://github.com/rwightman/posenet-pytorch)
pour la conversion du modèle PoseNet

### Le film n'est pas dans ce dépôt
Il est disponible à ????

### Installation
Testée avec Ubuntu Mate 20.04

Les packages python sont installés dans un virtualenv parce que c'est facile, ça marche bien, c'est la bonne façon de procéder.

#### RealSense D 455
``` bash
sudo apt-key adv --keyserver keys.gnupg.net --recv-key F6E65AC044F831AC80A06380C8B3A55A6F3EFCDE || sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-key F6E65AC044F831AC80A06380C8B3A55A6F3EFCDE
sudo apt install software-properties-common
sudo add-apt-repository "deb https://librealsense.intel.com/Debian/apt-repo focal main" -u
sudo apt install librealsense2-dkms librealsense2 librealsense2-utils
```

librealsense2-utils non instalable
The following packages have unmet dependencies:
 librealsense2-utils : Depends: libssl1.1 (>= 1.1.1) but it is not installable
E: Unable to correct problems, you have held broken packages.



#### Python
Installe tous les packages nécessaires dans un dossier /mon_env dans le dossier /grande_echelle
``` bash
# Mise à jour de pip
sudo apt install python3-pip
python3 -m pip install --upgrade pip
# Installation de venv
sudo apt install python3-venv

# Installation de l'environnement
cd /le/dossier/de/grande_echelle/
# Création du dossier environnement si pas encore créé, l'argument --system-site-packages permet d'utiliser les packages système où est pycoral
python3 -m venv mon_env
# Activation
source mon_env/bin/activate
# Installation des packages, numpy, opencv-python, pyrealsense2, kivy, ...
python3 -m pip install -r requirements.txt
```

#### Bug dans Kivy
``` bash
sudo apt install xclip
```


### Excécution
Copier coller le lanceur grande-echelle.desktop sur le Bureau

Il faut le modifier avec Propriétés: adapter le chemin à votre cas.

Ce lanceur lance un terminal et l'interface graphique,
et il permet aussi de créer une application au démarrage.


#### Utilisation
* Bascule full_screen en cours en activant la fenêtre à aggrandir puis:
    * espace
* Options permet de modifier tous les paramètres mais il faut relancer l'application pour les paramètres non modifiables à chaud
* En mode expo, démarrage directement en full screen sur le film, pas d'info, pas d'image de capture

#### Explications sur les  paramètres

* brightness et contrast: régler au centre de la plage de bonne détection
* threshold = 80 seuil de confiance de la détection, plus c'est grand moins il y a d'erreur, mais plus la détection est difficile.
* around = 1 nombre de pixels autour de la détection pour calcul moyenné de la profondeur, 1 à 3 mais ne change rien
* frame_rate_du_film = 50, ne pas le modifier
* film = 'ICOS.mp4' 1920x1080, 25 fps!
* pile_size = 80 lissage de la profondeur
* profondeur_mini = 1200, cale le 0 de la profondeur
* profondeur_maxi = 4000, limite le maxi
* largeur_maxi = 1500, limite la plage des x


### Version sans Coral et avec PyTorch et Cuda

Nécéssite une carte graphique NVidia un peu patate.

#### Installation sur Xubuntu 22.04

#### Installation de CUDA

#### Installation du driver propriétaire NVidia
 Settings/Additionnal Drivers: installer le driver 515






### LICENSE

#### Apache License, Version 2.0

* pose_engine.py
* posenet_histopocene.py
* pyrealsense2

#### Licence GPL v3

* tous les autres fichiers

#### Creative Commons

[Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International Public License](http://oer2go.org/mods/en-boundless/creativecommons.org/licenses/by-nc-nd/4.0/legalcode.html)
