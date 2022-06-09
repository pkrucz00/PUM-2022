from random import choice, random, sample, shuffle
from dataclasses import dataclass, field
from typing import Dict, List

g_clef_dist = {"a": -6, "h": -5,
               "c1": -4, "d1": -3, "e1": -2, "f1": -1, "g1": 0, "a1": 1, "h1": 2,
               "c2": 3, "d2": 4, "e2": 5, "f2": 6, "g2": 7, "a2": 8, "h2": 9,
               "c3": 10}  # TODO zmienić, kiedy zrobię wczytywanie nutek z pliku konfiguracyjnego
f_clef_dist = {"C_grand": 10, "D_grand": -9, "E_grand": -8,
               "F_grand": -7, "G_grand": -6, "A_grand": -5, "H_grand": -4,
               "c": -3, "d": -2, "e": -1, "f": 0, "g": 1, "a": 2, "h": 3,
               "c1": 4, "d1": 5, "e1": 6}


def get_dist_from_middle(note_name, clef):
    return g_clef_dist.get(note_name) if clef == "g_clef" else f_clef_dist.get(note_name)


@dataclass
class Note:
    name: str
    val: int
    clef: str
    dist_from_middle: int

    def to_dict(self):
        return {"name": self.name, "clef": self.clef, "val": self.val,
                "dist_from_middle": self.dist_from_middle }


def prepare_notes(notes):
    return [Note(name=name, clef=clef,
                 val=RlModel._init_val,
                 dist_from_middle=get_dist_from_middle(name, clef))
            for clef, note_names in notes.items() for name in note_names]


def _compute_new_val(note: Note, was_correct: bool) -> int:
    old_val = note.val
    reward = -1 if was_correct else 1
    return old_val + RlModel._alfa * (reward - old_val)


@dataclass
class RLModelObserver:
    observed: ...
    note_history: List = field(default_factory=lambda: [])
    selected_note_history: List = field(default_factory=lambda: [])
    active_notes_history: List = field(default_factory=lambda: [])
    active_notes_number_history: List = field(default_factory=lambda: [])

    def notify(self):
        self.note_history.append(RLModelObserver.notes_to_dicts(self.observed.notes))
        self.active_notes_history.append(RLModelObserver.notes_to_dicts(self.observed.active_notes))
        self.active_notes_number_history.append(len(self.observed.active_notes))

    def notify_selection(self, selected_note):
        self.selected_note_history.append(selected_note.to_dict())

    @staticmethod
    def notes_to_dicts(note_list):
        return [note.to_dict() for note in note_list]

    def get_state_dict(self):
        return {"note_history": self.note_history,
                "selected_note_history": self.selected_note_history,
                "active_notes_history": self.active_notes_history,
                "active_notes_number_history": self.active_notes_number_history}


class RlModel:
    _epsilon = 0.15
    _alfa = 0.1
    _init_val = 5

    def __init__(self, notes: Dict):
        self._notes = prepare_notes(notes)
        self._active_notes_range = (-2, 2)
        self._active_notes = self._choose_active_notes()

        self._rl_observer: RLModelObserver = RLModelObserver(observed=self)

    @property
    def notes(self):
        return self._notes

    @property
    def active_notes(self):
        return self._active_notes

    def _choose_active_notes(self):
        min_dist_from_middle, max_dist_from_middle = self._active_notes_range
        return [note for note in self._notes
                if min_dist_from_middle <= note.dist_from_middle <= max_dist_from_middle]

    def _get_max_note(self):
        max_val = max([note.val for note in self._active_notes])
        max_notes = [note for note in self._active_notes if note.val == max_val]
        return choice(max_notes)

    def _get_random_note_names(self, already_chosen: str, clef: str):
        possible_notes = [note for note in self._active_notes
                          if note.name != already_chosen and
                          note.clef == clef]
        sampled_notes = sample(possible_notes, 3)
        sampled_notes_names = [note.name for note in sampled_notes]
        sampled_notes_names.append(already_chosen)
        shuffle(sampled_notes_names)
        return sampled_notes_names

    def select_notes(self):
        chosen_note = self._get_max_note() if RlModel._epsilon < random() \
            else choice(self._active_notes)
        clef = chosen_note.clef
        correct_note_name = chosen_note.name
        all_notes_names = self._get_random_note_names(correct_note_name, clef)
        self._rl_observer.notify_selection(chosen_note)
        return correct_note_name, all_notes_names, clef

    def _find_note_by_name(self, note_name: str) -> Note:
        name_list = [note.name for note in self._notes]
        index = name_list.index(note_name)
        return self._notes[index]

    def update_val(self, note_name: str, was_correct: bool):
        if note_name is not None:
            note_to_update = self._find_note_by_name(note_name)
            note_to_update.val = _compute_new_val(note_to_update, was_correct)
            self._rl_observer.notify()

    def add_active_notes(self):
        old_min_range, old_max_range = self._active_notes_range
        self._active_notes_range = (old_min_range - 2, old_max_range + 2)
        self._active_notes = self._choose_active_notes()

    def get_state_dict(self):
        metadata = {"epsilon": self._epsilon, "alfa": self._alfa, "initial_value": self._init_val}
        return {"metadata": metadata,
                "history": self._rl_observer.get_state_dict()}
