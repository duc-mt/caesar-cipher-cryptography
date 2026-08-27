"""Tests for the interactive menu functions: validate_option() and
each option_*() function.
"""

from __future__ import annotations

from unittest import mock

import main


class TestValidateOption:
    def test_accepts_a_valid_integer(self):
        with mock.patch('builtins.input', return_value='3'):
            assert main.validate_option() == 3

    def test_rejects_non_numeric_then_accepts_valid(self, capsys):
        with mock.patch('builtins.input', side_effect=['abc', '1']):
            assert main.validate_option() == 1
        assert 'Invalid choice' in capsys.readouterr().out

    def test_rejects_out_of_range_then_accepts_valid(self, capsys):
        with mock.patch('builtins.input', side_effect=['99', '7']):
            assert main.validate_option() == 7
        assert 'Invalid choice' in capsys.readouterr().out

    def test_accepts_up_to_the_new_menu_size(self):
        with mock.patch('builtins.input', return_value='7'):
            assert main.validate_option() == 7


class TestOptionEnterMessage:
    def test_valid_message_is_accepted(self):
        with mock.patch('builtins.input', return_value='hello world'):
            assert main.option_enter_message() == 'hello world'

    def test_empty_input_returns_empty_string(self, capsys):
        with mock.patch('builtins.input', return_value=''):
            result = main.option_enter_message()
        assert result == ''
        assert 'Error' not in capsys.readouterr().out

    def test_invalid_characters_are_rejected(self, capsys):
        with mock.patch('builtins.input', return_value='bad\ttab'):
            result = main.option_enter_message()
        assert result == ''
        assert 'printable ASCII' in capsys.readouterr().out


class TestOptionLoadFile:
    def test_loads_a_valid_file(self, tmp_path):
        path = tmp_path / 'msg.txt'
        path.write_text('hello world')

        with mock.patch('builtins.input', return_value=str(path)):
            assert main.option_load_file() == 'hello world'

    def test_missing_file_reports_an_error(self, capsys, tmp_path):
        with mock.patch(
            'builtins.input', return_value=str(tmp_path / 'nope.txt')
        ):
            result = main.option_load_file()
        assert result == ''
        assert 'could not read' in capsys.readouterr().out

    def test_invalid_characters_in_file_are_rejected(self, capsys, tmp_path):
        path = tmp_path / 'bad.txt'
        path.write_text('hello\tworld')

        with mock.patch('builtins.input', return_value=str(path)):
            result = main.option_load_file()
        assert result == ''
        assert 'printable ASCII' in capsys.readouterr().out

    def test_non_utf8_file_reports_an_error(self, capsys, tmp_path):
        path = tmp_path / 'binary.txt'
        path.write_bytes(b'\xff\xfe\x00\x01')

        with mock.patch('builtins.input', return_value=str(path)):
            result = main.option_load_file()
        assert result == ''
        assert 'not a text file' in capsys.readouterr().out


class TestOptionEncrypt:
    def test_empty_message_is_rejected(self, capsys):
        result, offset = main.option_encrypt('')
        assert result == ''
        assert offset is None
        assert 'Error' in capsys.readouterr().out

    def test_blank_offset_input_generates_a_random_one(self):
        with mock.patch('builtins.input', return_value=''), \
             mock.patch('main.random_offset', return_value=50):
            ciphertext, offset = main.option_encrypt('hi')
        assert offset == 50
        assert ciphertext == main.encrypt('hi', 50)

    def test_a_specific_offset_can_be_chosen(self):
        with mock.patch('builtins.input', return_value='60'):
            ciphertext, offset = main.option_encrypt('hi')
        assert offset == 60
        assert ciphertext == main.encrypt('hi', 60)

    def test_out_of_range_offset_falls_back_to_random(self, capsys):
        with mock.patch('builtins.input', return_value='999'), \
             mock.patch('main.random_offset', return_value=50):
            ciphertext, offset = main.option_encrypt('hi')
        assert offset == 50
        assert 'out of range' in capsys.readouterr().out

    def test_non_numeric_offset_falls_back_to_random(self, capsys):
        with mock.patch('builtins.input', return_value='abc'), \
             mock.patch('main.random_offset', return_value=50):
            ciphertext, offset = main.option_encrypt('hi')
        assert offset == 50
        assert 'Invalid offset' in capsys.readouterr().out

    def test_ciphertext_does_not_contain_the_key_appended(self):
        with mock.patch('builtins.input', return_value='50'):
            ciphertext, offset = main.option_encrypt('hi')
        assert len(ciphertext) == len('hi')


class TestOptionDecrypt:
    def test_empty_ciphertext_is_rejected(self, capsys):
        result = main.option_decrypt('')
        assert result == ''
        assert 'Error' in capsys.readouterr().out

    def test_blank_input_uses_the_known_offset(self):
        ciphertext = main.encrypt('hi', 50)
        with mock.patch('builtins.input', return_value=''):
            result = main.option_decrypt(ciphertext, known_offset=50)
        assert result == 'hi'

    def test_manually_entered_offset_is_used_over_the_known_one(self):
        ciphertext = main.encrypt('hi', 60)
        with mock.patch('builtins.input', return_value='60'):
            result = main.option_decrypt(ciphertext, known_offset=50)
        assert result == 'hi'

    def test_no_known_offset_requires_a_typed_value(self):
        ciphertext = main.encrypt('hi', 60)
        with mock.patch('builtins.input', return_value='60'):
            result = main.option_decrypt(ciphertext, known_offset=None)
        assert result == 'hi'

    def test_reprompts_on_invalid_offset(self, capsys):
        ciphertext = main.encrypt('hi', 60)
        with mock.patch(
            'builtins.input', side_effect=['abc', '999', '60']
        ):
            result = main.option_decrypt(ciphertext)
        assert result == 'hi'
        assert capsys.readouterr().out.count('Invalid offset') == 2


class TestOptionBruteForce:
    def test_empty_ciphertext_is_rejected(self, capsys):
        main.option_brute_force('')
        assert 'Error' in capsys.readouterr().out

    def test_prints_every_offset_and_the_correct_candidate(self, capsys):
        ciphertext = main.encrypt('hi', 90)
        main.option_brute_force(ciphertext)
        out = capsys.readouterr().out
        assert "offset  90: 'hi'" in out
        # All 95 offsets should appear as lines.
        assert out.count('offset ') == main.ALPHABET_SIZE


class TestOptionSaveFile:
    def test_empty_message_is_rejected(self, capsys):
        main.option_save_file('')
        assert 'Error' in capsys.readouterr().out

    def test_saves_the_message(self, tmp_path):
        path = tmp_path / 'out.txt'
        with mock.patch('builtins.input', return_value=str(path)):
            main.option_save_file('hello world')
        assert path.read_text() == 'hello world'

    def test_unwritable_path_reports_an_error(self, capsys, tmp_path):
        bad_path = tmp_path / 'no-such-dir' / 'out.txt'
        with mock.patch('builtins.input', return_value=str(bad_path)):
            main.option_save_file('hello world')
        assert 'could not write' in capsys.readouterr().out
