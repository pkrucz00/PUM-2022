from random import choice, sample
import json

class GameModel:
    g_clef_notes = ["a", "h",
                     "c1", "d1", "e1", "f1", "g1", "a1", "h1",
                     "c2", "d2", "e2", "f2", "g2", "a2", "h2", "c3"]
    f_clef_notes = ["C_grand", "D_grand", "E_grand", "F_grand", "G_grand", "A_grand", "H_grand",
                    "c", "d", "e", "f", "g", "a", "h",
                    "c1", "d1", "e1"]

    def __init__(self):
        self._score = 0
        self._score_history = []

        self._correct_answer = ""
        self._all_answers = []
        self._last_chosen = None

        self._current_clef = "g_clef"
        self._possible_clefs = ["g_clef", "f_clef"]
        self._question_pick_method = "random"

        self._observers = []

    @property
    def score(self):
        return self._score

    @property
    def correct_answer(self):
        return self._correct_answer

    @property
    def all_answers(self):
        return self._all_answers

    @property
    def last_chosen(self):
        return self._last_chosen

    @property
    def current_clef(self):
        return self._current_clef

    @property
    def score_history(self):
        return self._score_history

    @property
    def question_pick_model(self):
        return self._question_pick_method

    @score.setter
    def score(self, value):
        self._score = value
        self._score_history.append(value)
        self.notify_observers()

    @correct_answer.setter
    def correct_answer(self, val):
        self._correct_answer = val

    @last_chosen.setter
    def last_chosen(self, val):
        self._last_chosen = val
        self.notify_observers()

    def set_game_config(self, possible_clefs, is_rl_picked):
        self._possible_clefs = possible_clefs
        self._question_pick_method = "rl" if is_rl_picked else "random"

    def increment_score(self):
        self.score = self._score + 1

    def decrement_score(self):
        self.score = self._score - 1

    def _get_random_notes(self):
        clef = self._current_clef
        if clef == "g_clef":
            return sample(self.g_clef_notes, 4)
        elif clef == "f_clef":
            return sample(self.f_clef_notes, 4)

    def initialize_round(self):
        self._current_clef = choice(self._possible_clefs)
        self._all_answers = self._get_random_notes()   # TODO add possibility of RL choosing
        self._correct_answer = choice(self._all_answers)
        self._last_chosen = None
        self.notify_observers()

    def check_answer(self, note):
        self.last_chosen = note
        if self.is_last_answer_correct():
            self.increment_score()
        else:
            self.decrement_score()

    def is_last_answer_correct(self):
        return self.last_chosen == self.correct_answer

    def dump_game_state_to_json(self):
        game_state = {"score_history": self._score_history,
                      "question_pick_method": self._question_pick_method,
                      "clefs": self._possible_clefs}
        return json.dumps(game_state)

    def add_observer(self, observer):
        self._observers.append(observer)

    def remove_observer(self, observer):
        self._observers.remove(observer)

    def notify_observers(self):
        for x in self._observers:
            x.model_is_changed()

