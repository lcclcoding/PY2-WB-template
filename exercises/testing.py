import contextlib
import io
import os
import re
import tempfile
import textwrap
import unittest.mock as mock

from contextlib import contextmanager
from typing import Callable, Generator, List, Tuple

REGEX_WORD = r"\b\w+\b"
REGEX_BINARY = r"[01]+"
REGEX_NUMBER = r"[-+]?\d*\.?\d+"

REGEX_FLOAT_DOLLAR = r"\$?-?\d+\.\d+"  # Matches a float with a dollar sign
REGEX_FLOAT_1DP = r"[-+]?\d+\.\d"

REGEX_FLOAT = r"[-+]?\d*\.\d+"
REGEX_INT = r"[-+]?\d+"
REGEX_STR_ANY = r".+"

REGEX_DATE_DD_MM_YYYY = r"\d{2}[/-]\d{2}[/-]\d{4}"
REGEX_DATE_YYYY_MM_DD = r"\d{4}[/-]\d{2}[/-]\d{2}"


def simulate_input(
    func: Callable,
    inputs: List[str],
    inputs_per_execution: int,
    regex: str = ".+",
    patch: str = "builtins.input",
) -> Tuple[str, List[str], List[List[str]]]:
    """
    Simulates input execution for a given function and parses the output based on a regular expression pattern.

    Args:
        func (Callable): The function to simulate input for.
        inputs (List[str]): A list of inputs to provide to the function.
        inputs_per_execution (int): The number of inputs to provide for each execution of the function.
        regex (str, optional): The regular expression pattern to use for extracting data from the output. Defaults to '.+'.
        patch (str, optional): The type of input to patch, e.g., 'builtins.input'. Defaults to 'builtins.input'.

    Returns:
        Tuple[str, List[str], List[List[str]]]: A tuple containing the following elements:
            - str: Stdout of all of the calls.
            - List[str]: A list of the outputs split based on inputs//inputs_per_execution runs.
            - List[List[str]]: A list of lists containing the matches found by the regex pattern for each output.
    """
    buffer = io.StringIO()
    error_regex = set()

    def run():
        try:
            func()
        except Exception as e:
            print(f"{type(e).__name__}: {e}")
            error_regex.add(f"{type(e).__name__}: .+")
        finally:
            print("++*****++")

    with contextlib.redirect_stdout(buffer):

        if len(inputs) == 0 or inputs_per_execution == 0:
            run()
        else:
            for i in range(len(inputs) // inputs_per_execution):
                batch = inputs[
                    i * inputs_per_execution : (i + 1) * inputs_per_execution
                ]
                with mock.patch(patch, side_effect=batch):
                    run()

    stdout = buffer.getvalue().strip()
    outputs = stdout.split("++*****++")[:-1]
    outputs = list(map(str.strip, outputs))

    # regex will be matched in all lowercase
    if error_regex:
        regex = f"{'|'.join(map(str.lower, error_regex))}|{regex}"

    tests = [re.findall(regex, output.lower()) for output in outputs]

    return stdout, outputs, tests


@contextmanager
def simulate_file(text: str = None) -> Generator[Tuple[str, str], None, None]:
    """
    A context manager that simulates reading and writing to temporary files with provided text.

    This function creates two temporary files: one for input (`in.txt`) and one for output (`out.txt`).
    The input file is populated with the provided text, which can be used by functions that require file input.

    Args:
        text (str, optional): The text to write to the input file. If not provided, a default text is used.

    Yields:
        Generator[Tuple[str, str], None, None]: A tuple containing two file paths:
            - str: The path to the input file (`in.txt`).
            - str: The path to the output file (`out.txt`).
    """
    if text is None:
        text = """
            Beneath the veil of twilight, shadows danced across the cobblestone streets.
            The air was thick with the scent of blooming jasmine, weaving through the whispers of a distant melody.
            A lantern flickered, its warm glow stretching out like the fingers of a ghostly hand.
            Somewhere, the hoot of an owl broke the silence, echoing through the stillness.

            Time seemed to slow, each tick of the clock magnified by the rhythmic patter of raindrops on weathered roofs.
            An old bookshop, its sign creaking in the wind, stood defiant against the passage of time.
            Inside, the scent of parchment and ink embraced the weary traveler who dared to step through its doors.

            Rows upon rows of books stood like sentinels, each holding secrets of far-off lands and forgotten worlds.
            A single candle burned on a wooden desk, its flame swaying gently as if keeping pace with the breath of the universe.
            The sound of a page turning was a symphony, a crescendo of knowledge waiting to be discovered.

            Beyond the shop, a narrow alley twisted and turned, its walls adorned with ivy that seemed to glow under the faint moonlight.
            The cobblestones shimmered like a mosaic of stars, each stone a relic of countless footsteps etched into history.

            A cat perched on a windowsill, its golden eyes glinting with secrets it would never share.
            In the distance, a bell tolled, each chime carrying a hint of mystery.
            The world felt alive yet eerily still, as if caught in the delicate balance between dream and reality.
        """
        text = textwrap.dedent(text).strip()

    with tempfile.TemporaryDirectory() as temp_dir:
        filepath_in = os.path.join(temp_dir, "in.txt")
        filepath_out = os.path.join(temp_dir, "out.txt")
        with open(filepath_in, "w") as file:
            _ = file.write(text)

        yield filepath_in, filepath_out
