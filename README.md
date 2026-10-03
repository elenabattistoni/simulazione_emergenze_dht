# Simulazione della Gestione delle Emergenze Urbane tramite DHT Chord

Progetto per l'esame di Sistemi di Elaborazione 2 (A.A. 2025/2026)  
Corso di Laurea Triennale in Statistica per l'Economia e l'Impresa — Università degli Studi di Padova  
Docente: Prof. Carlo Ferrari  
Autrice: Elena Battistoni

---

## Descrizione del Progetto

Il sistema modella la gestione delle emergenze in una città fittizia suddivisa in 10 quartieri, integrando una Simulazione ad Eventi Discreti con un'infrastruttura di rete decentralizzata basata sul protocollo DHT Chord.

### Caratteristiche principali

- **Generazione degli eventi**: processo di Poisson indipendente per quartiere, con frequenza media ($\lambda$) personalizzata.
- **Instradamento (DHT Chord)**: codifica degli ID nello spazio $2^9 = 512$ basata sulla struttura `SUQ` (Specializzazione, Unità, Quartiere).
- **Routing e Finger Table**: ricerca decentralizzata del nodo di intervento con complessità $O(\log N)$.
- **Gestione delle code**: code di attesa separate per specializzazione, con priorità in base alla gravità dell'emergenza.
- **Interfaccia e reporting**: interfaccia da riga di comando per il monitoraggio in tempo reale e report conclusivo sul carico di rete (hop count, stress di picco e medio).

---

## Struttura del Codice

- `citta_simulazione.py` — modello dei quartieri e generazione delle emergenze.
- `struttura_intervento.py` — Ring Chord, Finger Table e nodi di intervento.
- `sistema_emergenze.py` — coordinatore ed event manager della simulazione, gestione delle code e report finale.
- `interfaccia.py` — visualizzazione da riga di comando della simulazione.
- `quartieri.csv` — configurazione dei quartieri e dei relativi parametri $\lambda$.
- `emergenze.csv` — probabilità delle varie tipologie di emergenza per quartiere.
- `nodi_intervento.csv` — configurazione dei nodi di intervento e delle loro risorse.
- `relazione_sistemi2_battistoni.pdf` — relazione completa del progetto.

---

## Esecuzione

Il progetto usa esclusivamente moduli della libreria standard di Python 3 (nessuna dipendenza esterna). È stato sviluppato con Python 3.12.

Dalla cartella del progetto (i file CSV vengono letti con percorsi relativi):

```bash
python sistema_emergenze.py
```

Dal menu principale si può visualizzare la città, avviare la simulazione (con o senza pause, scegliendo il numero di eventi) e consultare il report finale.

Per una resa corretta di colori ed emoji serve un terminale che supporti i codici ANSI e Unicode.