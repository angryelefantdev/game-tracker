import os
import sys
import time
import requests
import sqlite3
from dotenv import load_dotenv


load_dotenv()
API_KEY = os.getenv("RAWG_API_KEY")

if not API_KEY:
    print("Error: RAWG_API_KEY not found in .env file!")
    sys.exit(1)

url = "https://api.rawg.io/api/games"

conn = sqlite3.connect("gametracker.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()



command_1 = """CREATE TABLE IF NOT EXISTS game_database(
id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,release_date VARCHAR(15),rating DECIMAL(2,1),status TEXT DEFAULT 'Plan to Play',developer VARCHAR(20))"""

with conn:
    cursor.execute(command_1)


def main():
    while True:
        try:
            print("=========== GAME TRACKER 1.0 ===========")
            print("OPTIONS:")
            print("1. Search game")
            print("2. My games")
            print("3. Add game")
            print("4. Remove game")
            print("5. Set status")
            print("6. Exit")

            action = input("Choose: ")

            if action in ["1","Search game"]:
                search_game()
            elif action in ["2","My games"]:
                my_games()
            elif action in ["3","Add game"]:
                add_game()
            elif action in ["4","Remove game"]:
                remove_game()
            elif action in ["5","Set status"]:
                setstatus()
            elif action in ["6","Exit"]:
                exit()
            else:
                print("Wrong input: number/action required")

        except ValueError:
            print("Something's wrong.")

 
def search_game():
    game = input("Input the game's name: ").strip()

    command = """SELECT name, release_date, rating, status, developer FROM game_database WHERE name = ?"""

    cursor.execute(command,(game,))

    with conn:
        data = cursor.fetchall()

        if not data:
            print(f"No game named '{game}' found in your database.")
            return
    
        for row in data:
            print(
            f"Name: {row['name']} | Released: {row['release_date']} | "
            f"Rating: {row['rating']} | Status: {row['status']} | Dev: {row['developer']}"
            )
    
    time.sleep(1.5)
  

def my_games():
    command = """SELECT name, release_date, rating, status, developer FROM game_database"""
    with conn:
        cursor.execute(command)
        data = cursor.fetchall()

        if not data:
            print("No games in your library.")
            return

        for row in data:
            print(
            f"Name: {row['name']} | Released: {row['release_date']} | "
            f"Rating: {row['rating']} | Status: {row['status']} | Dev: {row['developer']}"
            )
 

def add_game():
    adder = input("What game do you wish to add? ").strip()

    params = {"key":API_KEY,"search":adder}


    response = requests.get(url,params=params,timeout=20).json()

    print(f"Looking for {adder}...")
    results = response.get("results", [])
    if not results:
        print("No such game exists")
        return
    
    game_id = response["results"][0]["id"]
    details_url = f"https://api.rawg.io/api/games/{game_id}"
    details = requests.get(details_url,params={"key":API_KEY},timeout=20).json()
    developer = [d["name"] for d in details.get("developers",[])]
    developerjoin = ", ".join(developer) if developer else "Unknown"

    name = details.get("name")
    released = details.get("released")
    rating = details.get("rating")

    status = input("Status (Playing / Completed / Wishlist) [Default: Plan to Play]: ").strip()
    if status not in ["Completed", "Wishlist", "Playing"]:
        status = "Plan to Play"

    command = """INSERT INTO game_database (name, release_date, rating, status, developer)
                 VALUES (?, ?, ?, ?, ?)"""

    try:
        with conn:
            cursor.execute(command, (name, released, rating, status, developerjoin))
        print(f"Successfully added '{name}' to your tracker!")
    except sqlite3.Error as e:
        print(f"Database error: {e}")   


def setstatus():
    game = input("Which game do you want to update status for? ").strip()

    cursor.execute("SELECT id FROM game_database WHERE name = ?", (game,))
    if not cursor.fetchone():
        print(f"Game '{game}' not found in your database.")
        return

    status = input("Enter new status (Completed / Wishlist / Playing): ").strip()
    if status not in ["Completed", "Wishlist", "Playing"]:
        print("Wrong input: Completed, Wishlist, or Playing only.")
        return

    command = """UPDATE game_database SET status = ? WHERE name = ?"""

    try:
        with conn:
            cursor.execute(command, (status, game))
        print(f"Successfully updated '{game}' status to '{status}'!")
    except sqlite3.Error as e:
        print(f"Database error: {e}")



def remove_game():
    remover = input("What game do you wish to remove from the library? ").strip()
    command = """DELETE FROM game_database
    WHERE name = ? """
    with conn:
        cursor.execute(command,(remover,))

    if cursor.rowcount > 0:
        print(f"Successfully removed '{remover}'!")
    else:
        print(f"No game named '{remover}' found in your library.")


def exit():
    conn.close()
    sys.exit()


if __name__ == "__main__":
    main()