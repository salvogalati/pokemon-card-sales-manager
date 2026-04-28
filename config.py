import sys
import os

main_db = "pokemon.db"
card_db = "card_database.db"

stock_table = "stock"
sales_table = "sales"
purchase_table = "purchases"

cards_condizioni = ["Mint", "Near Mint", "Excellent", "Good", "Light Played", "Played", "Poor"]
card_condizioni_colors = {
    "Mint": "#3CC6C6",
    "Near Mint": "#8BC34A",
    "Excellent": "#7AA42D",
    "Good": "#FFEB3B",
    "Light Played": "#FFC107",
    "Played": "#D44ED2",
    "Poor": "#FF5722"
}

backup_folder = "backups"


def get_resource_path(filename):
    """
    Ritorna il percorso corretto della risorsa sia in sviluppo che nel bundle PyInstaller.
    """
    if getattr(sys, 'frozen', False):
        # Siamo dentro il bundle PyInstaller
        base_path = sys._MEIPASS
    else:
        # Siamo in sviluppo - ritorna la directory principale dell'applicazione
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, filename)


def get_app_root():
    """
    Ritorna la directory principale dell'applicazione.
    """
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    else:
        return os.path.dirname(os.path.abspath(__file__))
