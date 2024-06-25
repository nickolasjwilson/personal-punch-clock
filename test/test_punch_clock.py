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
"""This module contains its namesake class."""


import argparse as ap
import datetime as dt
import pathlib as pl
import shutil
import time
import typing as ty
from unittest import mock

import pandas as pd
import pytest

import punch_clock as pc

# pylint: disable=protected-access,redefined-outer-name

_TEST_DIR = pl.Path("test")


@pytest.fixture
def tmp_log(tmp_path: pl.Path) -> pl.Path:
    """The file system path to a temporary log file."""
    return tmp_path / "log"


class TestPunchClock:
    """Tests the class "PunchClock"."""

    _INDEX = pd.Index(pc.PunchClock._COLUMN_NAMES)
    _HAS_HEADER = _TEST_DIR / "has_header.csv"
    _IN = _TEST_DIR / "in.csv"
    _OUT = _TEST_DIR / "out.csv"
    _MANY_IN = _TEST_DIR / "many_in.csv"
    _MANY_OUT = _TEST_DIR / "many_out.csv"
    _TOTAL_OUT = dt.timedelta(seconds=1513607931 - 1513600731)
    _PART_MANY_IN = dt.timedelta(seconds=20478)
    _TOTAL_MANY_OUT = _PART_MANY_IN + dt.timedelta(seconds=12034)
    _LAST_IDX = 2

    def test_init_blank(self, tmp_log: pl.Path) -> None:
        """Tests the method "__init__" with a blank log."""
        tmp_log.touch()
        with pc.PunchClock(tmp_log) as clock:
            assert clock.state == pc.State.OUT
        modified = pd.read_csv(tmp_log)
        pd.testing.assert_index_equal(self._INDEX, modified.columns)

    def test_init_header(self) -> None:
        """Tests the method "__init__" with a log having a header."""
        self._assert_nothing_changes(self._HAS_HEADER, pc.State.OUT)

    def test_init_in(self) -> None:
        """Tests the method "__init__" with the user clocked in."""
        self._assert_nothing_changes(self._IN, pc.State.IN)

    def test_punch_in_first(self, tmp_log: pl.Path) -> None:
        """Tests the method "punch_in" with no clock punches."""
        with pc.PunchClock(tmp_log) as clock:
            clock.punch_in()
            assert clock.state == pc.State.IN
        self._assert_recent_integral(tmp_log, pc.State.IN)

    def test_punch_in_in(self) -> None:
        """Tests the method "punch_in" when clocked in."""
        self._assert_nothing_changes(
            self._IN, pc.State.IN, pc.PunchClock.punch_in.__name__
        )

    def test_punch_out_in(self, tmp_log: pl.Path) -> None:
        """Tests the method "punch_out" when clocked in."""
        shutil.copy(self._IN, tmp_log)
        original = pd.read_csv(tmp_log)
        with pc.PunchClock(tmp_log) as clock:
            clock.punch_out()
            assert clock.state == pc.State.OUT
        reopened = self._assert_recent_integral(tmp_log, pc.State.OUT)
        reopened.loc[0, pc.State.OUT.value] = None
        pd.testing.assert_frame_equal(original, reopened)

    def test_punch_out_out(self) -> None:
        """Tests the method "punch_out" when clocked out."""
        self._assert_nothing_changes(
            self._OUT, pc.State.OUT, pc.PunchClock.punch_out.__name__
        )

    def test_punch_out_many_in(self, tmp_log: pl.Path) -> None:
        """Tests the method "punch_out" with many punches when clocked in."""
        shutil.copy(self._MANY_IN, tmp_log)
        original = pd.read_csv(tmp_log)
        with pc.PunchClock(tmp_log) as clock:
            assert clock.state == pc.State.IN
            clock.punch_out()
            assert clock.state == pc.State.OUT
        reopened = pd.read_csv(tmp_log)
        original.loc[self._LAST_IDX, pc.State.OUT.value] = time.time()
        pd.testing.assert_frame_equal(
            original,
            reopened,
            check_dtype=False,
            check_exact=False,
        )

    def test_sum_blank(self, tmp_log: pl.Path) -> None:
        """Tests the method "sum" with a blank log."""
        tmp_log.touch()
        with pc.PunchClock(tmp_log) as clock:
            assert clock.sum() == dt.timedelta(0)

    def test_sum_in(self) -> None:
        """Tests the method "sum" when clocked in."""
        total, original = self._assert_nothing_changes(
            self._IN, pc.State.IN, pc.PunchClock.sum.__name__
        )
        clocked_in = original[pc.State.IN.value][0]
        now = time.time()
        total_cap_seconds = now - clocked_in
        total_cap = dt.timedelta(seconds=total_cap_seconds)
        diff_time_delta = total_cap - total
        diff_seconds = diff_time_delta.total_seconds()
        self._assert_small(diff_seconds)

    def test_sum_out(self) -> None:
        """Tests the method "sum" when clocked out."""
        self._assert_nothing_changes(
            self._OUT,
            pc.State.OUT,
            pc.PunchClock.sum.__name__,
            self._TOTAL_OUT,
        )

    def test_sum_many_in(self) -> None:
        """Tests the method "sum" with many punches when clocked in."""
        total, original = self._assert_nothing_changes(
            self._MANY_IN, pc.State.IN, pc.PunchClock.sum.__name__
        )
        clocked_in = original[pc.State.IN.value].iloc[-1]
        now = time.time()
        additional_cap_seconds = now - clocked_in
        additional_cap = dt.timedelta(seconds=additional_cap_seconds)
        total_cap = self._PART_MANY_IN + additional_cap
        diff_time_delta = total_cap - total
        diff_seconds = diff_time_delta.total_seconds()
        self._assert_small(diff_seconds)

    def test_sum_many_out(self) -> None:
        """Tests the method "sum" with many punches when clocked out."""
        self._assert_nothing_changes(
            self._MANY_OUT,
            pc.State.OUT,
            pc.PunchClock.sum.__name__,
            self._TOTAL_MANY_OUT,
        )

    def test_reset_out(self, tmp_log: pl.Path) -> None:
        """Tests the method "reset" when clocked out."""
        self._test_reset(self._MANY_OUT, tmp_log, pc.State.OUT)

    def test_reset_in(self, tmp_log: pl.Path) -> None:
        """Tests the method "reset" when clocked in."""
        self._test_reset(self._MANY_IN, tmp_log, pc.State.IN)

    def _assert_recent_integral(
        self, log_path: pl.Path, state: pc.State
    ) -> pd.DataFrame:
        """Assert that a timestamp is both recent and integral.

        Args:
            log_path: The file system path to a clock punch log.
            state: A state whose start the timestamp marks.

        Returns:
            The clock punch log as a data frame.
        """
        frame = pd.read_csv(log_path)
        timestamp = frame[state.value][0]
        timestamp_int = int(timestamp)
        assert timestamp == timestamp_int
        now = time.time()
        diff = now - timestamp
        self._assert_small(diff)
        return frame

    def _assert_small(self, value: float) -> None:
        """Assert that a numeric value is small.

        Args:
            value: A numeric value which should be non-negative and less
                than one.
        """
        assert 0 <= value <= 1

    def _assert_nothing_changes(
        self,
        log_path: pl.Path,
        state: pc.State,
        method_name: str | None = None,
        expected_return_value: dt.timedelta | None = None,
    ) -> ty.Tuple[dt.timedelta, pd.DataFrame]:
        """Assert that nothing changes.

        Instantiation of a punch clock should not alter the punch log.
        Any named method also should not alter the punch log nor the
        punch clock's state.

        Args:
            log_path: The file system path to a clock punch log.
            state: The expected state of the punch clock.
            method_name: The name of a punch-clock method.
            expected_return_value: The value expected to be returned
                from the method.

        Returns:
            A tuple. The first element is the value returned from the
            named method, and the second element is clock punch log in
            its original state.
        """
        original = pd.read_csv(log_path)
        with pc.PunchClock(log_path) as clock:
            assert clock.state == state
            if method_name:
                method = getattr(clock, method_name)
                return_value = method()
                if expected_return_value:
                    assert return_value == expected_return_value
            else:
                return_value = None
            assert clock.state == state
        reopened = pd.read_csv(log_path)
        pd.testing.assert_frame_equal(original, reopened)
        return return_value, original

    def _test_reset(
        self, source_log: pl.Path, temp_log: pl.Path, state: pc.State
    ) -> None:
        """Tests the method "reset".

        Args:
            source_log: The file system path to a clock punch log which
                is used as a starting point.
            temp_log: The file system path for an editable copy of
                `source_log`.
            state: The expected initial state of the punch clock.
        """
        shutil.copy(source_log, temp_log)
        with pc.PunchClock(temp_log) as clock:
            assert clock.state == state
            clock.reset()
            assert clock.state == pc.State.OUT
        has_header = pd.read_csv(self._HAS_HEADER)
        modified = pd.read_csv(temp_log)
        pd.testing.assert_frame_equal(has_header, modified)


@pytest.mark.parametrize(
    "name_space, state, work_time",
    [
        (ap.Namespace(in_=False, out=False, reset=False), "out", "2:26:49"),
        (ap.Namespace(in_=True, out=False, reset=False), "in", "2:26:49"),
        (ap.Namespace(in_=False, out=True, reset=False), "out", "2:26:49"),
        (ap.Namespace(in_=False, out=False, reset=True), "out", "0:00:00"),
    ],
)
def test_main(
    capsys: pytest.CaptureFixture,
    tmp_log: pl.Path,
    name_space: ap.Namespace,
    state: str,
    work_time: str,
) -> None:
    """Tests the function `main`."""
    orginal_log_path = pc._LOG_PATH
    source = _TEST_DIR / "main.csv"
    shutil.copy(source, tmp_log)
    pc._LOG_PATH = tmp_log
    with mock.patch("argparse.ArgumentParser.parse_args") as mock_parse_args:
        mock_parse_args.return_value = name_space
        pc.main()
    captured = capsys.readouterr()
    assert (
        captured.out
        == f"You have worked {work_time}; you are clocked {state}.\n"
    )
    assert captured.err == ""
    pc._LOG_PATH = orginal_log_path
