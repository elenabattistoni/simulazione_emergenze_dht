from citta_simulazione import *
from struttura_intervento import *
from interfaccia import *
import csv
 
# Costruisce la città e la rete di gestione delle emergenze.
class Costruttore():
    def __init__(self):
        self.dht = DHT(9)
        self.quartieri = {}
        self.costruzione_rete_gem()
   
    # Costruisce la città: genera i quartieri (dal file quartieri.csv), 
    # e memorizza le probabilità di avvenimento di ciascuna emergenza (dal file emergenze.csv).
    def costruzione_citta(self):
        with open("quartieri.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                q = Quartiere(row["nome"], int(row["posizione_id"]), float(row["lam"]))
                self.quartieri[q.nome] = q
            
        with open("emergenze.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                q = self.quartieri[row["quartiere"]]
                q.emergenze_prob.append(
                (row["descrizione"], float(row["probabilita"]))
                )

    # Costruisce la rete di gestione delle emergenze: identifica i nodi di intervento (dal file nodi_intervento.csv).     
    def costruzione_rete_gem(self):
        self.costruzione_citta()
        nodi_intervento = []
        with open("nodi_intervento.csv", newline = "", encoding = "utf-8") as f:
            reader = csv.DictReader(f, delimiter = ";")
            for row in reader:
                quartiere = self.quartieri[row["quartiere"]]
                ni = NodoIntervento(row["specializzazione"], 
                                quartiere, 
                                int(row["unita"]),
                                self.dht.myring.m)
                nodi_intervento.append(ni)
        self.dht.populate(nodi_intervento)
        self.dht.computeAllFTs()  

    # Permette alla città di tornare alla situazione di partenza.
    def reset_citta(self):
        for n in self.dht.myring.nodes:
            n.libero = True
            n.storico = []
        for q in self.quartieri.values():
            q.storico = []
            q.tp_emergenza = 0.0        


# Gestisce la simulazione, garantendo la memorizzazione dei dati derivanti da questa e rilevanti per l'analisi.            
class SistemaEmergenze():
    def __init__(self):
        self.costruttore = Costruttore()
        self.ora = 0.0
        self.storico_stress = []
        self.storico_salti = []
        self.code_attesa = {
        "ambulanza": [],
        "vigili_fuoco": [],
        "polizia": [],
        "protezione_civile": [],
        "soccorso_alpino": []
    }

    # Permette la generazione delle emergenze in tutti i quartieri della città.     
    def partenza_simulazione(self):
        for q in self.costruttore.quartieri.values():
            q.pianifica_emergenza(self.ora)

    # Porta le emergenze (trasformate in richieste di intervento) dai quartieri alla rete di gestione delle emergenze. 
    def instrada_richiesta(self, richiesta):
        nodo, num_salti = self.costruttore.dht.search(richiesta)
        if nodo and nodo.libero:
            return nodo, num_salti
        else:
            return None, num_salti

    # Gestisce le emergenze che non hanno trovato subito soluzione (ordinandole per gravità decrescente).
    def controlla_coda(self, eventi_rilascio, specializzazione):        
        coda_spec = self.code_attesa[specializzazione]
        if not coda_spec:
            return
        coda_spec.sort(key=lambda x: x.emergenza.gravita, reverse=True)
        for i in range(len(coda_spec)):
            req = coda_spec[i]
            risultato, num_salti = self.instrada_richiesta(req)
            if risultato:
                req.ora_inizio_intervento = self.ora
                tempo_rilascio = risultato.alloca_risorse(req)
                eventi_rilascio.append((tempo_rilascio, risultato, req))
                msg = f" RECUPERO CODA: {req.emergenza.descrizione}\n  Assegnato a Nodo {risultato.id} ({risultato.spec})"
                mostra_dashboard(self, msg, VIOLA)
                self.registra_stress()
                coda_spec.pop(i)
                return

    # Gestisce la simulazione: dalla generazione alla soluzione.
    def simulazione(self, n_eventi):
        self.partenza_simulazione()
        eventi_rilascio = []
        emergenze_generate = 0

        # La simulazione genera nuove emergenze nel numero richiesto
        while emergenze_generate < n_eventi:
            attesa(1.5)
            q = min(self.costruttore.quartieri.values(), key=lambda q: q.tp_emergenza)
            tempo_prossima_emergenza = q.tp_emergenza

            # Prima di procedere si controlla se ci sono emergenze precedentemente prese in carico che si sono concluse:
            # in caso positivo si rilasciano le risorse occupate.
            eventi_rilascio.sort(key=lambda e: e[0])
            while eventi_rilascio and eventi_rilascio[0][0] <= tempo_prossima_emergenza:
                tempo_rilascio, nodo_da_liberare, richiesta_finita = eventi_rilascio.pop(0)
                self.ora = tempo_rilascio
                nodo_da_liberare.rilascia_risorse()
                msg_ril = f"⚡ RILASCIO RISORSE\n  Nodo {nodo_da_liberare.id} ({nodo_da_liberare.spec}) è tornato disponibile."
                mostra_dashboard(self, msg_ril, AZZ)
                self.registra_stress()

                # Si controlla se emergenze non risolte in precedenza possono essere prese in carico dalle risorse appena rilasciate.
                self.controlla_coda(eventi_rilascio, richiesta_finita.specializzazione)

            # Si fa procedere la simulazione generando nuove emergenze e tentando di risolverle.
            self.ora = tempo_prossima_emergenza
            em = q.generazione_emergenza(self.ora)
            richiesta = RichiestaIntervento(em)
            emergenze_generate += 1
            pallini = "◉" * em.gravita + "○" * (3 - em.gravita)
            msg_unificato = (f"{GIALLO}⚠ EMERGENZA: {em.descrizione} [{pallini}]{RESET}\n"
                             f"{GIALLO}  Quartiere: {q.nome} (Pos ID: {q.posizione_id}){RESET}\n"
                             f"───────────────────────────────────────────────────────\n"
                             f"  ⚙ {GRASSETTO}DETTAGLI TECNICI RICHIESTA:{RESET}\n"
                             f"  Specializzazione: {richiesta.specializzazione.upper()}\n"
                             f"  Risorse: {richiesta.risorse_necessarie} | Target ID: {richiesta.target_id}")
            mostra_dashboard(self, msg_unificato, RESET)
            self.registra_stress()
            attesa(0.5)
            nodo_trovato, num_salti = self.instrada_richiesta(richiesta)
            self.storico_salti.append(num_salti)
            attesa(0.8)
            if nodo_trovato and nodo_trovato.libero:
                tempo_rilascio = nodo_trovato.alloca_risorse(richiesta)
                eventi_rilascio.append((tempo_rilascio, nodo_trovato, richiesta))
                msg = f"➔ ALLOCAZIONE RIUSCITA\n  Nodo {nodo_trovato.id} ({nodo_trovato.spec}) gestisce l'emergenza."
                mostra_dashboard(self, msg, VERDE)
                self.registra_stress()
            else:
                self.code_attesa[richiesta.specializzazione].append(richiesta)
                msg = f"✖ RISORSE NON DISPONIBILI AL MOMENTO\n  Richiesta inserita nella coda: {richiesta.specializzazione}"
                mostra_dashboard(self, msg, ROSSO)
                self.registra_stress()
        
        # Una volta generato il numero di emergenze richieste, si procede con la simulazione concludendo tutte quelle rimaste irrisolte.
        print("")
        print("")
        print(f"{GRASSETTO}SONO FINITE LE EMERGENZE GENERATE. Si procede con la simulazione.{RESET}")
        print("")
        while eventi_rilascio:
            eventi_rilascio.sort(key=lambda e: e[0])
            tempo_rilascio, nodo_da_liberare, richiesta = eventi_rilascio.pop(0)
            self.ora = tempo_rilascio
            nodo_da_liberare.rilascia_risorse()
            self.controlla_coda(eventi_rilascio, richiesta.specializzazione)
            msg_svuota = f"⚡ RILASCIO FINALE\n  Nodo {nodo_da_liberare.id} liberato al tempo {self.ora:.2f}."
            mostra_dashboard(self, msg_svuota, AZZ)
            self.registra_stress()
            attesa(0.5)

    # Registra lo stress della rete di gestione delle emergenze: è la percentuale di nodi occupati.         
    def registra_stress(self):
        nodi = self.costruttore.dht.myring.nodes
        occupati = len([n for n in nodi if not n.libero])
        percentuale = (occupati / len(nodi)) * 100
        self.storico_stress.append(percentuale)

    # Permette all'intero sistema di resettarsi.
    def reset_sistema(self):
        self.ora = 0.0
        for k in self.code_attesa:
            self.code_attesa[k] = []
        self.storico_stress = []
        self.costruttore.reset_citta()


# Genera le statistiche relative alla simulazione appena avvenuta.
class Report():
    def __init__(self, sistema):
        self.ora_fine = sistema.ora
        self.quartieri = sistema.costruttore.quartieri.values()
        self.nodi = sistema.costruttore.dht.myring.nodes
        self.code = sistema.code_attesa
        self.stress = sistema.storico_stress
        self.salti = sistema.storico_salti
        
        self.totale_emergenze = sum(len(q.storico) for q in self.quartieri)
        self.richieste_inevase = sum(len(lista) for lista in self.code.values())
        self.successo_rate = ((self.totale_emergenze - self.richieste_inevase) / self.totale_emergenze * 100)

    def distribuzione_quartieri(self):
        return sorted(self.quartieri, key=lambda q: len(q.storico), reverse=True)

    def distribuzione_specializzazione(self):
        stats = {spec: 0 for spec in ["ambulanza", "vigili_fuoco", "polizia", "protezione_civile", "soccorso_alpino"]}
        for n in self.nodi:
            if n.spec in stats:
                stats[n.spec] += len(n.storico)
        return sorted(stats.items(), key=lambda x: x[1], reverse=True)

    def nodi_top(self):
        return sorted(self.nodi, key=lambda n: len(n.storico), reverse=True)[:5]

    def analisi_rete(self):
        return {
            "stress_medio": sum(self.stress) / len(self.stress) if self.stress else 0,
            "stress_picco": max(self.stress) if self.stress else 0,
            "media_salti": sum(self.salti) / len(self.salti) if self.salti else 0,
            "max_salti": max(self.salti) if self.salti else 0
        }

# Mostra l'interfaccia del programma e permette l'interazione con l'utente
def main():
    stampa_header()
    sistema = SistemaEmergenze()
    simulazione_eseguita = False

    while True:
        print(f"\n{GRASSETTO}--- MENU PRINCIPALE ---{RESET}")
        print("1. Guarda la città")
        print("2. Fai partire la simulazione")
        print("3. Vedi report finale")
        print("4. Esci")
        scelta = input(f"\nSeleziona un'opzione: ")

        if scelta == "1":
            mostra_mappa_citta(sistema.costruttore.quartieri, sistema.costruttore.dht.myring.nodes)
            input(f"\nPremi INVIO per tornare al menu.")

        elif scelta == "2":
            sistema.reset_sistema()
            try:
                print(f"\n{GRASSETTO}--- IMPOSTAZIONE VELOCITA ---{RESET}")
                print("1. Standard (con pause)")
                print("2. Istantanea (senza pause)")
                scelta_vel = input("Scelta: ")
                velocita_impostata = 1.0 if scelta_vel == "1" else 0.0
                imposta_velocita(velocita_impostata)
                n_eventi = int(input(f"\nInserire numero di eventi da simulare: "))
                print(f"\n{GRASSETTO}AVVIO SIMULAZIONE.{RESET}")
                sistema.simulazione(n_eventi)
                simulazione_eseguita = True
                print(f"\nSimulazione completata con successo.")
                input(f"\nPremi INVIO per tornare al menu.")
            except ValueError:
                print(f"\n{ROSSO}Errore: Inserire un numero intero valido.{RESET}")
                input(f"\nPremi INVIO per tornare al menu.")

        elif scelta == "3":
            if simulazione_eseguita:
                report = Report(sistema)
                mostra_report_finale(report, n_eventi)
            else:
                print(f"\n{ROSSO}Nessun dato disponibile. Eseguire prima una simulazione (Opzione 2).{RESET}")
            input(f"\nPremi INVIO per tornare al menu.")

        elif scelta == "4":
            print(f"\n{GRASSETTO}Chiusura della centrale operativa. Arrivederci.{RESET}")
            break

        else:
            print(f"\n{ROSSO}Opzione non valida. Riprova.{RESET}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{ROSSO}Interruzione rilevata.{RESET}")
        print(f"{GRASSETTO}Chiusura della centrale operativa. Arrivederci.{RESET}")
        exit(0)


