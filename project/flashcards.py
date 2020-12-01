import json
import sys
from datetime import datetime
from io import StringIO
from pathlib import Path
from random import choices
from argparse import ArgumentParser


DECK_T = dict[str, dict[str, str | int]]


class Logger:
    def __init__(self) -> None:
        self.buffer = StringIO()

    def write(self, string: object, show=False, out=True) -> None:
        """Writes to `buffer` and prints to stdout if `show` is `True`"""
        if not string:
            return
        if show:
            print(string)
        _out, _in = "\u21A9", "\u21AA"  # chars for ↩ and ↪

        timestamp = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
        self.buffer.write(f"{timestamp} {_out if out else _in} {str(string).strip()}\n")

    def write_in(self, __prompt: object) -> str:
        """Writes to `buffer` and reads a string from `sys.stdin`"""
        self.write(__prompt, show=True)
        return input()

    def read(self) -> str:
        """Wrapper to read `buffer` from the start of the stream"""
        self.buffer.seek(0)
        return self.buffer.read()


class Flashcards:
    def __init__(self):
        self.deck: DECK_T = {}

    @staticmethod
    def json_file(filename: Path) -> DECK_T:
        with filename.open() as f:
            return json.load(f) if filename.stat().st_size > 0 else {}

    def load(self, filename: str = None) -> str:
        file: Path = Path(filename) if filename else Path(logger.write_in("Filename:"))
        logger.write(file.name, out=False)
        if file.exists():
            _json = self.json_file(file)
            self.deck |= _json
            return f"{len(_json)} cards have been loaded.\n"
        return "File not found."

    def export(self, filename: str = None) -> str:
        file: Path = Path(filename) if filename else Path(logger.write_in("Filename:"))
        logger.write(file.name, out=False)
        if not file.is_file():  # if `file` doesn't exist
            file.touch()  # , create it.
        loaded_dict: DECK_T = self.json_file(file) | self.deck
        with file.open("w") as f:
            json.dump(loaded_dict, f, indent=4)
        return f"{len(self.deck)} cards have been saved.\n"

    def remove(self) -> str:
        item = logger.write_in("Which card?")
        logger.write(item, out=False)
        return (
            "The card has been removed.\n"
            if self.deck.pop(item, None) is not None
            else f"Can't remove {item!r}: there is no such card.\n"
        )

    def add(self) -> str:
        while (card := logger.write_in("Card:")) in self.deck:
            logger.write(f"The card {card!r} already exists.", show=True)
        logger.write(card, out=False)
        while (definition := logger.write_in("Definition:")) in [
            item["definition"] for item in self.deck.values()
        ]:
            logger.write(f"The definition {definition!r} already exists.", show=True)
        logger.write(definition, out=False)
        self.deck[card] = {"definition": definition, "mistakes": 0}
        return f"The pair ({card!r}:{definition!r}) has been added.\n"

    def test_answer(self, card: str, guess: str) -> str:
        if self.deck[card]["definition"] == guess:
            return "Correct!"
        wrong_right_answer = tuple(
            key for key, v in self.deck.items() if v["definition"] == guess
        )
        self.deck[card]["mistakes"] += 1
        return (
            (
                f"Wrong. The right answer is {self.deck[card]['definition']!r}, "
                f"but your definition is correct for {wrong_right_answer[0]!r}\n"
            )
            if wrong_right_answer
            else f"Wrong. The right answer is {self.deck[card]['definition']!r}\n"
        )

    def ask(self) -> str | None:
        if not self.deck:
            return "There are no cards in the deck.\n"
        times: int = int(logger.write_in("How many times?"))
        logger.write(times, out=False)
        items: list[str] = choices(tuple(self.deck), k=times)
        for card in items:
            guess: str = logger.write_in(f"Input the definition of {card}")
            logger.write(self.test_answer(card, guess), show=True)

    def hardest_card(self) -> str:
        if not any(item["mistakes"] for item in self.deck.values()):
            return "There are no cards with errors.\n"
        max_val = max(card["mistakes"] for card in self.deck.values())
        cards = tuple(
            repr(card) for card in self.deck if self.deck[card]["mistakes"] == max_val
        )
        more_than_one = len(cards) > 1
        return (  # This is really ugly :)
            f"The hardest card{'s' if more_than_one else ''} "
            f"{'are' if more_than_one else 'is'} {', '.join(cards)}. You have {max_val} errors answering {'them' if more_than_one else 'it'}.\n"
        )

    def reset_stats(self) -> str:
        for card in self.deck:
            self.deck[card]["mistakes"] = 0
        return "Card statistics have been reset.\n"

    def exit(self, __status: object = ...) -> None:
        if args.export_to:
            logger.write(self.export(args.export_to), show=True)
        logger.write("Bye bye", show=True)
        sys.exit(__status)

    @staticmethod
    def log() -> str:
        """Reads from `logger.buffer` and outputs to a file."""
        file: Path = Path(logger.write_in("File name:"))
        with file.open(mode="w") as f:
            logger.write(file.name, out=False)
            f.write(logger.read())
        return "The log has been saved.\n"


if __name__ == "__main__":
    logger = Logger()
    deck = Flashcards()
    parser = ArgumentParser(usage="Flashcards")
    for command in ("--import_from", "--export_to"):
        parser.add_argument(command)
    args = parser.parse_args()
    if args.import_from:
        logger.write(deck.load(args.import_from), show=True)
    options: dict[str, callable] = {
        "add": deck.add,
        "remove": deck.remove,
        "import": deck.load,
        "export": deck.export,
        "ask": deck.ask,
        "exit": deck.exit,
        "log": deck.log,
        "hardest card": deck.hardest_card,
        "reset stats": deck.reset_stats,
    }
    while True:
        action = logger.write_in(f"Input one of these actions: ({', '.join(options)}):")
        logger.write(action, out=False)
        logger.write(options.get(action, lambda: "Unknown option")(), show=True)
