#!/usr/bin/env python3
###############################################################################
# Copyright 2017, 2024 Nickolas J. Wilson
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###############################################################################
"""This module contains two classes and a function.

Classes:
    State
    PunchClock

Functions:
    main
"""


import argparse as ap
import datetime as dt
import enum
import pathlib as pl
import string as st
import time
import typing as ty

import pandas as pd


class State(enum.Enum):
    """A clocked state."""

    # pylint: disable=invalid-name

    IN = "In"
    OUT = "Out"


class PunchClock:
    """A single-user punch clock.

    Atttributes:
        state: An instance of the class "State".

    Methods:
        punch_in
        punch_out
        sum
        reset
    """

    _COLUMN_NAMES = (State.IN.value, State.OUT.value)
    _NO_DECIMAL_POINT = "%.0f"
    _NULL_REPLACEMENT = 0

    def __init__(self, log_path: pl.Path) -> None:
        """Initialize an instance of this class.

        Load the log of clock punches from disk.

        Args:
            log_path: The path to the file in which punches are logged.
        """
        try:
            self._frame = pd.read_csv(log_path)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            self.reset()
        if not self._frame[State.OUT.value].empty and pd.isnull(
            self._frame[State.OUT.value].iloc[-1]
        ):
            self._state = State.IN
        else:
            self._state = State.OUT
        self._log_path = log_path

    def __enter__(self) -> "PunchClock":
        """Return this object."""
        return self

    def __exit__(self, *_: ty.Any) -> None:
        """Write the log of clock punches to disk."""
        # Pandas cannot represent missing values in integer series
        # <http://pandas.pydata.org/pandas-docs/stable/gotchas.html#support-for-integer-na>,
        # so the timestamps are stored as floating-point numbers.
        self._frame.to_csv(
            self._log_path, index=False, float_format=self._NO_DECIMAL_POINT
        )

    @property
    def state(self) -> State:
        """Return the corresponding attribute."""
        return self._state

    def punch_in(self) -> None:
        """Punch in."""
        if self.state == State.OUT:
            now = self._get_current_time()
            self._frame.loc[-1] = [now, None]
            self._state = State.IN

    def punch_out(self) -> None:
        """Punch out."""
        if self.state == State.IN:
            now = self._get_current_time()
            last_idx = self._frame.shape[0] - 1
            self._frame.loc[last_idx, State.OUT.value] = now
            self._state = State.OUT

    def sum(self) -> dt.timedelta:
        """Return the time worked."""
        elapsed_seconds_series = (
            self._frame[State.OUT.value] - self._frame[State.IN.value]
        )
        elapsed_seconds_sum = elapsed_seconds_series.sum()
        if pd.isnull(elapsed_seconds_sum):
            elapsed_seconds = self._NULL_REPLACEMENT
        else:
            elapsed_seconds = elapsed_seconds_sum
        if self.state == State.IN:
            clocked_in = self._frame[State.IN.value].iloc[-1]
            now = self._get_current_time()
            elapsed_seconds += now - clocked_in
        elapsed_seconds_int = int(elapsed_seconds)
        return dt.timedelta(seconds=elapsed_seconds_int)

    def reset(self) -> None:
        """Reset the log of clock punches."""
        self._frame = pd.DataFrame(columns=self._COLUMN_NAMES)
        self._state = State.OUT

    @staticmethod
    def _get_current_time() -> int:
        """Return the number of seconds since 1970-01-01 00:00:00 UTC."""
        current_time = time.time()
        return int(current_time)


_LOG_PATH = pl.Path.home() / ".punch_clock"
_MESSAGE_TEMPLATE = st.Template(
    "You have worked ${time}; you are clocked ${state}."
)


def main():
    """Execute this script's main functionality."""
    parser = ap.ArgumentParser(description="personal punch clock")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-i", "--in", action="store_true", help="punch in", dest="in_"
    )
    group.add_argument("-o", "--out", action="store_true", help="punch out")
    group.add_argument(
        "-r",
        "--reset",
        action="store_true",
        help="delete the stored clock punches",
    )
    args = parser.parse_args()
    with PunchClock(_LOG_PATH) as clock:
        if args.in_:
            clock.punch_in()
        elif args.out:
            clock.punch_out()
        elif args.reset:
            clock.reset()
        work_time = clock.sum()
        clocked_state = clock.state.value.lower()
    work_time_str = str(work_time)
    message = _MESSAGE_TEMPLATE.substitute(
        time=work_time_str, state=clocked_state
    )
    print(message)


if __name__ == "__main__":
    main()
