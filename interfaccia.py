# Sono qui raccolte tutte le funzioni che permettono la visualizzazione grafica del programma.

import time

RESET = "\033[0m"
ROSSO = "\033[31m"
VERDE = "\033[32m"
GIALLO = "\033[33m"
BLU = "\033[34m"
VIOLA = "\033[35m"
AZZ = "\033[36m"
GRASSETTO = "\033[1m"

icone = {
        "ambulanza": "🚑",
        "vigili_fuoco": "🔥",
        "polizia": "🚓",
        "protezione_civile": "🛡️ ",
        "soccorso_alpino": "🧗"
    }


VELOCITA = 1.0  


def imposta_velocita(nuova_velocita):
    global VELOCITA
    VELOCITA = nuova_velocita


def attesa(secondi):
    time.sleep(secondi * VELOCITA)


def mostra_dashboard(sistema, messaggio, colore_messaggio=RESET):
    nodi = sistema.costruttore.dht.myring.nodes
    nodi_occupati = len([n for n in nodi if not n.libero])
    totale_nodi = len(nodi)
    stress = (nodi_occupati / totale_nodi) * 100
    colore_barra = VERDE if stress < 40 else GIALLO if stress < 70 else ROSSO
    barra = colore_barra + "█" * int(stress/10) + RESET + "░" * (10 - int(stress/10))
    code_attive = []
    for k, v in sistema.code_attesa.items():
        if len(v) > 0:
            ico = icone[k]
            code_attive.append(f"{ico}: {len(v)}")
    if code_attive:
        stato_code = " | ".join(code_attive)
    else:
        stato_code = "Libere"
    print(f"\n╔" + "═"*70 + "╗")
    print(f"║ {GRASSETTO}STATO CITTA{RESET}         Tempo: {sistema.ora:>8.3f}                                  ║")
    print(f"╠" + "═"*70 + "╣")
    print(f"║ STRESS: [{barra}] {stress:>5.1f}%  |  CODE: {stato_code:<31}")
    print(f"╟" + "─"*70 + "╢")
    linee_msg = messaggio.split('\n')
    for linea in linee_msg:
        print(f"   {colore_messaggio}{linea}{RESET}")
    print(f"╚" + "═"*70 + "╝")


def stampa_header():
    print(f"┌" + "─"*58 + "┐")
    print(f"│ {GRASSETTO}SISTEMA DI RISPOSTA ALLE EMERGENZE SIMULATE DI UNA CITTÀ{RESET} │")
    print(f"└" + "─"*58 + "┘\n")


def mostra_mappa_citta(quartieri, nodi_totali):
    print(f"\n{GRASSETTO} MAPPA RISORSE CITTADINE {RESET}")
    print(f"═" * 75)
    quartieri_ordinati = sorted(quartieri.values(), key=lambda q: q.posizione_id)
    for q in quartieri_ordinati:
        nodi_locali = [n for n in nodi_totali if n.quart == q]
        print("")
        print(f" {GRASSETTO}{q.nome:<18}{RESET} [ID:{q.posizione_id:>3}] ", end="\n")
        report_risorse = {"ambulanza": 0, "vigili_fuoco": 0, "polizia": 0, "protezione_civile": 0, "soccorso_alpino": 0}
        for n in nodi_locali:
            valore = n.risorse
            report_risorse[n.spec] = report_risorse[n.spec] + valore
        for spec, totale_u in report_risorse.items():
            ico = icone[spec]
            nome_spec = spec.replace('_', ' ').upper()
            print(f"  {ico} {nome_spec:<18}: {totale_u} UNITÀ")
    print(f"═" * 75 + f"\n")


def mostra_report_finale(report, n_eventi):
    print(f"\n{GRASSETTO}╔" + "═"*68 + "╗")
    print(f"║{RESET}               {GRASSETTO}REPORT CONCLUSIVO DELLA SIMULAZIONE{RESET}                  ║")
    print(f"╚" + "═"*68 + "╝")

    print(f"\n{GRASSETTO} NUMERO DI EVENTI SIMULATI: {RESET}{n_eventi}")

    print(f"\n{GRASSETTO} DISTRIBUZIONE EMERGENZE PER QUARTIERE{RESET}")
    print("─" * 70)
    for q in report.distribuzione_quartieri():
        count = len(q.storico)
        if count > 0:
            barra = f"{GIALLO}█{RESET}" * (count)
            print(f" {q.nome:<18} | {barra} ({count})")

    print(f"\n{GRASSETTO} DISTRIBUZIONE EMERGENZE PER SPECIALIZZAZIONE{RESET}")
    print("─" * 70)
    for spec, count in report.distribuzione_specializzazione():
        if count > 0:
            ico = icone[spec]
            barra = f"{VIOLA}█{RESET}" * count
            print(f" {ico} {spec.capitalize():<18} | {barra} ({count})")
    
    print(f"\n{GRASSETTO} NODI DI INTERVENTO PIÙ OPERATIVI{RESET}")
    print("─" * 70)
    for i, n in enumerate(report.nodi_top()):
        if len(n.storico) > 0:
            print(f" {i+1}. Nodo {n.id:<3} [{n.spec.upper():<15}] in {GRASSETTO}{n.quart.nome:<12}{RESET} -> {len(n.storico)} interventi")

    print(f"\n{GRASSETTO} STATO DELLE CODE AL TERMINE DELLA SIMULAZIONE{RESET}")
    print("─" * 70)
    if report.richieste_inevase == 0:
        print(f" {VERDE}✔ Tutte le emergenze sono state gestite correttamente.{RESET}")
    else:
        for spec, lista in report.code.items():
            if len(lista) > 0:
                print(f" {ROSSO}⚠ {spec.upper():<18}: {len(lista)} richieste inevase{RESET}")
   
    print(f"\n{GRASSETTO} ANALISI CARICO DI RETE E PICCHI{RESET}")
    print("─" * 70)
    analisi = report.analisi_rete()
    
    def stampa_barra_percentuale(valore, etichetta):
        punti = int(valore / 2)
        barra = f"{AZZ}█{RESET}" * punti + "░" * (50 - punti)
        print(f" {etichetta:<16}: [{barra}] {valore:.1f}%")

    stampa_barra_percentuale(analisi["stress_picco"], "STRESS DI PICCO")
    stampa_barra_percentuale(analisi["stress_medio"], "STRESS MEDIO")
    

    print(f"\n{GRASSETTO} EFFICIENZA DEL ROUTING (HOP COUNT){RESET}")
    print("─" * 70)
    media_s = analisi["media_salti"]
    print(f" Media salti per ricerca: {media_s:.2f}")
    print(f" Salto più lungo        : {analisi['max_salti']} nodi")
    
    if media_s < 6:
        valutazione = f"{VERDE}Ottima (Ricerca efficiente){RESET}"
    elif media_s < 12:
        valutazione = f"{GIALLO}Saturazione moderata (Routing sotto sforzo){RESET}"
    else:
        valutazione = f"{ROSSO}Critica {RESET}"
    print(f" Valutazione rete       : {valutazione}")
