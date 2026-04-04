from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from plyer import gps
import requests
import math

# ZMIEŃ TO NA IP SWOJEGO KOMPUTERA LUB ADRES SERWERA
SERVER_URL = "http://192.168.100.40:5000"

class HideSeekGame(App):
    def build(self):
        self.room_code = ""
        self.nick = ""
        self.my_role = "viewer"
        self.my_pos = (0, 0)
        self.pos_locked = False
        
        self.main_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        self.top_bar = BoxLayout(size_hint_y=None, height='40dp')
        self.status_dot = Label(text="SZUKANIE...", color=(1, 1, 0, 1))
        self.count_label = Label(text="Graczy: 0", halign="right")
        self.top_bar.add_widget(self.status_dot)
        self.top_bar.add_widget(self.count_label)
        self.main_layout.add_widget(self.top_bar)
        
        self.content_area = BoxLayout(orientation='vertical', spacing=15)
        self.show_login_screen()
        self.main_layout.add_widget(self.content_area)
        
        Clock.schedule_interval(self.check_server_health, 3.0)
        return self.main_layout

    def show_login_screen(self):
        self.content_area.clear_widgets()
        self.nick_input = TextInput(hint_text="Nick", multiline=False, size_hint_y=None, height='50dp')
        self.code_input = TextInput(hint_text="Kod Pokoju", multiline=False, size_hint_y=None, height='50dp')
        btn = Button(text="DOŁĄCZ DO GRY", size_hint_y=None, height='60dp', background_color=(0.2, 0.6, 1, 1))
        btn.bind(on_press=self.connect)
        
        self.content_area.add_widget(Label(text="HIDE & SEEK GPS", font_size='24sp', bold=True))
        self.content_area.add_widget(self.nick_input)
        self.content_area.add_widget(self.code_input)
        self.content_area.add_widget(btn)

    def connect(self, instance):
        self.nick, self.room_code = self.nick_input.text.strip(), self.code_input.text.strip()
        if not self.nick or not self.room_code: return
        try:
            res = requests.post(f"{SERVER_URL}/join", json={"room_code": self.room_code, "nick": self.nick}, timeout=3)
            if res.status_code == 200:
                self.show_lobby_screen()
                Clock.schedule_interval(self.game_tick, 1.0)
                try:
                    # WYMUSZAMY WYSOKĄ DOKŁADNOŚĆ: minTime=1s, minDistance=0m
                    gps.configure(on_location=self.on_gps)
                    gps.start(minTime=1000, minDistance=0)
                except: print("GPS nieobsługiwany na tym urządzeniu")
        except: print("Błąd połączenia")

    def show_lobby_screen(self, msg="Kliknij GOTOWY"):
        self.content_area.clear_widgets()
        self.pos_locked = False
        self.content_area.add_widget(Label(text=f"POKÓJ: {self.room_code}", font_size='20sp'))
        
        self.btn_action = Button(text="GOTOWY", size_hint_y=None, height='70dp', background_color=(0.2, 0.8, 0.2, 1))
        self.btn_action.bind(on_press=self.send_ready)
        
        btn_leave = Button(text="OPUŚĆ", size_hint_y=None, height='50dp', background_color=(1, 0.2, 0.2, 1))
        btn_leave.bind(on_press=self.leave_room)
        
        self.status_msg = Label(text=msg, halign="center")
        self.content_area.add_widget(self.btn_action)
        self.content_area.add_widget(btn_leave)
        self.content_area.add_widget(self.status_msg)

    def on_gps(self, **kwargs):
        self.my_pos = (kwargs['lat'], kwargs['lon'])

    def game_tick(self, dt):
        try:
            res = requests.post(f"{SERVER_URL}/update", json={
                "room_code": self.room_code, "nick": self.nick,
                "lat": self.my_pos[0], "lon": self.my_pos[1]
            }, timeout=1)
            
            data = res.json()
            self.count_label.text = f"Graczy: {len(data['players'])}"
            
            if data["status"] == "lobby" and self.my_role != "viewer":
                self.my_role = "viewer"
                self.show_lobby_screen("RUNDA ZAKOŃCZONA")
                return

            me = data["players"][self.nick]
            self.my_role = me["role"]

            if data["status"] == "playing":
                if self.my_role == "hider":
                    if not self.pos_locked:
                        self.btn_action.text = "ZAPISZ POZYCJĘ"
                        self.btn_action.unbind(on_press=self.send_ready)
                        self.btn_action.bind(on_press=self.lock_my_position)
                    else:
                        self.status_msg.text = "ZŁAPANY! ❌" if me["found"] else "UKRYTY 🛡️"
                elif self.my_role == "seeker":
                    self.btn_action.text, self.btn_action.disabled = "SZUKASZ!", True
                    # Logika radaru analogiczna do JS...
        except: pass

    def send_ready(self, _):
        requests.post(f"{SERVER_URL}/ready", json={"room_code": self.room_code, "nick": self.nick})
        self.btn_action.disabled = True

    def lock_my_position(self, _):
        requests.post(f"{SERVER_URL}/lock_position", json={"room_code": self.room_code, "nick": self.nick})
        self.pos_locked = True
        self.btn_action.disabled = True

    def check_server_health(self, dt):
        try:
            res = requests.get(f"{SERVER_URL}/health", timeout=1)
            self.status_dot.color = (0, 1, 0, 1) if res.status_code == 200 else (1, 0, 0, 1)
        except: self.status_dot.color = (1, 0, 0, 1)

    def leave_room(self, _):
        requests.post(f"{SERVER_URL}/leave", json={"room_code": self.room_code, "nick": self.nick})
        self.room_code = ""
        self.show_login_screen()

    def on_stop(self):
        try: gps.stop()
        except: pass

if __name__ == '__main__':
    HideSeekGame().run()