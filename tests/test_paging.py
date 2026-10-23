from live_caption.paging import Paginator


def fake_measure(text: str) -> int:
    return len(text) * 10  # 10 px per character


def make(max_width=100):
    return Paginator(fake_measure, max_width)


def test_words_that_fit_stay_on_one_page():
    assert make(100).newest_page(["hi", "there"]) == ["hi", "there"]


def test_new_page_starts_when_next_word_does_not_fit():
    # "aaaa bbbb" = 40 + 10 + 40 = 90 px; "cccc" would need 50 more -> new page
    assert make(100).newest_page(["aaaa", "bbbb", "cccc"]) == ["cccc"]


def test_line_fills_before_paging():
    assert make(110).newest_page(["aa", "bb", "cc", "dd"]) == ["aa", "bb", "cc", "dd"]


def test_empty_input():
    assert make().newest_page([]) == []


def test_single_oversized_word_is_kept():
    assert make(30).newest_page(["extraordinarily"]) == ["extraordinarily"]


def test_cache_is_reused():
    calls = []

    def counting(text):
        calls.append(text)
        return len(text) * 10

    p = Paginator(counting, 100)
    p.word_width("hello")
    p.word_width("hello")
    assert calls.count("hello") == 1
