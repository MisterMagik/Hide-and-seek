from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from logic.game_engine import GameEngine
from ui.login_view import LoginView
from ui.lobby_view import LobbyView
from ui.game_view import GameView
from database import Database

class HideAndSeekApp(App):
    def build(self):
        self.db=Database()
        self.engine = GameEngine()
        self.player_nick = ""
        self.is_host = False
        
        sm = ScreenManager()
        sm.app = self # Umożliwia dostęp do danych aplikacji z widoków
        
        sm.add_widget(LoginView(name='login'))
        sm.add_widget(LobbyView(name='lobby'))
        sm.add_widget(GameView(name='game'))
        
        return sm

if __name__ == '__main__':
    HideAndSeekApp().run()