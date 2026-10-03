from citta_simulazione import *
from interfaccia import *

codici_spec = {"ambulanza": 0, "vigili_fuoco": 1, "polizia": 2, "protezione_civile": 3, "soccorso_alpino": 4}


# Rende le emergenze interpretabili dalla rete di gestione (che quindi sa come risolverle).
class RichiestaIntervento():
    tipi_specializzazione = {
        "infarto": "ambulanza",
        "caduta accidentale": "ambulanza",
        "intossicazione o avvelenamento": "ambulanza",
        "emergenza ostetrica": "ambulanza",
        "crisi epilettica": "ambulanza",
        "incendio veicolo": "vigili_fuoco",
        "incendio edificio": "vigili_fuoco",
        "incendio bosco": "vigili_fuoco",
        "fuga gas": "vigili_fuoco",
        "crollo strutturale": "vigili_fuoco",
        "rapina in corso": "polizia",
        "controllo traffico e incidenti": "polizia",
        "gestione manifestazioni o proteste": "polizia",
        "scomparsa persona": "polizia",
        "truffa o frode": "polizia",
        "alluvione o esondazione": "protezione_civile",
        "frana o smottamento": "protezione_civile",
        "terremoto": "protezione_civile",
        "evacuazione di zona a rischio": "protezione_civile",
        "blackout elettrico diffuso": "protezione_civile",
        "persona dispersa in montagna": "soccorso_alpino",
        "recupero in zone difficili": "soccorso_alpino",
        "emergenza nevosa o ghiaccio": "soccorso_alpino",
        "incidente escursionistico": "soccorso_alpino"
    }

    base_risorse = {
        "infarto": 1,
        "caduta accidentale": 1,
        "intossicazione o avvelenamento": 1,
        "emergenza ostetrica": 2,
        "crisi epilettica": 1,
        "incendio veicolo": 1,
        "incendio edificio": 2,
        "incendio bosco": 3,
        "fuga gas": 2,
        "crollo strutturale": 3,
        "controllo traffico e incidenti": 1,
        "truffa o frode": 1,
        "rapina in corso": 2,
        "gestione manifestazioni o proteste": 2,
        "scomparsa persona": 2,
        "blackout elettrico diffuso": 2,
        "evacuazione di zona a rischio": 3,
        "alluvione o esondazione": 3,
        "frana o smottamento": 3,
        "terremoto": 3,
        "persona dispersa in montagna": 2,
        "recupero in zone difficili": 2,
        "emergenza nevosa o ghiaccio": 1,
        "incidente escursionistico": 2
    }

    def __init__(self, emergenza):
        self.emergenza = emergenza
        self.specializzazione = None
        self.risorse_necessarie = None
        self.target_id = None
        self.durata = None  
        self.ora_inizio_intervento = None
        
        self.calcolo_risorse() 
        self.calcolo_target_id()

    # Calcola la quantità di risorse (in unità di intervento) necessarie per risolvere l'emergenza.        
    def calcolo_risorse(self):
        desc = self.emergenza.descrizione
        self.specializzazione = self.tipi_specializzazione[desc]

        unita = self.base_risorse[desc]
        moltiplicatore = self.emergenza.gravita
        unita = unita * moltiplicatore
        self.risorse_necessarie = unita
        
        base_durata = 1
        self.durata = base_durata * moltiplicatore

    # Calcola il punto da cui l'emergenza entrerà nella rete di gestione.    
    def calcolo_target_id(self):
        self.target_id = codici_spec[self.specializzazione] * 100 + self.risorse_necessarie * 10 + self.emergenza.quartiere.posizione_id

# Le finger table permettono i salti tra i nodi della rete.
class FT:
    def __init__(self, owner, m):
        self.owner = owner
        self.m = m
        self.tab = [None] * m
        
    def compute(self, ring): 
        for i in range(0, self.m): 
            target = (self.owner.id + (1 << i)) % (1 << self.m)
            candidate = ring.forward_from(target) 
            self.tab[i] = candidate
            

# Definisce il nodo di intervento, che prenderà a carico le emergenze (sottoforma di richieste di intervento) per risolverle. 
class NodoIntervento:
    def __init__(self, specializzazione, quartiere: Quartiere, 
                 unita, m):
        self.spec = specializzazione
        self.quart = quartiere
        self.risorse = unita
        self.libero = True
        self.m = m
        self.id = self.generazione_id()
        self.storico = []
        self.ft = FT(self, m)

    # Viene generato l'id del nodo (nella forma SUQ)    
    def generazione_id(self):
        Q = self.quart.posizione_id   
        S = codici_spec[self.spec]
        U = self.risorse
        return S * 100 + U * 10 + Q
       
    def __str__(self):
        return f"Nodo di intervento {self.id} \n- specializzazione: {self.spec} \n- quartiere: {self.quart} \n- risorse: {self.risorse}"

    # Valuta la capacità del nodo di risolvere una richiesta.
    def adatto_a_richiesta(self, richiesta):
        return self.spec == richiesta.specializzazione and self.risorse >= richiesta.risorse_necessarie
    
    # Permette al nodo di prendersi in carico dell'emergenza, ritornando il momento in cui questa sarà risolta.
    def alloca_risorse(self, richiesta):
        self.libero = False
        if richiesta.ora_inizio_intervento is None:
            inizio_reale = richiesta.emergenza.tempo
        else:
            inizio_reale = richiesta.ora_inizio_intervento
        fine_prevista = inizio_reale + richiesta.durata
        self.storico.append({
            'descrizione': richiesta.emergenza.descrizione,
            'inizio': inizio_reale,
            'fine': fine_prevista,
            'gravita': richiesta.emergenza.gravita
        })
        return fine_prevista
    
    # Libera il nodo dall'emergenza conclusa
    def rilascia_risorse(self):
        self.libero = True
    
    # Cerca nella finger table del nodo il nodo più vicino al target di ricerca.
    def searchNewId(self, id_ricercato):
        for i in range(self.m - 1, -1, -1):
            n_jump = self.ft.tab[i]
            if self.is_between(self.id, n_jump.id, id_ricercato):
                return n_jump
        return self.ft.tab[0]

    # Definisce l'ordinamento dei nodi (nel ring circolare).
    def is_between(self, start, middle, end):
        if start < end:
            return start < middle <= end
        else: 
            return middle > start or middle <= end

# Struttura base della rete di gestione delle emergenze.   
class Ring():
    def __init__(self, m):
        self.m = m
        self.size = 2**m
        self.nodes: list = []
    
    def addnode(self, node):
        self.nodes.append(node) 
        self.nodes.sort(key=lambda n: n.id)

    # Trova il nodo con id prossimo a quello dato.
    def forward_from(self, id):
        for node in self.nodes:
            if node.id >= id:
                return node
        return self.nodes[0]  

# Struttura base della rete di gestione delle emergenze.   
class DHT:
    def __init__(self, m):
        self.myring = Ring(m)
       
    def populate(self, nodes: list): 
        nodes.sort(key=lambda n: n.id)
        for node in nodes:
            self.myring.addnode(node)
        
    def computeAllFTs(self):
        for i in self.myring.nodes:
            i.ft.compute(self.myring)

    # Ricerca all'interno della rete del nodo che risolve l'emergenza (sottoforma di richiesta di intervento).
    def search(self, richiesta):
        
        # La richiesta entra nella rete tramite il nodo più vicino al target_id
        target_attuale = richiesta.target_id 
        nodo = self.myring.forward_from(target_attuale)
        visitati = set()
        salti = 0
        print(f"   {BLU}{GRASSETTO} ANALISI PERCORSO DHT (Target: {target_attuale}){RESET}")
        while (nodo.id, target_attuale) not in visitati:
            salti +=1
            visitati.add((nodo.id, target_attuale))
            attesa(0.4)
            print(f"      {BLU}↳ Arrivato al Nodo {GRASSETTO}{nodo.id:<3}{RESET} {BLU}(Specializzazione: {nodo.spec}){RESET}")
           
            # Se il nodo è adatto a prendersi carico della richiesta ed è libero nel momento in cui questa si presenta, l'emergenza viene evasa.
            if nodo.adatto_a_richiesta(richiesta) and nodo.libero:
                attesa(0.3)
                print(f"         {BLU}✔ Nodo compatibile e libero trovato!{RESET}")
                return nodo, salti
            
            # Se il nodo non è in grado di occuparsi dela richiesta, viene generato un nuovo target, che viene raggiunto tramite 
            # i salti, effettuabili grazie alle finger table dei nodi
            else:
                attesa(0.3)
                motivo = "OCCUPATO" if not nodo.libero else "SPEC. NON CORRISPONDENTE"
                nuovo_target = self.genera_nuovo_target(target_attuale)
                if nuovo_target is not None:
                    print(f"         {BLU}✘ {motivo}. Provo con più risorse: Target {nuovo_target}{RESET}")
                    target_attuale = nuovo_target
                else:
                    print(f"         {BLU}✘ {motivo}. Risorse massime raggiunte per questa spec.{RESET}")
            prossimo_nodo = nodo.searchNewId(target_attuale)
            # RIDONDANTE, si potrebbe togliere
            if prossimo_nodo.id == nodo.id:
                prossimo_nodo = nodo.ft.tab[0]
            attesa(0.2)
            print(f"      {BLU}⇄ Routing FT: Inoltro da {nodo.id} verso Target {target_attuale}.{RESET}")
            nodo = prossimo_nodo
        
        # Non è stato trovato nessun nodo in grado di prendersi carico della richiesta
        print(f"   {BLU}⚠ Nessun nodo disponibile trovato per la richiesta.{RESET}")
        return None, salti
    
    # Viene generato un nuovo target per cercare di trovare un nodo che risolva la richiesta di intervento (il nuovo target sarà S(U+1)Q)
    def genera_nuovo_target(self, target_attuale):
        U = (target_attuale % 100) // 10
        if U < 9: 
            return target_attuale + 10
        return None
        
        

