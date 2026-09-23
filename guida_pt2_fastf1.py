import sys

# =============================================================================
# 6. I tempi sono timedelta, non numeri
# =============================================================================

def sezione_6_tempi():
    """LapTime & co. sono pandas.Timedelta. Non si sommano a un float.

    È l'inciampo più frequente: matplotlib non sa disegnare un timedelta su un
    asse numerico, e 'LapTime' - 90 dà errore. Vanno convertiti in secondi.
    """
    sessione = fastf1.get_session(2024, "Monza", "R")
    sessione.load(telemetry=False, weather=False, messages=False)
    laps = sessione.laps.pick_drivers("LEC").pick_quicklaps()

    giro = laps.pick_fastest()
    print("Tipo di LapTime :", type(giro["LapTime"]).__name__)
    print("Valore grezzo   :", giro["LapTime"])

    # Un singolo valore -> .total_seconds()
    print("In secondi      :", giro["LapTime"].total_seconds())

    # Un'intera colonna -> .dt.total_seconds()
    secondi = laps["LapTime"].dt.total_seconds()
    print("Media dei giri  :", round(secondi.mean(), 3), "s")
    print("Migliore        :", round(secondi.min(), 3), "s")

    # Per stampare in formato 1:21.046 invece di 0 days 00:01:21.046000
    def formatta(td):
        totale = td.total_seconds()
        return f"{int(totale // 60)}:{totale % 60:06.3f}"

    print("Formattato      :", formatta(giro["LapTime"]))

    # In alternativa, fastf1.plotting.setup_mpl() insegna a matplotlib a
    # disegnare i timedelta direttamente sugli assi.


# =============================================================================
# 7. La telemetria — dal giro ai canali di bordo
# =============================================================================

def sezione_7_telemetria():
    """Da un oggetto Lap si scendono i dati campionati a bordo vettura.

    Serve aver caricato con telemetry=True (che è il default).
    """
    sessione = fastf1.get_session(2024, "Monza", "Q")
    sessione.load()  # tutti i default, telemetria compresa

    giro = sessione.laps.pick_drivers("LEC").pick_fastest()

    # --- tre modi per ottenere i dati ---------------------------------------
    # get_car_data()  -> canali della vettura: Speed, RPM, nGear, Throttle,
    #                    Brake, DRS
    # get_pos_data()  -> posizione in pista: X, Y, Z, Status
    # .telemetry      -> i due precedenti già uniti e allineati (il più comodo)

    car = giro.get_car_data()
    print("Canali di get_car_data():", list(car.columns))

    pos = giro.get_pos_data()
    print("Canali di get_pos_data():", list(pos.columns))

    tel = giro.telemetry
    print("Canali di .telemetry    :", list(tel.columns))
    print("Campioni sul giro       :", len(tel))

    # --- i metodi add_* aggiungono colonne derivate -------------------------
    # add_distance()          -> 'Distance', metri percorsi dall'inizio del giro
    # add_relative_distance() -> 'RelativeDistance', da 0 a 1 sul giro
    # add_driver_ahead()      -> distanza e sigla di chi precede
    car = car.add_distance()
    print("\nDopo add_distance():", list(car.columns))
    print("Lunghezza del giro:", round(car['Distance'].iloc[-1]), "m")
    print("Velocità massima  :", car["Speed"].max(), "km/h")

    print("\nEstratto dei dati:")
    print(car[["Distance", "Speed", "nGear", "Throttle", "Brake"]].head().to_string(index=False))

    # Telemetria dell'intera sessione, non di un solo giro:
    #   sessione.car_data['16']  e  sessione.pos_data['16']
    # sono dizionari indicizzati per NUMERO di pilota (stringa), non per sigla.


# =============================================================================
# 8. session.results — classifiche e anagrafica piloti
# =============================================================================

def sezione_8_risultati():
    """Il DataFrame dei risultati, una riga per pilota."""
    sessione = fastf1.get_session(2024, "Monza", "R")
    sessione.load(telemetry=False, weather=False, messages=False)

    risultati = sessione.results
    print("Colonne dei risultati:")
    print(" ", list(risultati.columns))

    print("\nPodio:")
    print(risultati[["Position", "Abbreviation", "FullName", "TeamName", "Points"]]
          .head(3).to_string(index=False))

    # In qualifica ci sono anche le colonne Q1, Q2, Q3 con i tempi per fase.

    # session.drivers è la lista dei NUMERI di gara, come stringhe
    print("\nsession.drivers:", sessione.drivers[:5], "...")

    # get_driver() accetta sia la sigla sia il numero
    pilota = sessione.get_driver("LEC")
    print("get_driver('LEC'):", pilota["FullName"], "-", pilota["TeamName"],
          "- arrivato P" + str(int(pilota["Position"])))


# =============================================================================
# 9. Meteo, bandiere, circuito
# =============================================================================

def sezione_9_contorno():
    """I dati che stanno intorno ai giri."""
    sessione = fastf1.get_session(2024, "Monza", "R")
    sessione.load(telemetry=False)  # weather e messages restano True

    # --- meteo: un campione ogni minuto -------------------------------------
    meteo = sessione.weather_data
    print("Colonne meteo:", list(meteo.columns))
    print("Temp. aria media :", round(meteo["AirTemp"].mean(), 1), "°C")
    print("Temp. pista max  :", meteo["TrackTemp"].max(), "°C")
    print("Ha piovuto       :", bool(meteo["Rainfall"].any()))

    # Ogni giro ha anche il suo meteo allineato:
    #   sessione.laps.get_weather_data()

    # --- messaggi della direzione gara --------------------------------------
    messaggi = sessione.race_control_messages
    print("\nMessaggi direzione gara:", len(messaggi))
    print(messaggi[["Lap", "Category", "Message"]].head(3).to_string(index=False))

    # --- informazioni sul tracciato -----------------------------------------
    # get_circuit_info() dà le curve, con posizione X/Y, numero e lettera.
    # Utilissimo per annotare le curve su una mappa del circuito.
    circuito = sessione.get_circuit_info()
    print("\nCurve del tracciato:", len(circuito.corners))
    print(circuito.corners[["Number", "Letter", "Distance", "X", "Y"]].head(3).to_string(index=False))
    print("Rotazione mappa:", circuito.rotation, "gradi")


# =============================================================================
# 10. fastf1.plotting — colori ufficiali e confronti
# =============================================================================

def sezione_10_plotting():
    """FastF1 conosce i colori di team, piloti e mescole.

    Non serve inventarsi una palette: in F1 il colore È l'identità della
    squadra, e usare quello rende il grafico leggibile a colpo d'occhio.
    """
    sessione = fastf1.get_session(2024, "Monza", "R")
    sessione.load(telemetry=False, weather=False, messages=False)

    # setup_mpl() applica lo stile FastF1 a matplotlib e, cosa più utile,
    # abilita il supporto ai timedelta sugli assi.
    #   fastf1.plotting.setup_mpl(mpl_timedelta_support=True, color_scheme='fastf1')

    print("Colore pilota  LEC:", fastf1.plotting.get_driver_color("LEC", sessione))
    print("Colore team Ferrari:", fastf1.plotting.get_team_color("Ferrari", sessione))
    print("Colore mescola SOFT:", fastf1.plotting.get_compound_color("SOFT", sessione))

    print("\nMescole della sessione:", fastf1.plotting.list_compounds(sessione))
    print("Squadre:", fastf1.plotting.list_team_names(sessione)[:4], "...")

    # Utile per le legende ordinate per posizione in campionato:
    #   fastf1.plotting.add_sorted_driver_legend(ax, sessione)

    # --- confronto tra due giri ---------------------------------------------
    # delta_time restituisce lo scarto del secondo giro rispetto al primo,
    # campionato lungo la distanza: positivo = il secondo è più lento.
    lec = sessione.laps.pick_drivers("LEC").pick_fastest()
    pia = sessione.laps.pick_drivers("PIA").pick_fastest()
    delta, rif, confronto = fastf1.utils.delta_time(lec, pia)
    print(f"\nDelta PIA vs LEC: parte da {delta.iloc[0]:+.3f}s e chiude a {delta.iloc[-1]:+.3f}s")


# =============================================================================
# 11. Errori tipici e come evitarli
# =============================================================================

def sezione_11_trappole():
    """Promemoria dei punti dove ci si incastra."""
    promemoria = [
        ("Cache non abilitata",
         "Ogni avvio riscarica tutto. Chiama Cache.enable_cache() una volta all'inizio."),
        ("Attributi che non esistono",
         "session.laps prima di session.load() solleva un errore: load() riempie l'oggetto."),
        ("Telemetria vuota",
         "Se hai caricato con telemetry=False, get_car_data() non ha dati da restituire."),
        ("pick_driver deprecato",
         "Dalla 3.4 si usa pick_drivers / pick_teams al plurale."),
        ("LapTime è NaT",
         "Out lap, in lap e giri interrotti non hanno tempo. Filtra con pick_accurate() "
         "o con laps['LapTime'].notna()."),
        ("Timedelta sugli assi",
         "Converti con .dt.total_seconds(), oppure chiama plotting.setup_mpl()."),
        ("Position solo in gara",
         "In prove e qualifica la colonna Position non ha il significato che ti aspetti."),
        ("Telemetria solo dal 2018",
         "Prima di quell'anno ci sono risultati e tempi, ma nessun canale di bordo."),
        ("car_data indicizzato per numero",
         "session.car_data vuole il numero di gara come stringa ('16'), non la sigla ('LEC')."),
        ("Chiamate di rete lente",
         "get_session() è istantanea, load() no: in una GUI mostra uno stato di attesa "
         "e chiama processEvents() prima di bloccare."),
    ]
    for titolo, spiegazione in promemoria:
        print(f"\n  {titolo}\n    {spiegazione}")


# =============================================================================
# Esecuzione
# =============================================================================

SEZIONI = {
    1: ("get_session e identificazione sessione", sezione_1_get_session),
    2: ("calendario ed eventi", sezione_2_calendario),
    3: ("session.load e i suoi flag", sezione_3_load),
    4: ("session.laps, il DataFrame centrale", sezione_4_laps),
    5: ("i metodi pick_* per filtrare", sezione_5_pick),
    6: ("i tempi sono timedelta", sezione_6_tempi),
    7: ("la telemetria di bordo", sezione_7_telemetria),
    8: ("risultati e anagrafica piloti", sezione_8_risultati),
    9: ("meteo, bandiere, circuito", sezione_9_contorno),
    10: ("fastf1.plotting e delta_time", sezione_10_plotting),
    11: ("errori tipici", sezione_11_trappole),
}


def main(argv):
    if not argv:
        print(__doc__)
        print("Sezioni disponibili:\n")
        for numero, (titolo, _) in SEZIONI.items():
            print(f"  {numero:>2}. {titolo}")
        print("\nEsempio:  python guida_fastf1.py 1 5 11")
        return

    for argomento in argv:
        try:
            numero = int(argomento)
        except ValueError:
            print(f"'{argomento}' non è un numero di sezione.")
            continue
        if numero not in SEZIONI:
            print(f"Sezione {numero} inesistente.")
            continue

        titolo, funzione = SEZIONI[numero]
        print("\n" + "=" * 70)
        print(f"SEZIONE {numero} — {titolo.upper()}")
        print("=" * 70)
        funzione()

if __name__ == "__main__":
    main(sys.argv[1:])