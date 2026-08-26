<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
# Table of Contents

- [Table of Contents](#table-of-contents)
- [Aim](#aim)
- [Introduction](#introduction)
- [Mainly used functions](#mainly-used-functions)
- [Options](#options)
- [Key vs Ciphertext](#key-vs-ciphertext)
- [Brute-force Decryption](#brute-force-decryption)
- [Command-Line Mode](#command-line-mode)
- [Encryption Process](#encryption-process)
- [Decryption Process](#decryption-process)
- [Sample Output](#sample-output)
- [Testing](#testing)
- [Development](#development)
- [Known Limitations](#known-limitations)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Aim

Use Caesar Cipher technique to encrypt or decrypt an inputted message.

# Introduction

A simple way to encrypt data is attributed to [Julius
Caesar](http://en.wikipedia.org/wiki/Caesar_cipher), the Roman Emperor. This
method takes each character in a message and replaces it with one which is a
certain distance (offset) along the alphabet from it.

For example:
![Example of the technique](assets/example.png)

If the offset is 3 then A becomes D, B becomes E, C becomes F etc.

Encrypting DIG with the offset of +3 will result in GLJ. The decrypt GLJ, simply
offset by the same amount in the opposite direction (i.e. with the negative
offset -3).

Instead of restricting the cipher to the alphabetic characters only, we will use
all the printable ASCII characters. That is, all the characters from ASCII 32
(Space) to ASCII 126 (~).

# Mainly used functions

1. **ord(c)**


   If *c* is a string of length 1, *ord(c)* returns an integer representing the
   ASCII value of the string.

   For example: *ord(*'*a*'*)* returns the integer *97*.

2. **chr(i)**

   If *i* is an integer, *chr(i)* returns a string containing only one character
   with an ASCII code is equal to the integer *i*.

   For example: *chr(97)* returns the string '*a*'

# Options

Includes many functions that collectively simulate a menu driven program that
will allow the user to enter commands and process these commands until the quit
command is entered.

The following commands are allowed:
1. **Enter Message**:

   Prompt for and read (from the keyboard) a string to be encrypted. Rejected
   immediately (with a clear error) if it contains any character outside the
   printable ASCII range - see "Encryption Process" below for why that matters.

2. **Load Message from File**:

   Prompt for a file path and read the message from it instead of typing it.
   The same character-range validation applies as for "Enter Message".

3. **Encrypt Message**:

   Encrypts the current message, or displays an error message if there isn't
   one yet. You can either type your own offset (32-126) or press Enter for a
   randomly generated one (using a CSPRNG, `secrets.randbelow()`). The
   ciphertext and the key (offset) are printed as two clearly separate pieces
   of output - see "Key vs Ciphertext" below.

4. **Decrypt Message**:

   Decrypts the current message, or displays an error message if there isn't
   one yet. Prompts for the offset (key) that was used to encrypt it; if you
   just encrypted something in this same session, pressing Enter reuses that
   offset automatically.

5. **Brute-force Decrypt**:

   Tries all 95 possible offsets against the current message and prints every
   candidate plaintext - see "Brute-force Decryption" below.

6. **Save Message to File**:

   Prompt for a file path and write the current message to it.

7. **Quit**:

   Displays a goodbye message to the screen and quits the program.

# Key vs Ciphertext

The original version of this program appended the encryption key as the last
character of the "encrypted" string - meaning anyone who had the ciphertext
automatically had the key too, which defeats the entire point of encrypting a
message to send to someone else. The key is now always printed and handled
separately from the ciphertext:

- In the interactive menu, encrypting prints the ciphertext and the key on
  separate lines, and decrypting always asks for the key rather than reading
  it off the end of the message.
- In the [command-line mode](#command-line-mode), the key is always printed
  to *stderr* - never mixed into stdout or an `--output` file - so piping the
  ciphertext to a file or another program never leaks the key alongside it.

# Brute-force Decryption

Because this cipher's keyspace is only 95 possible offsets (32-126), trying
every single one takes no time at all - no cryptanalysis needed, just
patience. This is *why* a Caesar cipher isn't considered secure by modern
standards: option 5 in the interactive menu (or `--mode brute-force` on the
command line) demonstrates this directly by printing every possible
decryption of a message, so you can just read down the list for one that
looks like real text.

# Command-Line Mode

Running `main.py` with no arguments starts the interactive menu described
above. Passing `--mode` instead runs a single operation and exits - useful for
scripting, piping, or processing a file without going through the menu:

```bash
# Encrypt (random offset; the key is printed to stderr)
python main.py --mode encrypt --message "Meet at dawn"

# Encrypt with a specific offset, reading from and writing to files
python main.py --mode encrypt --file plans.txt --offset 77 --output plans.enc

# Decrypt (the offset is required - it's never embedded in the ciphertext)
python main.py --mode decrypt --message "..." --offset 77

# Try every offset
python main.py --mode brute-force --message "..."
```

Run `python main.py --help` for the full list of options.

# Encryption Process

To start with, choose 1 as the offset. In this case, if the message 'abG' is
entered, after the encryption, the result should be 'bcH'. Now that it is
working, use the *randint()* function from the *random* module to make the
offset a random number between 32 and 126.

![Printable ASCII character set](assets/printable-ascii.png)

The program only work with the printable ASCII character set. That is, all the
characters from ASCII 32 (Space) to ASCII 126 (~). When the ASCII value of the
encrypted character points to a character beyond 126 it should *wrap* around to
the beginning of the set.

For example, if the offset is 4 and the character is '}' (ASCII 125) then it
will encrypt to ASCII 129. This is beyond 126 so you should subtract the total
number of characters in the set (95) to wrap back to the beginning. The
resulting encrypted character will be the double-quote character " (129-95,
ASCII 34). You may have to subtract 95 multiple times until it is within the
set, for example, '}' + '}' is 250, and minus 95 is 155. This is still out of
bounds. Use a loop. Note that if the encrypted string contains characters that
are not in the table above, then your ASCII values are not 'wrapping' correctly.

# Decryption Process

Subtract the offset (key) from the ASCII value of each character in the
message. These ASCII values are then converted back to characters using the
chr(i) function. As described in "Key vs Ciphertext" above, the offset is
supplied separately by whoever is decrypting - it's no longer read off the
end of the ciphertext itself.

Again, the program only work with the printable ASCII character set. That is,
all the characters from ASCII 32 (Space) to ASCII 126 (~). When the offset
points to a character less than 32 it should *wrap* around to the end of the
set.

For example, if the offset is 4 and the character is '!' (ASCII 33) then it will
decrypt to ASCII 29. This is less than 32 so wrap back to the end by adding the
total number of characters (95). This gives character '|' (29+95, ASCII 124).
You may have to add 95 multiple times until it is within the set. Use a loop.

# Sample Output

```text
-------------------
     MAIN MENU
-------------------
1. Enter Message
2. Load Message from File
3. Encrypt Message
4. Decrypt Message
5. Brute-force Decrypt (try every offset)
6. Save Message to File
7. Quit

Enter an option (1-7): 1
Please enter a new message: The rabbit has sprung.
Your message is: 'The rabbit has sprung.'.

-------------------
     MAIN MENU
-------------------
1. Enter Message
2. Load Message from File
3. Encrypt Message
4. Decrypt Message
5. Brute-force Decrypt (try every offset)
6. Save Message to File
7. Quit

Enter an option (1-7): 3
Enter an offset (32-126), or press Enter for a random one: 50
Your message was successfully encrypted.
Ciphertext: "';8RE455<GR;4FRFCEHA:`".
Key (offset): 50. Keep this separate from the ciphertext - anyone with both can decrypt it.

-------------------
     MAIN MENU
-------------------
1. Enter Message
2. Load Message from File
3. Encrypt Message
4. Decrypt Message
5. Brute-force Decrypt (try every offset)
6. Save Message to File
7. Quit

Enter an option (1-7): 4
Enter the offset (key) (32-126) [Enter for 50]: 
Your message was successfully decrypted.
Your message is: 'The rabbit has sprung.'.

-------------------
     MAIN MENU
-------------------
1. Enter Message
2. Load Message from File
3. Encrypt Message
4. Decrypt Message
5. Brute-force Decrypt (try every offset)
6. Save Message to File
7. Quit

Enter an option (1-7): 7
Your message is: 'The rabbit has sprung.'.

Goodbye
```


# Testing

Install the dev dependencies and run the test suite:

```bash
pip install -r requirements-dev.txt
pytest
```

# Development

CI runs on every pull request and push via GitHub Actions
(`.github/workflows/ci.yml`): linting (`ruff`), tests across Python
3.10-3.12, and `bandit` + `pip-audit` security scans. A weekly CodeQL scan
and Dependabot are also configured.

# Known Limitations

A round of review found and fixed one real bug:

- **Messages containing characters outside the printable ASCII range
  (32-126) were silently corrupted, not rejected.** The encrypt/decrypt
  wrap-around math is only a well-defined, invertible mapping for
  characters already within that range - a tab character, a newline, or
  any non-Latin/emoji character would still "encrypt" and "decrypt"
  without ever raising an error, but the round trip produced a different
  message than what was typed. Confirmed directly:
  `"hello\tworld\U0001F600"` round-tripped through encrypt then decrypt
  came back as `"hellohworldH"`. Entering a message with such characters
  is now rejected immediately, with a clear error, rather than silently
  corrupted later.

Also switched the offset generator from `random.randint()` to
`secrets.randbelow()`. This matters less than it might sound: the cipher
only has 95 possible offsets in total (32-126), so it's trivially
brute-forceable by exhaustive search regardless of how the offset was
generated - but using a CSPRNG instead of a general-purpose PRNG is still
the correct, zero-cost choice for anything called a cipher, rather than
leaning on that other weakness to excuse this one.

## New: key/ciphertext separation, brute-force, file I/O, CLI mode

Four features were added on top of the bug fixes above:

1. **Key and ciphertext are no longer bundled together** - see "Key vs
   Ciphertext" above. This was arguably the most significant gap in the
   original design: appending the key to the "encrypted" message meant
   anyone with the ciphertext had the key too.
2. **Brute-force decryption** (`option_brute_force()` / `--mode
   brute-force`) - tries all 95 possible offsets and prints every
   candidate plaintext, directly demonstrating why this cipher's tiny
   keyspace makes it insecure.
3. **Load/save a message from/to a file** (`option_load_file()` /
   `option_save_file()` in the menu, `--file`/`--output` on the command
   line) - the same character-range validation applies as for a typed
   message.
4. **A non-interactive CLI mode** (`--mode encrypt|decrypt|brute-force`)
   - see "Command-Line Mode" above - for scripting, piping, or batch
   processing without going through the menu.

The underlying cipher math (`encrypt()`/`decrypt()`) was pulled out into
functions with no I/O of their own, so both the interactive menu and the
CLI mode share a single implementation instead of duplicating it - and so
the cipher logic itself can be tested directly, independent of either
interface.
