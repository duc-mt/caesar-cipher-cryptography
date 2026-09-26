"""Tests for the pure cipher logic: is_valid_message(), encrypt(),
decrypt(), brute_force(), random_offset().

None of these do any I/O, so they're tested directly with no mocking.
"""

from __future__ import annotations

import main


class TestIsValidMessage:
    def test_ordinary_text_is_valid(self):
        assert main.is_valid_message("The rabbit has sprung.") is True

    def test_empty_string_is_valid(self):
        assert main.is_valid_message("") is True

    def test_boundary_characters_are_valid(self):
        assert main.is_valid_message(chr(32) + chr(126)) is True

    def test_out_of_range_characters_are_invalid(self):
        for bad in [chr(31), chr(127), "\t", "\n", "\U0001f600"]:
            assert main.is_valid_message(f"hello{bad}world") is False


class TestRandomOffset:
    def test_is_always_within_range(self):
        for _ in range(500):
            offset = main.random_offset()
            assert main.ASCII_MIN <= offset <= main.ASCII_MAX

    def test_is_not_a_constant(self):
        offsets = {main.random_offset() for _ in range(50)}
        assert len(offsets) > 1


class TestEncryptDecrypt:
    def test_matches_the_documented_worked_example_for_encrypt(self):
        # From the README's own "Encryption Process" section: offset 1
        # turns 'abG' into 'bcH'.
        assert main.encrypt("abG", 1) == "bcH"

    def test_wraps_around_past_126(self):
        # From the README's own worked example: offset 4 on '}' (125)
        # should wrap to '"' (34).
        assert main.encrypt("}", 4) == '"'

    def test_matches_the_documented_worked_example_for_decrypt(self):
        # From the README's own "Decryption Process" section: offset 4
        # on '!' (33) should wrap to '|' (124).
        assert main.decrypt("!", 4) == "|"

    def test_encrypt_no_longer_appends_the_offset(self):
        """Regression test for the key/ciphertext separation: the
        original version appended the offset as the last character of
        the ciphertext itself, so anyone with the ciphertext
        automatically had the key too."""
        assert len(main.encrypt("hi", 50)) == len("hi")

    def test_round_trip_every_valid_character_every_offset(self):
        alphabet = [chr(i) for i in range(main.ASCII_MIN, main.ASCII_MAX + 1)]
        for offset in range(main.ASCII_MIN, main.ASCII_MAX + 1):
            for char in alphabet:
                assert main.decrypt(main.encrypt(char, offset), offset) == char

    def test_round_trip_a_realistic_message(self):
        message = "The rabbit has sprung."
        for offset in (main.ASCII_MIN, 79, main.ASCII_MAX):
            ciphertext = main.encrypt(message, offset)
            assert main.decrypt(ciphertext, offset) == message

    def test_wrong_offset_does_not_recover_the_original(self):
        message = "The rabbit has sprung."
        ciphertext = main.encrypt(message, 50)
        assert main.decrypt(ciphertext, 51) != message


class TestBruteForce:
    def test_returns_one_candidate_per_possible_offset(self):
        results = main.brute_force("anything")
        assert len(results) == main.ALPHABET_SIZE

    def test_covers_every_offset_in_range(self):
        results = main.brute_force("anything")
        offsets = [offset for offset, _candidate in results]
        assert offsets == list(range(main.ASCII_MIN, main.ASCII_MAX + 1))

    def test_the_correct_offset_is_among_the_candidates(self):
        message = "The rabbit has sprung."
        ciphertext = main.encrypt(message, 90)
        candidates = dict(main.brute_force(ciphertext))
        assert candidates[90] == message
