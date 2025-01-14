
"""
Interface graphique pour Grande Echelle
"""


from time import time, sleep
from pathlib import Path
from multiprocessing import Process, Pipe
from threading import Thread
import json
import gzip
from datetime import datetime

import kivy
kivy.require('2.0.0')

from kivy.core.window import Window

k = 1
WS = (int(720*k), int(720*k))
Window.size = WS


from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.clock import Clock

from posenet_realsense import posenet_realsense_run
from grande_echelle import grande_echelle_run
from utils import MyTools



class BigData:
    """Enregistrement toutes les heures de toutes les depth, et sur quit.
    Enregistrement dans un dossier /grande_echelle_data/ dans le home
    40 ko pour 10 mn
    240 ko pour 1h
    3 mois de 6 jours de 6h / semaine = 6*3*30*240 = 130000 ko = 130 Mo
    1 dossier par jour, 1 fichier par heure
    12 semaines de 6 jours = 72 dossiers de 6 zip
    """

    def __init__(self):
        # Création du dosier dans le home
        self.mkdir_grande_echelle_data()

        # Le dossier des data dans le home, c'est un objet Path
        self.data_dir = Path.home() / 'grande_echelle_data'
        print(f"Dossier des datas: {self.data_dir} type {type(self.data_dir)}")

        # Le dossier du jour
        self.mkdir_dir_day()

        # Ce sera un objet Path
        self.dir_day = None
        self.mkdir_dir_day()

        # Référence pour enregistrement toutes les heures
        self.t_zero = time()

    def mkdir_grande_echelle_data(self):
        """Création du dossier ~/grande_echelle_data si non existant"""
        MyTools().mkdir_in_home('grande_echelle_data')

    def mkdir_dir_day(self):
        dt_now = datetime.now()
        dj = dt_now.strftime("%Y_%m_%d")
        dd = self.data_dir / dj
        print(f"Dossier du jour: {dd} type {type(dd)}")
        MyTools().mkdir(dd)
        self.dir_day = dd

    def do_save(self, data):

        dt_now = datetime.now()
        dt = dt_now.strftime("%Y_%m_%d_%H_%M")
        fichier = self.dir_day / f"cap_{dt}.zip"  # objet Path
        print(f"Enregistrement de: {fichier}")
        # fichier n'a pas besoin d'être converti en str()
        with gzip.open(fichier, 'w') as f_out:
            f_out.write(json.dumps(data).encode('utf-8'))

    def save_every_hours(self, datas):
        t = time()
        if t - self.t_zero > 3600:
            # Save
            self.do_save(datas)
            self.t_zero = t
            return True



class MainScreen(Screen):
    """Ecran principal, l'appli s'ouvre sur cet écran
    root est le parent de cette classe dans la section <MainScreen> du kv
    """

    # Attribut de class, obligatoire pour appeler root.titre dans kv
    titre = StringProperty("toto")
    enable = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Trop fort
        self.app = App.get_running_app()

        # Pour le Pipe
        self.p1_conn = None
        self.p2_conn = None
        self.kivy_receive_loop = 1

        # Pour ne lancer qu'une fois les processus
        self.enable = False

        self.titre = "Grande Echelle"

        Clock.schedule_once(self.set_run_on, 1.0)

        # Pour enregistrement en json
        self.bd = BigData()
        self.datas = []

        print("Initialisation du Screen MainScreen ok")

    def set_run_on(self, dt):
        """Start automatique"""
        self.ids.run.state = "down"
        self.run_grande_echelle()

    def kivy_receive_thread(self):
        t_kivy = Thread(target=self.kivy_receive)
        t_kivy.start()

    def kivy_receive(self):
        while self.kivy_receive_loop:
            sleep(0.01)

            # De posenet realsense
            if self.p1_conn is not None:
                if self.p1_conn.poll():
                    try:
                        data1 = self.p1_conn.recv()
                    except:
                        data1 = None

                    if data1 is not None:
                        # Relais des depth
                        if data1[0] == 'from_realsense':
                            self.p2_conn.send(['depth', data1[1]])
                            self.datas.append([time(), data1[1]])
                            done = self.bd.save_every_hours(self.datas)
                            if done:
                                print("Saved.")
                                self.datas = []

                        if data1[0] == 'quit':
                            print("\nQuit reçu dans Kivy de Posenet Realsense ")
                            # Fait le quit dans GrandeEchelle et PoseRealsense
                            # avec le quit envoyé par le Viewer
                            self.p2_conn.send(['quit', 1])
                            self.p1_conn.send(['quit', 1])
                            self.kivy_receive_loop = 0
                            self.app.do_quit()

            # De grande echelle
            if self.p2_conn is not None:
                if self.p2_conn.poll():
                    try:
                        data2 = self.p2_conn.recv()
                    except:
                        data2 = None

                    if data2 is not None:
                        if data2[0] == 'quit':
                            print("\nQuit reçu dans Kivy de Grande Echelle")
                            # Fait le quit dans GrandeEchelle et PoseRealsense
                            # avec le quit envoyé par le Viewer
                            self.p1_conn.send(['quit', 1])
                            self.p2_conn.send(['quit', 1])
                            self.kivy_receive_loop = 0
                            self.app.do_quit()

    def run_grande_echelle(self):
        if not self.enable:
            print("Lancement de 2 processus:")

            current_dir = str(Path(__file__).parent.absolute())
            print("Dossier courrant:", current_dir)

            # Posenet et Realsense
            self.p1_conn, child_conn1 = Pipe()
            self.p1 = Process(target=posenet_realsense_run, args=(child_conn1,
                                                             current_dir,
                                                             self.app.config, ))
            self.p1.start()
            print("Posenet Realsense lancé ...")

            # Grande Echelle
            self.p2_conn, child_conn2 = Pipe()
            self.p2 = Process(target=grande_echelle_run, args=(child_conn2,
                                                          current_dir,
                                                          self.app.config, ))
            self.p2.start()
            print("Histopocene lancé ...")

            self.enable = True
            self.kivy_receive_thread()
            print("Ca tourne ...")



class Reglage(Screen):

    threshold_pose = NumericProperty(0.8)
    threshold_points = NumericProperty(0.8)
    profondeur_mini = NumericProperty(1500)
    profondeur_maxi = NumericProperty(4000)
    largeur_maxi = NumericProperty(500)
    pile_size = NumericProperty(12)
    lissage = NumericProperty(11)
    d_mode = NumericProperty(0)
    info = NumericProperty(0)
    mode_expo = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print("Initialisation du Screen Settings")

        self.app = App.get_running_app()

        self.threshold_pose = float(self.app.config.get('pose', 'threshold_pose'))
        self.threshold_points = float(self.app.config.get('pose', 'threshold_points'))
        self.profondeur_mini = int(self.app.config.get('histopocene',
                                                    'profondeur_mini'))
        self.profondeur_maxi = int(self.app.config.get('histopocene',
                                                    'profondeur_maxi'))
        self.largeur_maxi = int(self.app.config.get('histopocene',
                                                    'largeur_maxi'))
        self.pile_size = int(self.app.config.get('histopocene', 'pile_size'))
        self.lissage = int(self.app.config.get('histopocene', 'lissage'))
        self.info = int(self.app.config.get('histopocene', 'info'))
        self.mode_expo = int(self.app.config.get('histopocene', 'mode_expo'))

        Clock.schedule_once(self.set_switch, 0.5)

    def set_switch(self, dt):
        """Les objets graphiques ne sont pas encore créé pendant le init,
        il faut lancer cette méthode plus tard
        le switch est setter à 1 si 1 dans la config
        """
        if self.mode_expo == 1:
            self.ids.mode_expo.active = 1
        if self.info == 1:
            self.ids.info.active = 1

    def do_slider(self, iD, instance, value):

        scr = self.app.screen_manager.get_screen('Main')

        if iD == 'threshold_pose':
            # Maj de l'attribut
            self.threshold_pose = round(value, 2)
            # Maj de la config
            self.app.config.set('pose', 'threshold_pose', self.threshold_pose)
            # Sauvegarde dans le *.ini
            self.app.config.write()

            # Envoi de la valeur au process enfant
            if scr.p1_conn:
                scr.p1_conn.send(['threshold_pose', self.threshold_pose])

        if iD == 'threshold_points':
            # Maj de l'attribut
            self.threshold_points = round(value, 2)
            # Maj de la config
            self.app.config.set('pose', 'threshold_points', self.threshold_points)
            # Sauvegarde dans le *.ini
            self.app.config.write()

            # Envoi de la valeur au process enfant
            if scr.p1_conn:
                scr.p1_conn.send(['threshold_points', self.threshold_points])

        if iD == 'profondeur_mini':
            self.profondeur_mini = int(value)

            self.app.config.set('histopocene', 'profondeur_mini', self.profondeur_mini)
            self.app.config.write()

            if scr.p1_conn:
                scr.p1_conn.send(['profondeur_mini', self.profondeur_mini])
            if scr.p2_conn:
                scr.p2_conn.send(['profondeur_mini', self.profondeur_mini])

        if iD == 'profondeur_maxi':
            self.profondeur_maxi = int(value)

            self.app.config.set('histopocene', 'profondeur_maxi', self.profondeur_maxi)
            self.app.config.write()

            if scr.p1_conn:
                scr.p1_conn.send(['profondeur_maxi', self.profondeur_maxi])
            if scr.p2_conn:
                scr.p2_conn.send(['profondeur_maxi', self.profondeur_maxi])

        if iD == 'largeur_maxi':
            self.largeur_maxi = int(value)

            self.app.config.set('histopocene', 'largeur_maxi', self.largeur_maxi)
            self.app.config.write()
            if scr.p1_conn:
                scr.p1_conn.send(['largeur_maxi', self.largeur_maxi])
            if scr.p2_conn:
                scr.p2_conn.send(['largeur_maxi', self.largeur_maxi])

        if iD == 'pile_size':
            self.pile_size = int(value)

            self.app.config.set('histopocene', 'pile_size', self.pile_size)
            self.app.config.write()

            if scr.p2_conn:
                scr.p2_conn.send(['pile_size', self.pile_size])

        if iD == 'lissage':
            self.lissage = int(value)
            if self.lissage >= self.pile_size:
                self.lissage = self.pile_size - 1
            self.app.config.set('histopocene', 'lissage', self.lissage)
            self.app.config.write()

            if scr.p2_conn:
                scr.p2_conn.send(['lissage', self.lissage])

    def on_switch_info(self, instance, value):
        scr = self.app.screen_manager.get_screen('Main')
        if value:
            value = 1
        else:
            value = 0
        self.info = value
        if scr.p2_conn:
            scr.p2_conn.send(['info', self.info])
        self.app.config.set('histopocene', 'info', self.info)
        self.app.config.write()
        print("info =", self.info)

    def on_switch_mode_expo(self, instance, value):
        scr = self.app.screen_manager.get_screen('Main')
        if value:
            value = 1
        else:
            value = 0
        self.mode_expo = value
        if scr.p2_conn:
            scr.p2_conn.send(['mode_expo', self.mode_expo])
        if scr.p1_conn:
            scr.p1_conn.send(['mode_expo', self.mode_expo])
        self.app.config.set('histopocene', 'mode_expo', self.mode_expo)
        self.app.config.write()
        print("mode_expo =", self.mode_expo)


# Variable globale qui définit les écrans
# L'écran de configuration est toujours créé par défaut
# Il suffit de créer un bouton d'accès
# Les class appelées (MainScreen, ...) sont placées avant
SCREENS = { 0: (MainScreen, 'Main'),
            1: (Reglage, 'Reglage')}



class Grande_EchelleApp(App):
    """Construction de l'application. Exécuté par if __name__ == '__main__':,
    app est le parent de cette classe dans kv
    """

    def build(self):
        """Exécuté après build_config, construit les écrans"""

        # Création des écrans
        self.screen_manager = ScreenManager()
        for i in range(len(SCREENS)):
            # Pour chaque écran, équivaut à
            # self.screen_manager.add_widget(MainScreen(name="Main"))
            self.screen_manager.add_widget(SCREENS[i][0](name=SCREENS[i][1]))

        return self.screen_manager

    def build_config(self, config):
        """Excécuté en premier (ou après __init__()).
        Si le fichier *.ini n'existe pas,
                il est créé avec ces valeurs par défaut.
        Il s'appelle comme le kv mais en ini
        Si il manque seulement des lignes, il ne fait rien !
        """

        print("Création du fichier *.ini si il n'existe pas")

        config.setdefaults( 'camera',
                                        {   'width_input': 1280,
                                            'height_input': 720})

        config.setdefaults( 'pose',
                                        {   'threshold': 0.80})

        config.setdefaults( 'histopocene',
                                        {   'frame_rate_du_film': 25,
                                            'film': 'ICOS.mp4',
                                            'profondeur_mini': 1500,
                                            'profondeur_maxi': 4000,
                                            'largeur_maxi': 500,
                                            'pile_size': 16,
                                            'lissage': 11,
                                            'full_screen': 0,
                                            'mode_expo': 0,
                                            'raz': 5})

        print("self.config peut maintenant être appelé")

    def build_settings(self, settings):
        """Construit l'interface de l'écran Options, pour Grande_Echelle seul,
        Les réglages Kivy sont par défaut.
        Cette méthode est appelée par app.open_settings() dans .kv,
        donc si Options est cliqué !
        """

        print("Construction de l'écran Options")

        data = """[ {"type": "title", "title": "Histopocene"},

                        {   "type": "string",
                            "title": "Nom du film",
                            "desc": "Nom du fichier du fiml avecextension, sans chemin",
                            "section": "histopocene", "key": "film"}
                    ]"""

        # self.config est le config de build_config
        settings.add_json_panel('Grande_Echelle', self.config, data=data)

    def go_mainscreen(self):
        """Retour au menu principal depuis les autres écrans."""
        self.screen_manager.current = ("Main")

    def do_quit(self):
        print("Je quitte proprement, j'attends ....")
        scr = self.screen_manager.get_screen('Main')
        scr.bd.do_save(scr.datas)

        scr.p2_conn.send(['quit', 1])
        scr.p1_conn.send(['quit', 1])
        scr.kivy_receive_loop = 0
        sleep(0.5)

        scr.p1.terminate()
        scr.p2.terminate()
        sleep(0.5)

        # Kivy
        print("Quit final")
        Grande_EchelleApp.get_running_app().stop()



if __name__ == '__main__':
    """L'application s'appelle Grande_Echelle
    d'où
    la class
        Grande_EchelleApp()
    les fichiers:
        grande_echelle.kv
        grande_echelle.ini
    """

    Grande_EchelleApp().run()
