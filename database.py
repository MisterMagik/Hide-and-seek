import requests
import json

# TUTAJ WKLEJ SWÓJ LINK Z FIREBASE (musi kończyć się slashem /)
FIREBASE_URL = "https://TWOJA-NAZWA-PROJEKTU.europe-west1.firebasedatabase.app/"

class Database:
    def __init__(self, game_code=None):
        self.game_code = game_code

    def create_game(self, game_code, host_nick):
        """Tworzy nowy pokój w bazie danych."""
        self.game_code = game_code
        data = {
            "status": "waiting",
            "host": host_nick,
            "players": {
                host_nick: {
                    "lat": 0,
                    "lon": 0,
                    "role": "pending"
                }
            }
        }
        response = requests.put(f"{FIREBASE_URL}games/{game_code}.json", json=data)
        return response.status_code == 200

    def join_game(self, game_code, player_nick):
        """Dodaje gracza do istniejącego pokoju."""
        self.game_code = game_code
        # Najpierw sprawdzamy czy gra istnieje
        check = requests.get(f"{FIREBASE_URL}games/{game_code}.json")
        if check.json() is None:
            return False, "Nie znaleziono takiego kodu gry."

        # Dodajemy gracza
        player_data = {
            "lat": 0,
            "lon": 0,
            "role": "pending"
        }
        response = requests.patch(f"{FIREBASE_URL}games/{game_code}/players/{player_nick}.json", 
                                 json=player_data)
        return response.status_code == 200, "Dołączono!"

    def start_game(self, roles_assignment):
        """Zmienia status gry na 'started' i przypisuje role."""
        # roles_assignment to słownik np: {"Adam": "seeker", "Ewa": "hider"}
        update_data = {
            "status": "started"
        }
        requests.patch(f"{FIREBASE_URL}games/{self.game_code}.json", json=update_data)
        
        for nick, role in roles_assignment.items():
            requests.patch(f"{FIREBASE_URL}games/{self.game_code}/players/{nick}.json", 
                          json={"role": role})

    def update_location(self, player_nick, lat, lon):
        """Wysyła aktualną pozycję GPS gracza do bazy."""
        if not self.game_code: return
        data = {"lat": lat, "lon": lon}
        requests.patch(f"{FIREBASE_URL}games/{self.game_code}/players/{player_nick}.json", 
                      json=data)

    def get_game_state(self):
        """Pobiera wszystkie dane o aktualnej grze (pozycje graczy, status)."""
        if not self.game_code: return None
        response = requests.get(f"{FIREBASE_URL}games/{self.game_code}.json")
        return response.json()

    def get_players(self):
        """Pobiera listę graczy w lobby."""
        state = self.get_game_state()
        if state and "players" in state:
            return state["players"]
        return {}