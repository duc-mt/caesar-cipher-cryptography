#!/usr/bin/python3
# -*- coding: utf-8 -*-

# =============================================================================
#
#        FILE: main.py
#      AUTHOR: Mai Tan Duc
#       EMAIL: ducmai.network@gmail.com
#        DATE: 2021-10-21
# DESCRIPTION: Use Caesar Cipher technique to encrypt or decrypt an
#              inputted message.
#
# =============================================================================


# ------------------------------- Module Imports ------------------------------
# To parse command-line arguments for the non-interactive CLI mode.
import argparse

# To print the encryption key to stderr, separately from stdout, so
# piping stdout to a file or another program never mixes the key in
# with the ciphertext.
import sys

# To randomise the offset value with a CSPRNG, so it isn't predictable
# from a PRNG's internal state - see the note on random_offset() below
# for why this matters less than it sounds, but it's a correct,
# zero-cost choice for anything calling itself a cipher.
import secrets

# To implement Design by Contract.
import icontract


# ------------------------------- Named Constant -------------------------------
# The printable ASCII range this cipher is defined over: Space to ~.
ASCII_MIN = 32
ASCII_MAX = 126
ALPHABET_SIZE = ASCII_MAX - ASCII_MIN + 1  # 95


# ------------------------------ Pure Cipher Logic -----------------------------
# The functions below hold the actual cipher math and have no I/O of
# their own - both the interactive menu and the CLI mode call into
# these, so the logic is only implemented (and tested) once.
@icontract.ensure(lambda message: isinstance(message, str))
@icontract.ensure(lambda result: isinstance(result, bool))
def is_valid_message(message):
    """Check every character in `message` is within the printable
    ASCII range this cipher is defined over: 32 (Space) to 126 (~).

    Parameters
    ----------
    message : str
        The message to check.

    Returns
    -------
    bool
        True if every character is in range, False otherwise.
    """
    return all(ASCII_MIN <= ord(char) <= ASCII_MAX for char in message)


@icontract.ensure(lambda result: isinstance(result, int))
def random_offset():
    """Generate a random offset in [32, 126] using a CSPRNG.

    NOTE: random.randint() used to be used for this. It's a Mersenne
    Twister PRNG, not a CSPRNG - not appropriate for a cipher's key,
    in principle. In practice this cipher only has 95 possible offsets
    total, so it's trivially brute-forceable by exhaustive search
    regardless of how the offset was generated - see brute_force()
    below - but using secrets instead of random is still the correct,
    zero-cost choice for anything called a cipher, rather than relying
    on that other weakness to excuse this one.
    """
    return secrets.randbelow(ALPHABET_SIZE) + ASCII_MIN


@icontract.require(lambda message: is_valid_message(message))
@icontract.ensure(lambda result: isinstance(result, str))
def encrypt(message, offset):
    """Encrypt `message` by shifting every character forward by
    `offset`, wrapping around within the printable ASCII range.

    Parameters
    ----------
    message : str
        The plaintext to encrypt. Must be valid per is_valid_message().
    offset : int
        The shift amount. Mathematically this works correctly for any
        non-negative integer (the wrap-around is equivalent to a
        shift by `offset mod 95`) - restricting user-entered offsets
        to 32-126 is a UX convention enforced at the menu/CLI layer
        (so "the keyspace" has a clean, bounded, documented size for
        brute_force() to exhaustively search), not a requirement of
        this function. A negative offset is not supported.

    Returns
    -------
    str
        The ciphertext. Unlike the original version of this cipher,
        the offset is never appended to the result - see
        option_encrypt()'s docstring for why keeping them separate
        matters.
    """
    result = ''
    for char in message:
        value = ord(char) + offset
        while value > ASCII_MAX:
            value -= ALPHABET_SIZE
        result += chr(value)
    return result


@icontract.ensure(lambda result: isinstance(result, str))
def decrypt(ciphertext, offset):
    """Decrypt `ciphertext` by shifting every character back by
    `offset`, wrapping around within the printable ASCII range.

    Parameters
    ----------
    ciphertext : str
        The text to decrypt.
    offset : int
        The shift amount that was used to encrypt it. See encrypt()'s
        docstring for why this isn't restricted to 32-126 here (but a
        negative offset isn't supported, same as encrypt()).

    Returns
    -------
    str
        The recovered plaintext - correct only if `offset` is the
        actual key that was used to encrypt this ciphertext.
    """
    result = ''
    for char in ciphertext:
        value = ord(char) - offset
        while value < ASCII_MIN:
            value += ALPHABET_SIZE
        result += chr(value)
    return result


@icontract.ensure(lambda result: len(result) == ALPHABET_SIZE)
def brute_force(ciphertext):
    """Try every one of the 95 possible offsets against `ciphertext`.

    This is the classic demonstration of why a Caesar cipher isn't
    secure: with such a small keyspace, trying every key takes no
    time at all - no cryptanalysis needed, just patience.

    Parameters
    ----------
    ciphertext : str
        The text to attack.

    Returns
    -------
    list[tuple[int, str]]
        One (offset, candidate_plaintext) pair per possible offset,
        in ascending offset order.
    """
    return [
        (offset, decrypt(ciphertext, offset))
        for offset in range(ASCII_MIN, ASCII_MAX + 1)
    ]


# -------------------------- File Helpers (shared) -----------------------------
def read_message_file(path):
    """Read a message from a text file, for shared use by both the
    interactive menu and the CLI mode.

    A single trailing newline (the kind any text editor leaves at the
    end of a file) is stripped, since it isn't part of the message.
    Embedded newlines elsewhere in the file are NOT stripped - they're
    outside the printable ASCII range this cipher is defined over, so
    is_valid_message() will (correctly) reject a genuinely multi-line
    file rather than silently mangling it.

    Parameters
    ----------
    path : str
        Path to the file to read.

    Returns
    -------
    str
        The file's content.

    Raises
    ------
    OSError
        If the file can't be read.
    UnicodeDecodeError
        If the file isn't valid UTF-8 text.
    """
    with open(path, encoding='utf-8') as f:
        content = f.read()
    if content.endswith('\n'):
        content = content[:-1]
    return content


def write_message_file(path, content):
    """Write `content` to a text file, for shared use by both the
    interactive menu and the CLI mode.

    Parameters
    ----------
    path : str
        Path to the file to write.
    content : str
        The text to write.

    Raises
    ------
    OSError
        If the file can't be written.
    """
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


# --------------------------- Interactive Menu ---------------------------------
NUM_MENU_OPTIONS = 7


@icontract.ensure(lambda result: result is None)
def menu_driven_program():
    print(
        '-------------------',
        '     MAIN MENU',
        '-------------------',
        '1. Enter Message',
        '2. Load Message from File',
        '3. Encrypt Message',
        '4. Decrypt Message',
        '5. Brute-force Decrypt (try every offset)',
        '6. Save Message to File',
        '7. Quit',
        sep='\n',
        end='\n\n',
    )


@icontract.ensure(lambda result: isinstance(result, int))
def validate_option():
    """Prompt the user for a number and validate it.

    Returns
    -------
    int
        The valid choice taken from the user.
    """
    option = None

    while option is None or option not in range(1, NUM_MENU_OPTIONS + 1):
        try:
            option = float(input(f'Enter an option (1-{NUM_MENU_OPTIONS}): '))
        except ValueError as e:
            print(f'Invalid choice: {e}.')
        else:
            if option not in range(1, NUM_MENU_OPTIONS + 1):
                print(f'Invalid choice: option should be between 1 and '
                      f'{NUM_MENU_OPTIONS}.')

    return int(option)


@icontract.ensure(lambda result: isinstance(result, str))
def option_enter_message():
    """Prompt for and display the user message to the screen.

    Returns
    -------
    str
        The message received from the user.
    """
    message = input('Please enter a new message: ')

    if message == '':
        print()
        return message

    # NOTE: this used to accept any string at all, then silently
    # corrupt it later during encryption/decryption. Both operations'
    # wrap-around math is only a well-defined, invertible mapping for
    # characters already within 32-126: e.g. a tab character (ASCII 9)
    # or an emoji (ASCII 128000+) would still "encrypt" and "decrypt"
    # without ever raising an error, but the round trip silently
    # produced a different character than what was typed - confirmed
    # directly: "hello\tworld\U0001F600" decrypted back as
    # "hellohworldH". Rejecting invalid characters up front, where the
    # user can see and fix them, replaces silent data corruption with
    # a clear error.
    if not is_valid_message(message):
        print('Error: message must only contain printable ASCII '
              'characters (Space to ~).', end='\n\n')
        return ''

    print(f'Your message is: {message!r}.', end='\n\n')
    return message


def option_load_file():
    """Prompt for a file path and load a message from it.

    Returns
    -------
    str
        The loaded message, or '' if the file couldn't be read or
        contained invalid characters.
    """
    path = input('Enter the file path to load the message from: ').strip()

    try:
        content = read_message_file(path)
    except OSError as e:
        print(f'Error: could not read {path!r}: {e}.', end='\n\n')
        return ''
    except UnicodeDecodeError:
        print(f'Error: {path!r} is not a text file this cipher can read.',
              end='\n\n')
        return ''

    if not is_valid_message(content):
        print('Error: file contains characters outside the printable '
              'ASCII range (Space to ~).', end='\n\n')
        return ''

    print(f'Loaded message from {path!r}: {content!r}.', end='\n\n')
    return content


def option_encrypt(message):
    """Encrypt `message`, printing the ciphertext and the key
    (offset) as two clearly separate pieces of output.

    NOTE: the original version of this cipher appended the offset as
    the last character of the "encrypted" string, meaning anyone who
    had the ciphertext automatically had the key too - which defeats
    the point of encrypting a message to send to someone else in the
    first place. The offset is now printed separately (and can be
    chosen by the user instead of always random), and decrypting
    requires it to be supplied independently - see option_decrypt().

    Parameters
    ----------
    message : str
        The plaintext to encrypt. May be empty if the user chose this
        option before entering/loading a message.

    Returns
    -------
    tuple[str, int or None]
        (ciphertext, offset) - offset is None if message was empty.
    """
    if message == '':
        print('Error: Cannot encrypt an empty message.', end='\n\n')
        return message, None

    raw = input(
        f'Enter an offset ({ASCII_MIN}-{ASCII_MAX}), or press Enter for a '
        'random one: '
    ).strip()
    if raw == '':
        offset = random_offset()
    else:
        try:
            offset = int(raw)
        except ValueError:
            print('Invalid offset - using a random one instead.')
            offset = random_offset()
        else:
            if not (ASCII_MIN <= offset <= ASCII_MAX):
                print(f'Offset out of range ({ASCII_MIN}-{ASCII_MAX}) - '
                      'using a random one instead.')
                offset = random_offset()

    ciphertext = encrypt(message, offset)
    print('Your message was successfully encrypted.')
    print(f'Ciphertext: {ciphertext!r}.')
    print(f'Key (offset): {offset}. Keep this separate from the '
          'ciphertext - anyone with both can decrypt it.', end='\n\n')
    return ciphertext, offset


def option_decrypt(ciphertext, known_offset=None):
    """Decrypt `ciphertext` using an offset supplied by the user.

    Parameters
    ----------
    ciphertext : str
        The text to decrypt. May be empty if the user chose this
        option before entering/loading/encrypting anything.
    known_offset : int or None
        If this ciphertext was just produced by option_encrypt() in
        this same session, its offset - offered as the default so the
        common "encrypt then immediately decrypt" workflow doesn't
        require retyping it, without making it mandatory: decrypting
        a message received from someone else still works by entering
        whatever offset they separately told you.

    Returns
    -------
    str
        The decrypted message, or '' if ciphertext was empty.
    """
    if ciphertext == '':
        print('Error: Cannot decrypt an empty message.', end='\n\n')
        return ciphertext

    prompt = f'Enter the offset (key) ({ASCII_MIN}-{ASCII_MAX})'
    if known_offset is not None:
        prompt += f' [Enter for {known_offset}]'
    prompt += ': '

    offset = None
    while offset is None:
        raw = input(prompt).strip()
        if raw == '' and known_offset is not None:
            offset = known_offset
            break
        try:
            candidate = int(raw)
        except ValueError:
            print(f'Invalid offset: must be a whole number between '
                  f'{ASCII_MIN} and {ASCII_MAX}.')
            continue
        if not (ASCII_MIN <= candidate <= ASCII_MAX):
            print(f'Invalid offset: must be between {ASCII_MIN} and '
                  f'{ASCII_MAX}.')
            continue
        offset = candidate

    decrypted_message = decrypt(ciphertext, offset)
    print('Your message was successfully decrypted.')
    print(f'Your message is: {decrypted_message!r}.', end='\n\n')
    return decrypted_message


def option_brute_force(ciphertext):
    """Try every possible offset against `ciphertext` and print every
    candidate plaintext - the classic demonstration of why a Caesar
    cipher's tiny keyspace makes it insecure.

    Parameters
    ----------
    ciphertext : str
        The text to attack. May be empty if the user chose this
        option before entering/loading/encrypting anything.

    Returns
    -------
    None
    """
    if ciphertext == '':
        print('Error: Cannot brute-force an empty message.', end='\n\n')
        return

    print(f'Trying all {ALPHABET_SIZE} possible offsets - this is exactly '
          'why a Caesar cipher is not secure:', end='\n\n')
    for offset, candidate in brute_force(ciphertext):
        print(f'  offset {offset:3d}: {candidate!r}')
    print()


def option_save_file(message):
    """Prompt for a file path and save `message` to it.

    Parameters
    ----------
    message : str
        The text to save. May be empty if nothing has been
        entered/loaded/encrypted/decrypted yet.

    Returns
    -------
    None
    """
    if message == '':
        print('Error: There is no message to save yet.', end='\n\n')
        return

    path = input('Enter the file path to save the message to: ').strip()

    try:
        write_message_file(path, message)
    except OSError as e:
        print(f'Error: could not write to {path!r}: {e}.', end='\n\n')
        return

    print(f'Saved message to {path!r}.', end='\n\n')


def run_interactive():
    """Run the interactive, menu-driven session (the original
    behaviour of this program, extended with the new options above).
    """
    # Display the menu.
    menu_driven_program()

    # Current working text - whatever was last entered, loaded,
    # encrypted, or decrypted.
    message = ''
    # The offset last used by option_encrypt(), offered as the
    # default the next time option_decrypt() runs - see its
    # docstring. Cleared whenever `message` stops being that exact
    # ciphertext (i.e. after any operation other than encrypting).
    offset = None

    # Validate option chosen by user.
    option = validate_option()

    # Now we have a valid option.
    while option != NUM_MENU_OPTIONS:
        if option == 1:
            message = option_enter_message()
            offset = None
        elif option == 2:
            message = option_load_file()
            offset = None
        elif option == 3:
            message, offset = option_encrypt(message)
        elif option == 4:
            message = option_decrypt(message, offset)
            offset = None
        elif option == 5:
            option_brute_force(message)
        else:  # option == 6
            option_save_file(message)

        # Display the menu again.
        menu_driven_program()
        # Validate option chosen by user.
        option = validate_option()

    # Exit the loop, meaning option == NUM_MENU_OPTIONS (Quit):
    if message != '':
        print(f'Your message is: {message!r}.')
    print('\nGoodbye')


# ------------------------------ Non-Interactive CLI ---------------------------
def build_arg_parser():
    parser = argparse.ArgumentParser(
        description='Encrypt or decrypt a message using the Caesar Cipher '
                     'technique over the printable ASCII character set '
                     f'({ASCII_MIN}-{ASCII_MAX}). Run with no arguments for '
                     'the interactive menu.',
    )
    parser.add_argument(
        '--mode', choices=['encrypt', 'decrypt', 'brute-force'],
        help='Run once in this mode instead of the interactive menu.',
    )

    source = parser.add_mutually_exclusive_group()
    source.add_argument('--message', help='The message to process.')
    source.add_argument(
        '--file', help='Read the message from this file instead of '
                        '--message.',
    )

    parser.add_argument(
        '--offset', type=int,
        help=f'The offset (key), {ASCII_MIN}-{ASCII_MAX}. Required for '
             '--mode decrypt; random if omitted for --mode encrypt; '
             'ignored for --mode brute-force.',
    )
    parser.add_argument(
        '--output', help='Write the result to this file instead of '
                          'stdout. For --mode encrypt, the key is always '
                          'printed separately (to stderr), never included '
                          'in --output or stdout, so it never ends up '
                          'mixed in with the ciphertext.',
    )
    return parser


def run_cli(args, parser):
    """Run one CLI-mode operation and return a process exit code."""
    if args.file:
        try:
            text = read_message_file(args.file)
        except OSError as e:
            parser.error(f'could not read {args.file!r}: {e}')
        except UnicodeDecodeError:
            parser.error(f'{args.file!r} is not a text file this cipher '
                          'can read')
    elif args.message is not None:
        text = args.message
    else:
        parser.error('--message or --file is required with --mode')

    if args.mode != 'brute-force' and not is_valid_message(text):
        parser.error('message contains characters outside the printable '
                      f'ASCII range ({ASCII_MIN}-{ASCII_MAX})')

    if args.mode == 'encrypt':
        offset = args.offset if args.offset is not None else random_offset()
        if not (ASCII_MIN <= offset <= ASCII_MAX):
            parser.error(f'--offset must be between {ASCII_MIN} and '
                          f'{ASCII_MAX}')
        result = encrypt(text, offset)
        # The key is always printed to stderr, separately from the
        # ciphertext on stdout/--output - see build_arg_parser()'s
        # --output help text for why.
        print(f'Key (offset): {offset}', file=sys.stderr)

    elif args.mode == 'decrypt':
        if args.offset is None:
            parser.error('--offset is required for --mode decrypt')
        if not (ASCII_MIN <= args.offset <= ASCII_MAX):
            parser.error(f'--offset must be between {ASCII_MIN} and '
                          f'{ASCII_MAX}')
        result = decrypt(text, args.offset)

    else:  # brute-force
        result = '\n'.join(
            f'offset {offset:3d}: {candidate!r}'
            for offset, candidate in brute_force(text)
        )

    if args.output:
        try:
            write_message_file(args.output, result)
        except OSError as e:
            parser.error(f'could not write to {args.output!r}: {e}')
        print(f'Result written to {args.output!r}.', file=sys.stderr)
    else:
        print(result)

    return 0


# ------------------------------- Main Function -------------------------------
def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.mode is None:
        run_interactive()
        return 0

    return run_cli(args, parser)


# --------------------------- Call the Main Function --------------------------
if __name__ == '__main__':
    sys.exit(main())
