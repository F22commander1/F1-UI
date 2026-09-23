"""Guida ragionata a FastF1 — le basi, con esempi eseguibili.

Il file è diviso in sezioni numerate. Ogni sezione è una funzione che stampa
quello che fa, così si può leggere il codice e poi vederlo girare:

    python guida_fastf1.py            # elenco delle sezioni
    python guida_fastf1.py 3          # esegue solo la sezione 3
    python guida_fastf1.py 1 2 3      # più sezioni in fila

La prima esecuzione di una sezione scarica i dati dai server FastF1 e può
metterci un minuto; dalla seconda in poi legge dalla cache ed è istantanea.

Testato con FastF1 3.8, pandas 2.3, Python 3.x.
"""

import os

import fastf1
import fastf1.plotting
import fastf1.utils


# =============================================================================
# 0. LA CACHE — da fare sempre, prima di ogni altra cosa
# =============================================================================
# FastF1 scarica i dati dai server della F1 e li tiene su disco. Senza cache
# ogni avvio riscarica tutto: sono decine di MB per sessione e i server sono
# lenti. Con la cache, la seconda volta la stessa sessione si apre in un attimo.
#
# enable_cache() va chiamata UNA volta sola, all'import del programma, prima
# di qualsiasi get_session(). La cartella viene creata se non esiste.

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "f1_cache")
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)


# =============================================================================
# 1. get_session() — come si identifica una sessione
# =============================================================================

def sezione_1_get_session():
    """fastf1.get_session(anno, gran_premio, sessione) -> Session

    I tre argomenti accettano forme diverse, ed è la fonte di metà degli errori
    di chi comincia. Nota: get_session() NON scarica ancora niente, costruisce
    solo l'oggetto. Il download avviene a session.load().
    """
    # --- argomento 1: l'anno ------------------------------------------------
    # La telemetria esiste dal 2018 in poi. Risultati e tempi sul giro si
    # trovano anche più indietro (via Ergast), ma senza dati di telemetria.

    # --- argomento 2: il Gran Premio ----------------------------------------
    # Tre modi equivalenti, scegli quello che preferisci:
    #   * il numero di round nel calendario ......... 16
    #   * il nome ufficiale dell'evento ............. "Italian Grand Prix"
    #   * il nome della località o un soprannome .... "Monza"
    # Il matching è "fuzzy": tollera minuscole, accenti e piccoli errori di
    # battitura. "monza", "Monza", "Italy" arrivano tutti allo stesso evento.

    # --- argomento 3: la sessione -------------------------------------------
    # Sigle brevi:  'FP1' 'FP2' 'FP3' 'Q' 'S' 'SQ' 'R'
    # Nomi estesi:  'Practice 1' 'Qualifying' 'Sprint' 'Race'
    # Numeri:       1..5 (posizione della sessione nel weekend)
    #   R  = gara            Q  = qualifica
    #   S  = sprint          SQ = sprint qualifying / sprint shootout
    #   FP1/FP2/FP3 = prove libere

    sessione = fastf1.get_session(2024, "Monza", "R")

    # L'oggetto esiste ma è ancora "vuoto": gli attributi anagrafici però ci sono
    print("Oggetto creato senza scaricare nulla:")
    print("  nome sessione :", sessione.name)
    print("  evento        :", sessione.event["EventName"])
    print("  round         :", sessione.event["RoundNumber"])
    print("  data          :", sessione.event["EventDate"].date())
    print("  circuito      :", sessione.event["Location"], "-", sessione.event["Country"])

    # Tre chiamate equivalenti alla stessa gara:
    a = fastf1.get_session(2024, 16, "Race")
    b = fastf1.get_session(2024, "Italian Grand Prix", "R")
    c = fastf1.get_session(2024, "monza", 5)
    print("\nStesso evento da 3 scritture diverse:",
          a.event["EventName"], "|", b.event["EventName"], "|", c.event["EventName"])


def sezione_2_calendario():

    # L'intero calendario di una stagione, come DataFrame
    calendario = fastf1.get_event_schedule(2024)
    print(" ", list(calendario.columns))

    print("\nPrimi 5 round del 2024:")
    print(calendario[["RoundNumber", "EventName", "Location", "EventDate"]].head().to_string(index=False))

    # Un singolo evento (una riga del calendario, come Series)
    evento = fastf1.get_event(2024, "Monza")
    print("\nEvento singolo:", evento["EventName"], "-", evento["EventDate"].date())

    # Formato del weekend: 'conventional' oppure 'sprint_qualifying'. Serve per
    # sapere in anticipo se esistono FP2/FP3 o invece una sprint.
    print("Formato weekend:", evento["EventFormat"])

    # I nomi delle 5 sessioni del weekend stanno in colonne Session1..Session5
    print("Sessioni:", [evento[f"Session{i}"] for i in range(1, 6)])

    # Comodo: l'evento sa anche costruirsi le proprie sessioni
    gara = evento.get_race()
    print("Da evento a sessione:", gara.name)

    # Solo gli eventi già disputati (utile per non chiedere gare future)
    import pandas as pd
    passati = calendario[calendario["EventDate"] < pd.Timestamp.now()]
    print(f"\nEventi già corsi nel 2024: {len(passati)} su {len(calendario)}")


def sezione_3_load():
    """load() riempie l'oggetto. I flag decidono cosa scaricare.

    Scaricare meno = più veloce. La telemetria è di gran lunga la parte
    pesante: se ti servono solo i tempi sul giro, mettila a False.
    """
    sessione = fastf1.get_session(2024, "Monza", "R")

    # Firma completa, con i valori di default:
    #   session.load(laps=True, telemetry=True, weather=True, messages=True)
    #
    #   laps      -> tempi sul giro, mescole, stint, posizioni
    #   telemetry -> velocità, marce, gas, freno, DRS, posizione in pista
    #   weather   -> temperature aria/pista, umidità, vento, pioggia
    #   messages  -> track status e messaggi della direzione gara
    sessione.load(laps=True, telemetry=False, weather=False, messages=False)

    print("Sessione caricata:", sessione.event["EventName"], sessione.name)
    print("Giri totali nel dataset:", len(sessione.laps))
    print("Piloti presenti:", len(sessione.drivers))

    # Attenzione: prima di load() questi attributi sollevano un'eccezione.
    # È l'errore più comune — "perché session.laps non esiste?" perché manca load().


# =============================================================================
# 4. session.laps — il DataFrame centrale di FastF1
# =============================================================================

def sezione_4_laps():
    """session.laps è un DataFrame pandas arricchito (classe Laps).

    Vale tutto quello che sai di pandas: filtri booleani, groupby, sort_values.
    In più ha i metodi pick_* che sono solo scorciatoie leggibili per i filtri
    più frequenti.
    """
    sessione = fastf1.get_session(2024, "Monza", "R")
    sessione.load(telemetry=False, weather=False, messages=False)

    laps = sessione.laps
    print("Colonne disponibili su ogni giro:")
    for colonna in laps.columns:
        print("   ", colonna)

    print("\nLe più usate:")
    print("  Driver / DriverNumber / Team  -> chi ha fatto il giro")
    print("  LapNumber / LapTime           -> quale giro e in quanto")
    print("  Sector1Time..Sector3Time      -> i tre settori")
    print("  Compound / TyreLife / Stint   -> mescola, giri sulla gomma, nr. stint")
    print("  Position                      -> posizione in gara a fine giro")
    print("  PitInTime / PitOutTime        -> giri di entrata/uscita dai box")
    print("  IsAccurate                    -> il dato è affidabile per l'analisi")
    print("  TrackStatus                   -> bandiere attive durante il giro")

    print("\nPrimi giri di Leclerc:")
    print(laps.pick_drivers("LEC")[["LapNumber", "LapTime", "Compound", "Position"]].head().to_string(index=False))


# =============================================================================
# 5. I metodi pick_* — filtrare i giri
# =============================================================================

def sezione_5_pick():
    """Le scorciatoie di selezione. Si concatenano a piacere."""
    sessione = fastf1.get_session(2024, "Monza", "R")
    sessione.load(telemetry=False, weather=False, messages=False)
    laps = sessione.laps

    # pick_drivers accetta sigla, numero, o una lista
    print("pick_drivers('VER')         ->", len(laps.pick_drivers("VER")), "giri")
    print("pick_drivers(['VER','LEC']) ->", len(laps.pick_drivers(["VER", "LEC"])), "giri")

    # pick_teams filtra per squadra
    print("pick_teams('Ferrari')       ->", len(laps.pick_teams("Ferrari")), "giri")

    # pick_quicklaps scarta i giri lenti (safety car, out lap, traffico).
    # Di default tiene i giri sotto il 107% del migliore; la soglia è regolabile.
    print("pick_quicklaps()            ->", len(laps.pick_quicklaps()), "giri")
    print("pick_quicklaps(1.03)        ->", len(laps.pick_quicklaps(1.03)), "giri")

    # pick_accurate tiene solo i giri che FastF1 considera misurati bene
    print("pick_accurate()             ->", len(laps.pick_accurate()), "giri")

    # pick_wo_box toglie i giri di entrata e uscita dai box
    print("pick_wo_box()               ->", len(laps.pick_wo_box()), "giri")

    # pick_fastest() restituisce UN SOLO giro (oggetto Lap, non Laps)
    veloce = laps.pick_drivers("LEC").pick_quicklaps().pick_fastest()
    print("\nGiro veloce di LEC: giro", int(veloce["LapNumber"]), "in", veloce["LapTime"])

    # ATTENZIONE alle versioni: pick_driver() e pick_team() (singolare) sono
    # deprecati da FastF1 3.4. Usa sempre pick_drivers / pick_teams al plurale.

    # I pick_ si concatenano: leggibile e ordinato
    selezione = laps.pick_teams("Ferrari").pick_quicklaps().pick_wo_box()
    print("Giri buoni Ferrari fuori dai box:", len(selezione))

# Il runner (main, SEZIONI 1-11) vive in guida_pt2_fastf1.py, che importa
# le sezioni 1-5 da qui. Esegui quel file per lanciare la guida completa.
