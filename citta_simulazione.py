import random

# Definisce il messaggio di emergenza che indica l'avvenimento di una situazione anomala in un quartiere della città.
class M_Emergenza():
    def __init__(self, quartiere, descrizione, tempo, gravita):
        self.quartiere = quartiere
        self.descrizione = descrizione
        self.tempo = tempo
        self.gravita = gravita 
    
    def __str__(self):
        return f"EMERGENZA: \n- Descrizione: {self.descrizione} \n- Quartiere di provenienza: {self.quartiere} \n- Momento in cui è avvenuta: {self.tempo}"
        
# Definisce le caratteristiche dei quartieri della città.      
class Quartiere():
    def __init__(self, nome, posizione_id, lam):
        self.nome = nome
        self.posizione_id = posizione_id
        
        self.lam = lam
        self.emergenze_prob = []
        self.tp_emergenza = 0.0
    
        self.storico = []
        
    def __str__(self):
        return f"Quartiere {self.nome}, id: {self.posizione_id}"
            
    # Pianifica il momento in cui avverrà la prossima emergenza, secondo un processo Poisson con parametro lam.
    def pianifica_emergenza(self, ora):
        delta_t = random.expovariate(self.lam)
        self.tp_emergenza = ora + delta_t
        return self.tp_emergenza
    
    # Genera un'emergenza in modo casuale all'interno del quartiere.
    # L'emergenza viene selezionata tra quelle descritte nel file emergenze.csv, pesando la scelta 
    # con la probabilità di realizzazione di ognuna.
    def generazione_emergenza(self, ora):
        descrizioni = []
        pesi = []
        for emergenza in self.emergenze_prob:
            descrizioni.append(emergenza[0])
            pesi.append(emergenza[1])
        descrizione = random.choices(descrizioni, weights=pesi, k=1)[0]
        gravita = random.randint(1, 3)  
        em = M_Emergenza(self, descrizione, ora, gravita)   
        self.storico.append(em)
        self.pianifica_emergenza(ora)
        return em
      

