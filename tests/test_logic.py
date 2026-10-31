from core.logic import NayEngine, is_question

OWNER, ASKER, TARGET, OTHER = 1, 2, 3, 4


class FakeClock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def make(targets=(TARGET,)):
    clock = FakeClock()
    eng = NayEngine(targets=list(targets), insults=["NAY {name}"],
                    window_sec=600, cooldown_sec=60, clock=clock)
    return eng, clock


def ask(eng, about=OWNER):
    """ASKER replies to `about`'s message (id 10) with a question (id 11)."""
    eng.on_message(1, 11, ASKER, "isnt that just an algorithm",
                   reply_to_msg_id=10, reply_to_sender_id=about)


def test_is_question():
    assert is_question("isnt that just an algorithm")
    assert is_question("u eat already?")
    assert is_question("can or not")
    assert not is_question("yeah it is")


def test_nay_when_target_answers_for_them():
    eng, _ = make()
    ask(eng)
    r = eng.on_message(1, 12, TARGET, "yeah lol",
                       reply_to_msg_id=11, reply_to_sender_id=ASKER, sender_name="Bob")
    assert r == "NAY Bob"


def test_non_target_can_answer():
    eng, _ = make()
    ask(eng)
    assert eng.on_message(1, 12, OTHER, "ya", reply_to_msg_id=11) is None


def test_empty_targets_nays_anyone():
    eng, _ = make(targets=())
    ask(eng)
    assert eng.on_message(1, 12, OTHER, "ya", reply_to_msg_id=11)


def test_protects_everyone():
    eng, _ = make()
    ask(eng, about=OTHER)                      # question about someone else's message
    assert eng.on_message(1, 12, TARGET, "ya", reply_to_msg_id=11)


def test_no_nay_for_out_of_nowhere_question():
    eng, _ = make()
    eng.on_message(1, 20, ASKER, "u eat?")      # not a reply to anyone
    assert eng.on_message(1, 21, TARGET, "he ate", reply_to_msg_id=20) is None


def test_right_person_answers_first_closes_question():
    eng, _ = make()
    ask(eng)
    eng.on_message(1, 12, OWNER, "you pick the topic", reply_to_msg_id=11)
    assert eng.on_message(1, 13, TARGET, "ya", reply_to_msg_id=11) is None


def test_expiry():
    eng, clock = make()
    ask(eng)
    clock.t += 601
    assert eng.on_message(1, 12, TARGET, "ya", reply_to_msg_id=11) is None
