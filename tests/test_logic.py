from core.logic import NayEngine, is_question

OWNER, ASKER, INTERCEPTOR, OTHER = 1, 2, 3, 4


class FakeClock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def make(targets=None):
    clock = FakeClock()
    eng = NayEngine(OWNER, targets=targets, insults=["NAY {name}"],
                    window_sec=600, cooldown_sec=60, clock=clock)
    return eng, clock


def test_is_question():
    assert is_question("isnt that just an algorithm")
    assert is_question("u eat already?")
    assert is_question("can or not")
    assert not is_question("yeah it is")


def test_nay_when_someone_answers_for_owner():
    eng, _ = make()
    eng.on_message(1, 10, OWNER, "doomscroll but more personalised")
    eng.on_message(1, 11, ASKER, "isnt that just an algorithm",
                   reply_to_msg_id=10, reply_to_sender_id=OWNER)
    r = eng.on_message(1, 12, INTERCEPTOR, "yeah lol",
                       reply_to_msg_id=11, reply_to_sender_id=ASKER, sender_name="Bob")
    assert r == "NAY Bob"


def test_no_nay_for_out_of_nowhere_question():
    eng, _ = make()
    eng.on_message(1, 20, ASKER, "fabian u eat?")          # not a reply to owner
    r = eng.on_message(1, 21, INTERCEPTOR, "he ate",
                       reply_to_msg_id=20, reply_to_sender_id=ASKER)
    assert r is None


def test_owner_answers_first_closes_question():
    eng, _ = make()
    eng.on_message(1, 11, ASKER, "how?", reply_to_msg_id=10, reply_to_sender_id=OWNER)
    eng.on_message(1, 12, OWNER, "you pick the topic", reply_to_msg_id=11)
    r = eng.on_message(1, 13, INTERCEPTOR, "ya", reply_to_msg_id=11)
    assert r is None


def test_targets_filter():
    eng, _ = make(targets=[INTERCEPTOR])
    eng.on_message(1, 11, ASKER, "how?", reply_to_msg_id=10, reply_to_sender_id=OWNER)
    assert eng.on_message(1, 12, OTHER, "like this", reply_to_msg_id=11) is None
    assert eng.on_message(1, 13, INTERCEPTOR, "like this", reply_to_msg_id=11)


def test_expiry():
    eng, clock = make()
    eng.on_message(1, 11, ASKER, "how?", reply_to_msg_id=10, reply_to_sender_id=OWNER)
    clock.t += 601
    assert eng.on_message(1, 12, INTERCEPTOR, "ya", reply_to_msg_id=11) is None
