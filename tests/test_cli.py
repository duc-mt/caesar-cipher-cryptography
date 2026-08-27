"""Tests for the non-interactive CLI mode.

Exercises main.main() with a mocked sys.argv, which is how a person
would actually invoke `python main.py --mode ...` from a shell.
"""

from __future__ import annotations

from unittest import mock

import pytest

import main


def run_main(argv):
    with mock.patch('sys.argv', ['main.py', *argv]):
        return main.main()


class TestNoModeRunsInteractive:
    def test_no_arguments_runs_the_interactive_menu(self):
        with mock.patch('main.run_interactive') as mock_run_interactive:
            exit_code = run_main([])
        mock_run_interactive.assert_called_once()
        assert exit_code == 0


class TestEncryptMode:
    def test_encrypts_with_a_given_offset(self, capsys):
        exit_code = run_main(
            ['--mode', 'encrypt', '--message', 'hi', '--offset', '50']
        )
        assert exit_code == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == main.encrypt('hi', 50)
        assert 'Key (offset): 50' in captured.err

    def test_key_is_never_printed_to_stdout(self, capsys):
        run_main(['--mode', 'encrypt', '--message', 'hi', '--offset', '50'])
        captured = capsys.readouterr()
        assert '50' not in captured.out

    def test_random_offset_when_none_given(self, capsys):
        with mock.patch('main.random_offset', return_value=50):
            run_main(['--mode', 'encrypt', '--message', 'hi'])
        captured = capsys.readouterr()
        assert captured.out.strip() == main.encrypt('hi', 50)

    def test_invalid_message_exits_with_an_error(self):
        with pytest.raises(SystemExit) as exc_info:
            run_main(['--mode', 'encrypt', '--message', 'bad\ttab'])
        assert exc_info.value.code == 2

    def test_out_of_range_offset_exits_with_an_error(self):
        with pytest.raises(SystemExit) as exc_info:
            run_main(
                ['--mode', 'encrypt', '--message', 'hi', '--offset', '999']
            )
        assert exc_info.value.code == 2

    def test_unwritable_output_path_exits_with_an_error(self, tmp_path):
        bad_path = tmp_path / 'no-such-dir' / 'out.txt'
        with pytest.raises(SystemExit) as exc_info:
            run_main([
                '--mode', 'encrypt', '--message', 'hi', '--offset', '50',
                '--output', str(bad_path),
            ])
        assert exc_info.value.code == 2

    def test_writes_ciphertext_to_output_file_key_stays_out_of_it(
        self, capsys, tmp_path
    ):
        out_path = tmp_path / 'out.txt'
        run_main([
            '--mode', 'encrypt', '--message', 'hi', '--offset', '50',
            '--output', str(out_path),
        ])
        assert out_path.read_text() == main.encrypt('hi', 50)
        # The key must never end up in the output file.
        assert '50' not in out_path.read_text()
        # It's still reported, just to stderr.
        assert 'Key (offset): 50' in capsys.readouterr().err


class TestDecryptMode:
    def test_decrypts_with_a_given_offset(self, capsys):
        ciphertext = main.encrypt('hi', 50)
        exit_code = run_main(
            ['--mode', 'decrypt', '--message', ciphertext, '--offset', '50']
        )
        assert exit_code == 0
        assert capsys.readouterr().out.strip() == 'hi'

    def test_missing_offset_exits_with_an_error(self):
        with pytest.raises(SystemExit) as exc_info:
            run_main(['--mode', 'decrypt', '--message', 'anything'])
        assert exc_info.value.code == 2

    def test_out_of_range_offset_exits_with_an_error(self):
        with pytest.raises(SystemExit) as exc_info:
            run_main(
                ['--mode', 'decrypt', '--message', 'x', '--offset', '999']
            )
        assert exc_info.value.code == 2


class TestBruteForceMode:
    def test_prints_every_offset(self, capsys):
        ciphertext = main.encrypt('hi', 90)
        run_main(['--mode', 'brute-force', '--message', ciphertext])
        out = capsys.readouterr().out
        assert "offset  90: 'hi'" in out
        assert out.count('offset ') == main.ALPHABET_SIZE

    def test_accepts_input_outside_printable_ascii(self, capsys):
        """brute-force must not require --message to already be valid
        printable ASCII - the whole point is trying to recover
        arbitrary ciphertext, which the wrap-around math can decode
        even if the *result* doesn't happen to be valid plaintext."""
        exit_code = run_main(['--mode', 'brute-force', '--message', 'xyz'])
        assert exit_code == 0


class TestFileInputOutput:
    def test_reads_message_from_file(self, capsys, tmp_path):
        in_path = tmp_path / 'in.txt'
        in_path.write_text('hi')

        run_main(
            ['--mode', 'encrypt', '--file', str(in_path), '--offset', '50']
        )
        assert capsys.readouterr().out.strip() == main.encrypt('hi', 50)

    def test_missing_input_file_exits_with_an_error(self, tmp_path):
        with pytest.raises(SystemExit) as exc_info:
            run_main([
                '--mode', 'encrypt',
                '--file', str(tmp_path / 'nope.txt'),
                '--offset', '50',
            ])
        assert exc_info.value.code == 2

    def test_non_utf8_input_file_exits_with_an_error(self, tmp_path):
        path = tmp_path / 'binary.txt'
        path.write_bytes(b'\xff\xfe\x00\x01')

        with pytest.raises(SystemExit) as exc_info:
            run_main([
                '--mode', 'encrypt', '--file', str(path), '--offset', '50',
            ])
        assert exc_info.value.code == 2

    def test_message_and_file_are_mutually_exclusive(self):
        with pytest.raises(SystemExit) as exc_info:
            run_main([
                '--mode', 'encrypt',
                '--message', 'hi', '--file', 'whatever.txt',
                '--offset', '50',
            ])
        assert exc_info.value.code == 2


class TestNoInputSource:
    def test_mode_without_message_or_file_exits_with_an_error(self):
        with pytest.raises(SystemExit) as exc_info:
            run_main(['--mode', 'encrypt'])
        assert exc_info.value.code == 2
