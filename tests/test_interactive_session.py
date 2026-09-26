"""Integration tests for main.run_interactive(): full menu-driven
sessions exercising the whole 7-option menu.
"""

from __future__ import annotations

from unittest import mock

import main


def run(inputs: list[str]) -> None:
    with mock.patch("builtins.input", side_effect=inputs):
        main.run_interactive()


class TestFullSession:
    def test_enter_encrypt_decrypt_quit_recovers_the_original(self, capsys):
        run(["1", "The rabbit has sprung.", "3", "50", "4", "", "7"])

        out = capsys.readouterr().out
        assert "Key (offset): 50" in out
        assert "'The rabbit has sprung.'" in out
        assert "Goodbye" in out

    def test_quitting_immediately_prints_goodbye_with_no_message(self, capsys):
        run(["7"])
        out = capsys.readouterr().out
        assert "Goodbye" in out
        assert "Your message is:" not in out.split("Goodbye")[0]

    def test_encrypting_before_entering_a_message_shows_an_error(self, capsys):
        run(["3", "7"])
        out = capsys.readouterr().out
        assert "Cannot encrypt an empty message" in out

    def test_invalid_message_never_reaches_encryption(self, capsys):
        run(["1", "bad\tinput", "3", "7"])
        out = capsys.readouterr().out
        assert "printable ASCII" in out
        assert "Cannot encrypt an empty message" in out

    def test_decrypting_after_entering_a_new_message_forgets_the_old_key(self, capsys):
        """Regression-guarding test: option_encrypt()'s known offset
        must not leak into a decrypt attempted after the working
        message was replaced by something else (e.g. a freshly
        entered message) - entering '1' must reset it."""
        run(
            [
                "1",
                "first message",
                "3",
                "50",  # encrypt with offset 50
                "1",
                "second message",  # overwrite the message
                "4",
                "99",  # must require typing an offset now
                "7",
            ]
        )
        out = capsys.readouterr().out
        # The decrypt prompt must NOT have offered offset 50 as a
        # default once the message changed.
        assert "[Enter for 50]" not in out.split("second message")[1]

    def test_brute_force_end_to_end(self, capsys):
        run(["1", "hi", "3", "50", "5", "7"])
        out = capsys.readouterr().out
        assert "offset  50: 'hi'" in out

    def test_save_and_load_round_trip(self, capsys, tmp_path):
        path = str(tmp_path / "msg.txt")
        run(
            [
                "1",
                "The rabbit has sprung.",
                "6",
                path,
                "1",
                "overwritten",
                "2",
                path,
                "7",
            ]
        )
        out = capsys.readouterr().out
        assert "'The rabbit has sprung.'" in out
