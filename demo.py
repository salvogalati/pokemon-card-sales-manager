import sqlite3
import pandas as pd
from datetime import datetime

class C:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    END = "\033[0m"

def print_menu(commands):
    print(C.CYAN + "\n====================================================")
    print("  Gestionale Vendita Carte Pokémon by Kingdom Cards ".upper())
    print("====================================================" + C.END)

    for i, (name, _) in enumerate(commands):
        print(f"{C.BLUE}{i+1}{C.END} - {name}")

    print()

def get_card(cursor, card_id):
    cursor.execute("""
        SELECT id, nome_completo, prezzo_eur, quantita_stock
        FROM stock
        WHERE id = ?
    """, (card_id,))
    return cursor.fetchone()


def sell_cart(df_cart):
    with sqlite3.connect("pokemon.db", timeout=10) as conn:
        cursor = conn.cursor()

        for _, row in df_cart.iterrows():
            sell_date = datetime.now().isoformat(sep=" ")

            cursor.execute("""
                INSERT INTO sell (id, nome_completo, prezzo_eur, sell_date)
                VALUES (?, ?, ?, ?)
            """, (row["id"], row["nome_completo"], row["prezzo_eur"], sell_date))

            cursor.execute("""
                UPDATE stock
                SET quantita_stock = quantita_stock - 1
                WHERE id = ?
            """, (row["id"],))

        conn.commit()

def remove_from_cart(df_cart, card_id):
    """
    Rimuove una carta dal carrello (DataFrame pandas).
    Rimuove solo la prima occorrenza.
    """

    if df_cart.empty:
        return df_cart, "Carrello vuoto"

    # verifica presenza
    mask = df_cart["id"] == card_id

    if not mask.any():
        return df_cart, "Carta non presente nel carrello"

    # rimuove la prima occorrenza
    idx_to_remove = df_cart[mask].index[0]
    df_cart = df_cart.drop(idx_to_remove).reset_index(drop=True)

    return df_cart, "Carta rimossa"


def print_recap(df_cart):
    if df_cart.empty:
        print(C.YELLOW + "\nCarrello vuoto\n" + C.END)
        return

    print(C.HEADER + "\n----- RECAP CARRELLO -----" + C.END)

    print(f"{'ID':<12} {'NOME':<25} {'PREZZO'}")
    print("-" * 50)

    for _, row in df_cart.iterrows():
        print(f"{row['id']:<12} {row['nome_completo']:<25} €{row['prezzo_eur']}")

    totale = df_cart["prezzo_eur"].sum()

    print("-" * 50)
    print(C.GREEN + f"TOTALE: €{totale}" + C.END)


def cmd_add():
    card_id = input("ID carta: ")
    card = get_card(cursor, card_id)

    if card is None:
        print(C.RED + "Carta non trovata" + C.END)
        return

    id_, nome, prezzo, qty = card

    if df_cart[df_cart["id"] == id_].shape[0] >= qty:
        print(C.YELLOW + "Stock insufficiente per la carta selezionata" + C.END)
        return

    df_cart.loc[len(df_cart)] = [id_, nome, prezzo]
    print(C.GREEN + f"Aggiunta: {nome}" + C.END)


def cmd_recap():
    print_recap(df_cart)


def cmd_confirm():
    if df_cart.empty:
        print(C.YELLOW + "Carrello vuoto" + C.END)
        return

    sell_cart(df_cart)
    print(C.GREEN + "Vendita completata" + C.END)

    df_cart.drop(df_cart.index, inplace=True)


def cmd_cancel():
    df_cart.drop(df_cart.index, inplace=True)
    print(C.YELLOW + "Vendita annullata" + C.END)


def cmd_remove():
    card_id = input("ID carta: ")
    global df_cart
    df_cart, msg = remove_from_cart(df_cart, card_id)
    print(msg)


def cmd_exit():
    print(C.CYAN + "\n\nSalvataggio Dati...\nChiusura gestionale..." + C.END)
    exit()

commands = [
    ("Aggiungi carta al carrello", cmd_add),
    ("Mostra carrello", cmd_recap),
    ("Conferma vendita", cmd_confirm),
    ("Svuota carrello", cmd_cancel),
    ("Rimuovi carta", cmd_remove),
    ("Esci", cmd_exit)
]

# ---------------- CLI ----------------

df_cart = pd.DataFrame(columns=["id", "nome_completo", "prezzo_eur"])
run_index = 0
import os
with sqlite3.connect("pokemon.db", timeout=10) as conn:
    cursor = conn.cursor()

    while True:
        if run_index >= 1:
            input("\n\nPremi qualsiasi tasto per tornare al menù")
            os.system('cls' if os.name == 'nt' else 'clear')
        print_menu(commands)

        cmd = input("Digita la funzione desiderata >> ")

        if not cmd.isdigit():
            print(C.RED + "Comando non valido" + C.END)
            continue

        idx = int(cmd) - 1

        if 0 <= idx < len(commands):
            commands[idx][1]()   # chiama la funzione
        else:
            print(C.RED + "Comando non valido" + C.END)
        run_index +=1