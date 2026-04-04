from kivy.uix.screenmanager import Screen
from kivy.lang import Builder

Builder.load_string("""
<LoginView>:
    BoxLayout:
        orientation: 'vertical'
        padding: [50, 20, 50, 20]
        spacing: 15
        
        Label:
            text: "AUTO-CHOWANY"
            font_size: 40
            size_hint_y: None
            height: 100

        TextInput:
            id: nick_input
            hint_text: "Twój Nick"
            multiline: False
            size_hint_y: None
            height: 50
            padding: [10, 10]

        Button:
            text: "STWÓRZ NOWĄ GRĘ"
            size_hint_y: None
            height: 60
            background_color: (0.2, 0.8, 0.2, 1)
            on_release: root.create_game()
        
        Label:
            text: "--- LUB DOŁĄCZ DO KOGOŚ ---"
            size_hint_y: None
            height: 40

        TextInput:
            id: code_input
            hint_text: "Wpisz 6-cyfrowy kod"
            multiline: False
            size_hint_y: None
            height: 50
            input_filter: 'int'  # Pozwala wpisywać tylko cyfry
            padding: [10, 10]

        Button:
            text: "DOŁĄCZ DO GRY"
            size_hint_y: None
            height: 60
            background_color: (0.2, 0.2, 0.8, 1)
            on_release: root.join_game()
""")

class LoginView(Screen):
    def create_game(self):
        app = self.manager.app
        nick = self.ids.nick_input.text
        if nick.strip():
            app.player_nick = nick
            app.is_host = True
            app.game_code = app.engine.generate_code()
            # Próba połączenia z bazą
            try:
                app.db.create_game(app.game_code, nick)
                self.manager.current = 'lobby'
            except Exception as e:
                print(f"Błąd bazy: {e}")

    def join_game(self):
        app = self.manager.app
        nick = self.ids.nick_input.text
        code = self.ids.code_input.text
        
        if nick.strip() and len(code) == 6:
            app.player_nick = nick
            app.game_code = code
            app.is_host = False
            
            try:
                success, msg = app.db.join_game(code, nick)
                if success:
                    self.manager.current = 'lobby'
                else:
                    print(f"Błąd: {msg}")
            except Exception as e:
                print(f"Błąd połączenia: {e}")