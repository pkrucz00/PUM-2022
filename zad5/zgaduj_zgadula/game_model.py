from rlmodel import RlModel

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
        self._score_history = [0]
        self._good_guesses_in_row = 0

        self._correct_answer = ""
        self._all_answers = []
        self._last_chosen = None

        self._current_clef = "g_clef"
        self._possible_clefs = ["g_clef", "f_clef"]
        self._question_pick_method = "random"
        self._rl_model: RlModel = None

        self._good_guesses = {}
        self._bad_guesses = {}

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

    def _init_rl_model(self):
        notes_dict = {}
        if "f_clef" in self._possible_clefs:
            notes_dict["f_clef"] = GameModel.f_clef_notes
        if "g_clef" in self._possible_clefs:
            notes_dict["g_clef"] = GameModel.g_clef_notes
        return RlModel(notes_dict)

    def set_game_config(self, possible_clefs, is_rl_picked):
        self._possible_clefs = possible_clefs
        if is_rl_picked:
            self._question_pick_method = "rl"
            self._rl_model = self._init_rl_model()
        else:
            self._question_pick_method = "random"

    def clear_game_data(self):
        self._score = 0
        self._score_history = [0]
        self._good_guesses_in_row = 0

    def increment_score(self):
        self.score = self._score + 1
        self._good_guesses_in_row += 1

    def decrement_score(self):
        self.score = self._score - 1
        self._good_guesses_in_row = 0

    def _get_random_notes(self, clef):
        if clef == "g_clef":
            return sample(self.g_clef_notes, 4)
        elif clef == "f_clef":
            return sample(self.f_clef_notes, 4)

    def select_random_notes(self):
        clef = choice(self._possible_clefs)
        all_notes = self._get_random_notes(clef)
        return choice(all_notes), all_notes, clef

    def initialize_round(self):
        self._correct_answer, self._all_answers, self._current_clef = \
            self._rl_model.select_notes() \
                if self._question_pick_method == "rl" \
                else self.select_random_notes()  # where is inheritance when I need it?
        self._last_chosen = None
        self.notify_observers()


    def _record_guess(self, dictionary, note):
        clef = self._current_clef
        key = f"{note} {clef}"
        dictionary.setdefault(key, 0)
        dictionary[key] += 1

    def _record_good_guess(self, note):
        self._record_guess(self._good_guesses, note)

    def _record_bad_guess(self, note):
        self._record_guess(self._bad_guesses, note)

    def check_if_not_none(self, note):
        if note is not None:
            self.check_answer(note)

    def check_answer(self, note):
        self.last_chosen = note
        if self.is_last_answer_correct():
            self.increment_score()
            self._record_good_guess(note)
        else:
            self.decrement_score()
            self._record_bad_guess(note)

        if self._rl_model:
            self._rl_model.update_val(note, self.is_last_answer_correct())
        if self.should_add_active_notes():
            self._rl_model.add_active_notes()
            self.notify_observers()
            self._good_guesses_in_row = 0

    def should_add_active_notes(self):
        return self._rl_model and self._good_guesses_in_row == 5

    def is_last_answer_correct(self):
        return self.last_chosen == self.correct_answer

    def dump_game_state_to_json(self):
        game_state = {"score_history": self._score_history,
                      "good_guesses": self._good_guesses,
                      "bad_guesses": self._bad_guesses,
                      "question_pick_method": self._question_pick_method,
                      "clefs": self._possible_clefs}
        if self._rl_model:
            rl_history = self._rl_model.get_state_dict()
            game_state.update({"rl_history": rl_history})
        return json.dumps(game_state)

    def add_observer(self, observer):
        self._observers.append(observer)

    def remove_observer(self, observer):
        self._observers.remove(observer)

    def notify_observers(self):
        for x in self._observers:
            x.model_is_changed()
