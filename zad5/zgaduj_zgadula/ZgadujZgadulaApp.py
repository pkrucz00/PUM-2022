from game_model import GameModel

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock

from dataclasses import dataclass, field
from typing import List

from datetime import datetime
from pathlib import Path
from os.path import join


def format_date(datetime: datetime):
    return f"{datetime.strftime('%Y_%m_%dT%H_%M_%S')}"


def save_results(game_state: str, rel_path: str):
    folder_name = "results"
    Path(folder_name).mkdir(parents=True, exist_ok=True)

    result_full_path = f"{join(folder_name, rel_path)}.json"

    with open(result_full_path, "w", encoding="UTF-8") as file:
        file.write(game_state)


@dataclass
class GameState:
    score: int = 0
    score_list: List = field(default_factory=lambda: [])


class ClefSelection(Widget):
    def _get_buttons_down_truth_table(self):
        return [bt.state == "down" for bt in
                (self.ids.g_clef_bt, self.ids.f_clef_bt, self.ids.all_clefs_bt)]

    def get_chosen_clefs(self):
        truth_table = self._get_buttons_down_truth_table()
        possible_results = [("g_clef", ), ("f_clef", ), ("g_clef", "f_clef")]
        for is_bt_down, res in zip(truth_table, possible_results):
            if is_bt_down:
                return res


class Options(Widget):
    clef_selection = ObjectProperty()

    def set_up_game(self, game: GameModel):
        possible_clefs = self.clef_selection.get_chosen_clefs()
        is_rl_picked = self.ids.rl_bt.state == "down"
        game.set_game_config(possible_clefs, is_rl_picked)


class MenuScreen(Screen):
    game = ObjectProperty()
    options = ObjectProperty()

    def go_to_next_panel(self):
        self.options.set_up_game(self.game)
        self.game.initialize_round()
        self.manager.current = 'game'


class AnswersPanel(Widget):
    def get_buttons(self):
        return list(self.children[0].children)  # I hope no one will see that

    def get_selected_note(self):
        selected_buttons = [bt for bt in self.get_buttons() if bt.state == "down"]
        selected_button = selected_buttons[0] if len(selected_buttons) == 1 else None
        return selected_button.text if selected_button else None

    def model_is_changed(self):
        game = self.parent.parent.game   #Good God, what am I doing
        buttons, answers = self.get_buttons(), game.all_answers
        for bt, ans in zip(buttons, answers):
            bt.text = ans
            bt.state = "normal"


class GameScreen(Screen):
    game = ObjectProperty()
    answers_panel = ObjectProperty()

    checked_good_answer = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game.add_observer(self)

    def get_score_label(self):
        return f"Wynik: {self.game.score}"

    def get_check_button_label(self):
        return "Jeszcze raz" if self.game.is_last_answer_correct() else "Sprawdź"

    def get_check_button_callback(self):
        return self.initialize_new_round if self.game.is_last_answer_correct() else self.check_answer

    def get_feedback_label(self):  # For this kind of spaghetti devs go to hell
        if self.game.last_chosen is None:
            return "Zaznacz prawidłową odpowiedź"
        elif self.game.is_last_answer_correct():
            if self.game.should_add_active_notes():
                return "LEVEL UP! Dostajesz nowe nutki do rozpoznania. Czy sprostasz wyzwaniu?"
            return "GRATULACJE! Odgadłeś prawidłowo nutkę\n" \
                   "Naciśnij przycisk 'Jeszcze raz', aby spróbować ponownie"
        else:
            return "Niestety, to nie jest ta nutka. Zaznacz inną odpowiedź"

    def get_image(self):
        return f"src/img/notes/{self.game.current_clef}/{self.game.correct_answer}.png"

    def check_answer(self):
        selected_note = self.answers_panel.get_selected_note()
        self.game.check_answer(selected_note)

    def initialize_new_round(self):
        self.game.initialize_round()
        self.checked_good_answer = False

    def model_is_changed(self):
        self.ids.score_label.text = self.get_score_label()
        self.ids.check_button.text = self.get_check_button_label()
        self.ids.check_button.on_release = self.get_check_button_callback()
        self.ids.feedback.text = self.get_feedback_label()
        self.ids.note_img.source = self.get_image()

        self.answers_panel.model_is_changed()


class EndScreen(Screen):
    game = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game.add_observer(self)

    def get_score_label(self):
        return f"{self.game.score} pkt"

    def save_results(self):
        save_results(self.game.dump_game_state_to_json(), format_date(datetime.now()))
        self.ids.save_button.disabled = True

    def model_is_changed(self):
        self.ids.score_label.text = self.get_score_label()


class ZgadujZgadulaScreen(ScreenManager):
    pass


class ZgadujZgadulaApp(App):
    def build(self):
        game = GameModel()

        screen = ZgadujZgadulaScreen()
        screen.add_widget(MenuScreen(game=game, name="menu"))
        screen.add_widget(GameScreen(game=game, name="game"))
        screen.add_widget(EndScreen(game=game, name="end"))
        return screen


if __name__ == '__main__':
    ZgadujZgadulaApp().run()
