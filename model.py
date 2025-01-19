from typing import Optional, List, Union

from pydantic import Field, BaseModel

class Tecnica(BaseModel):
    nome: str = Field(description="Nome della tecnica")
    descrizione: Optional[str] = Field(description="Descrizione della tecnica")
    licenza: Optional[str] = Field(description="Nome della licenza richiesta per usare la tecnica")
    eLeggendaria: Optional[bool] = Field(description="Indica se la tecnica è leggendaria")
#
# class Ingrediente(BaseModel):
#     nome: str = Field(description="Nome dell'ingrediente")
#     descrizione: Optional[str] = Field(description="Descrizione dell'ingrediente")
#     quantita: Optional[str] = Field(description="Quantità dell'ingrediente")
#     unita_di_misura: Optional[str] = Field(description="Unità di misura dell'ingrediente")

class Ristorante(BaseModel):
    nome: str = Field(description="Nome del ristorante")
    descrizione: Optional[str] = Field(description="Descrizione del ristorante")
    leggendario: Optional[bool] = Field(description="Indica se il ristorante è leggendario")
    pianeta: Optional[str] = Field(description="Nome del pianeta in cui si trova il ristorante")

class Ordine(BaseModel):
    nome: str = Field(..., description="Nome dell'ordine")
    descrizione: Optional[str] = Field(None, description="Descrizione estesa dell'ordine")
    principi_fondamentali: Optional[List[str]] = Field(None, description="Elenco di principi fondamentali dell'ordine")
    obiettivo: Optional[str] = Field(None, description="Obiettivo principale dell'ordine")

class Livello(BaseModel):
    livello: Union[str, int] = Field(..., description="Il livello specifico")
    descrizione: Optional[str] = Field(None, description="Descrizione del livello")

class Categoria(BaseModel):
    nome: str = Field(..., description="Nome della categoria di abilità o licenza")
    livelli: List[Livello] = Field(..., description="Elenco dei livelli con descrizioni")

class LicenzeRichieste(BaseModel):
    descrizione_generale: str = Field(
        ...,
        description="Descrizione generale delle abilità e licenze richieste per operare nello spazio"
    )
    categorie: List[Categoria] = Field(..., description="Categorie e livelli delle licenze")

class Chef(BaseModel):
    nome: str = Field(description="Nome del chef")
    specializzazione: Optional[str] = Field(description="Specializzazione del chef")
    licenza: Optional[LicenzeRichieste] = Field(description="Nome della licenza posseduta dal chef")
    ordine: Optional[Ordine] = Field(description="Nome dell'ordine di appartenenza del chef")
    ristorante: Optional[Ristorante] = Field(description="Nome del ristorante in cui lavora il chef")

class Piatto(BaseModel):
    nome: str = Field(description="Nome del piatto")
    descrizione: Optional[str] = Field(description="Descrizione del piatto")
    ingredienti: Optional[list[str]] = Field(description="Lista degli ingredienti")
    tecniche: Optional[list[Tecnica]] = Field(description="Lista delle tecniche usate per preparare il piatto")
    ristorante: Optional[Ristorante] = Field(description="Nome del ristorante in cui il piatto è servito")
    chef: Optional[Chef] = Field(description="Nome del chef che ha preparato il piatto")
    eLeggendario: Optional[bool] = Field(description="Indica se il piatto è leggendario")
    ordine: Optional[Ordine] = Field(description="Nome dell'ordine a cui appartiene il piatto")

class Pianeta(BaseModel):
    nome: str = Field(description="Nome del pianeta")
    descrizione: Optional[str] = Field(description="Descrizione del pianeta")
    categoria: Optional[str] = Field(description="Categoria del pianeta")
    coordinate: Optional[str] = Field(description="Coordinate del pianeta")
    regione: Optional[str] = Field(description="Regione galattica in cui si trova il pianeta")
    galassia: Optional[str] = Field(description="Galassia in cui si trova il pianeta")