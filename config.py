import sys
import os
from enum import Enum

class DBTables(str, Enum):
    STOCK = "stock"
    SALES = "sales"
    PURCHASES = "purchases"
    UNPRICED_CARDS = "unpriced_cards"
    DATABASE_CARDS = "DatabaseCards"
    BOZZE_ACQUISTI = "draft_purchases"

class DBNames(str, Enum):
     MAIN_DB = "pokemon.db"
     CARD_DB = "card_database.db"

class FieldsEnum(str, Enum):
    Quantità = "quantity"
    Nome = "name"
    Espansione = "set"
    Espansione_ID = "setCode"
    Condizione = "condition"
    Lingua = "language"
    Prezzo = "price"
    Barcode = "barcode"
    Prezzo_Vendita = "sale_price"
    Data_Vendita = "sell_date"
    Prezzo_Acquisto = "purchase_price"
    Data_Acquisto = "purchase_date"
    ID_Vendita = "sale_id"
    Da_Prezzare = "to_price"
    Prezzo_acquisto = "purchase_price"
    ID_Acquisto = "purchase_id"
    ID_Carta = "id"
    ID_Bozza_Acquisto = "id_purchase_draft"
    Totale = "total"
    Oggetti = "items"
    Numero_oggetti = "number_of_items"
    ID_Cardmarket = "cardmarketId"
    Prezzo_Valutazione = "estimated_price"
    Numero_Espansione = "collectorNumber"

cards_condizioni = [
    "Mint",
    "Near Mint",
    "Excellent",
    "Good",
    "Light Played",
    "Played",
    "Poor",
]
card_condizioni_colors = {
    "Mint": "#3CC6C6",
    "Near Mint": "#8BC34A",
    "Excellent": "#7AA42D",
    "Good": "#FFEB3B",
    "Light Played": "#FFC107",
    "Played": "#D44ED2",
    "Poor": "#FF5722",
}
card_condizioni_icons = {
    "MT": ":/condizioni/condizioni/Mint.png",
    "NM": ":/condizioni/condizioni/Near Mint.png",
    "EX": ":/condizioni/condizioni/Excellent.png",
    "GD": ":/condizioni/condizioni/Good.png",
    "LP": ":/condizioni/condizioni/Light Played.png",
    "PL": ":/condizioni/condizioni/Played.png",
    "PO": ":/condizioni/condizioni/Poor.png",
}

class FolderNames(str, Enum):
    BACKUPS = "backups"






def get_resource_path(filename):
    """
    Ritorna il percorso corretto della risorsa sia in sviluppo che nel bundle PyInstaller.
    """
    if getattr(sys, "frozen", False):
        # Siamo dentro il bundle PyInstaller
        base_path = sys._MEIPASS
    else:
        # Siamo in sviluppo - ritorna la directory principale dell'applicazione
        base_path = os.path.dirname(os.path.abspath(__file__))

    print(f"Resource path for {filename}: {os.path.join(base_path, filename)}")
    return os.path.join(base_path, filename)


def get_app_root():
    """
    Ritorna la directory principale dell'applicazione.
    """
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    else:
        return os.path.dirname(os.path.abspath(__file__))
