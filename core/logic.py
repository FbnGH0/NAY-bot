"""
NAY bot core logic (platform-independent).

Rule (protects everyone in the chat):
  1. Person A sends a message.
  2. Person B REPLIES to A's message with a question -> question is "open" (for A).
  3. Person C (on the TARGETS list) REPLIES to that question before A does -> NAY C.

Questions sent out of nowhere (not a reply to someone's message) are ignored,
so anyone can answer them. An empty TARGETS list NAYs anyone.
"""

import random
import re
import time
from dataclasses import dataclass
from pathlib import Path

QUESTION_STARTERS = {
    "what", "why", "how", "when", "where", "who", "which", "whats", "hows",
    "did", "do", "does", "are", "is", "isnt", "isn't", "can", "could",
    "will", "would", "should", "shld", "wld", "isit", "issit", "got",
    "u", "you", "ur", "so",
}


def is_question(text: str) -> bool:
    """Rule-based question check. Swap this for an ML classifier later."""
    t = text.strip().lower()
    if not t:
        return False
    if t.endswith("?"):
        return True
    first = re.split(r"\s+", t)[0].strip(",.!")
    if first in QUESTION_STARTERS:
        return True
    # Singlish-style endings: "can or not", "got or not", "isit"
    return bool(re.search(r"(or not|isit|issit|anot)\W*$", t))


@dataclass
class OpenQuestion:
    asker_id: int      # who asked
    for_id: int        # who the question is for (author of the original message)
    opened_at: float


class NayEngine:
    def __init__(self, targets=None, insults=None,
                 window_sec=600, cooldown_sec=60, clock=time.time):
        self.targets = set(targets or [])      # empty = NAY anyone
        self.insults = insults or ["NAY. Not asking you, {name}."]
        self.window_sec = window_sec
        self.cooldown_sec = cooldown_sec
        self.clock = clock
        self.open = {}            # (chat_id, question_msg_id) -> OpenQuestion
        self.last_nay = {}        # chat_id -> timestamp

    def _cleanup(self):
        now = self.clock()
        self.open = {k: q for k, q in self.open.items()
                     if now - q.opened_at <= self.window_sec}

    def on_message(self, chat_id, msg_id, sender_id, text,
                   reply_to_msg_id=None, reply_to_sender_id=None,
                   sender_name="bro"):
        """Feed every message in. Returns a NAY string, or None.

        reply_to_sender_id should be None if the replied-to message is from a bot.
        """
        self._cleanup()
        key = (chat_id, reply_to_msg_id) if reply_to_msg_id else None

        # Someone replies to an open question
        if key in self.open:
            q = self.open[key]
            if sender_id == q.for_id:
                del self.open[key]               # the right person answered
                return None
            if sender_id == q.asker_id:
                return None                      # asker adding on, fine
            if not self.can_nay(sender_id):
                return None                      # not on the NAY list
            now = self.clock()
            if now - self.last_nay.get(chat_id, 0) < self.cooldown_sec:
                return None                      # cooldown
            del self.open[key]
            self.last_nay[chat_id] = now
            return self.pick_insult(sender_name)

        # Someone asks a question about another person's message -> open it
        if (reply_to_sender_id is not None and reply_to_sender_id != sender_id
                and is_question(text)):
            self.open[(chat_id, msg_id)] = OpenQuestion(
                sender_id, reply_to_sender_id, self.clock())

        return None

    def can_nay(self, user_id):
        """Empty target list = anyone can be NAY'd."""
        return not self.targets or user_id in self.targets

    def pick_insult(self, name):
        return random.choice(self.insults).format(name=name)


def load_insults(path=None):
    path = Path(path or Path(__file__).resolve().parent.parent / "insults.txt")
    if not path.exists():
        return None
    lines = [l.strip() for l in path.read_text(encoding="utf-8").splitlines()]
    return [l for l in lines if l and not l.startswith("#")] or None


def parse_ids(value):
    return [int(x) for x in (value or "").replace(" ", "").split(",") if x]
