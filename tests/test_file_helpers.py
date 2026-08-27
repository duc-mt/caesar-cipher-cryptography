from __future__ import annotations

import pytest

import main


class TestReadMessageFile:
    def test_reads_the_file_content(self, tmp_path):
        path = tmp_path / 'msg.txt'
        path.write_text('The rabbit has sprung.')

        assert main.read_message_file(str(path)) == 'The rabbit has sprung.'

    def test_strips_a_single_trailing_newline(self, tmp_path):
        path = tmp_path / 'msg.txt'
        path.write_text('The rabbit has sprung.\n')

        assert main.read_message_file(str(path)) == 'The rabbit has sprung.'

    def test_does_not_strip_other_whitespace(self, tmp_path):
        path = tmp_path / 'msg.txt'
        path.write_text('  padded  ')

        assert main.read_message_file(str(path)) == '  padded  '

    def test_missing_file_raises_oserror(self, tmp_path):
        with pytest.raises(OSError):
            main.read_message_file(str(tmp_path / 'does-not-exist.txt'))

    def test_non_utf8_file_raises_unicode_decode_error(self, tmp_path):
        path = tmp_path / 'binary.txt'
        path.write_bytes(b'\xff\xfe\x00\x01')

        with pytest.raises(UnicodeDecodeError):
            main.read_message_file(str(path))


class TestWriteMessageFile:
    def test_writes_the_content(self, tmp_path):
        path = tmp_path / 'out.txt'
        main.write_message_file(str(path), 'The rabbit has sprung.')

        assert path.read_text() == 'The rabbit has sprung.'

    def test_overwrites_an_existing_file(self, tmp_path):
        path = tmp_path / 'out.txt'
        path.write_text('old content')
        main.write_message_file(str(path), 'new content')

        assert path.read_text() == 'new content'

    def test_unwritable_path_raises_oserror(self, tmp_path):
        with pytest.raises(OSError):
            main.write_message_file(str(tmp_path / 'no-such-dir' / 'out.txt'),
                                     'content')
