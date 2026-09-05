import sys
import os

import fastf1
import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QMessageBox
from ui_mywindow import Ui_MainWindow  # generato da pyuic5 a partire da mywindow.ui

# FastF1 salva su disco i dati scaricati per evitare di riscaricarli ad ogni avvio
CACHE_DIR = os.path.join(os.path.dirname(__file__), "f1_cache")
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)


class MyApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        # ultima sessione FastF1 caricata, tenuta per riutilizzo futuro
        self.session = None  
        self.setupUi(self)

    def load_telemetry(self):
        # legge sessione/pilota scelti dall'utente
        year = self.yearSpinBox.value()
        gran_prix = self.gpLineEdit.text().strip()
        session_type = self.sessionComboBox.currentText()
        driver = self.driverLineEdit.text().strip().upper()

        if not gran_prix or not driver:
            QMessageBox.warning(self, "Dati mancanti", "Inserisci Gran Premio e codice pilota.")
            return

        self.statusLabel.setText("Caricamento sessione in corso...")

        # forza il ridisegno della UI prima della chiamata bloccante
        QApplication.processEvents()  





        try:
            # scarica (o legge dalla cache) la sessione ed estrae il giro più veloce del pilota
            session = fastf1.get_session(year, gran_prix, session_type)
            session.load(telemetry=True, laps=True, weather=False)
            lap = session.laps.pick_driver(driver).pick_fastest()
            telemetry = lap.get_car_data().add_distance()
        except Exception as exc:
            QMessageBox.critical(self, "Errore", f"Impossibile caricare i dati:\n{exc}")
            self.statusLabel.setText("")
            return

        self._plot_telemetry(telemetry, driver)
        self.statusLabel.setText(f"{driver} - giro più veloce: {lap['LapTime']}")
    

    def setupUi(self, MainWindow):
        # costruisce tutti i widget definiti in Qt Designer
        super().setupUi(MainWindow)  
        self.loadButton.clicked.connect(self.load_telemetry)
        self.reset_telemetry.clicked.connect(self.on_reset_telemetry)
        # inserisce un canvas matplotlib dentro il widget placeholder del .ui
        self.figure = Figure(figsize=(5, 4))
        self.canvas = FigureCanvas(self.figure)
        canvas_layout = QVBoxLayout(self.canvasWidget)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.addWidget(self.canvas)

    def on_reset_telemetry(self):
        # riporta canvas, campi e sessione allo stato iniziale post-avvio
        self.session = None
        self.figure.clear()
        self.canvas.draw()
        self.yearSpinBox.setValue(2024)
        self.gpLineEdit.clear()
        self.sessionComboBox.setCurrentIndex(0)
        self.driverLineEdit.clear()
        self.statusLabel.setText("")





    def _plot_telemetry(self, telemetry, driver):
        # ridisegna la traccia velocità-distanza del giro più veloce
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(telemetry["Distance"], telemetry["Speed"], label=driver)
        ax.set_xlabel("Distanza (m)")
        ax.set_ylabel("Velocità (km/h)")
        ax.set_title("Telemetria di velocità - giro più veloce")
        ax.legend()
        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())  # resta bloccato qui finché l'event loop di Qt non termina
