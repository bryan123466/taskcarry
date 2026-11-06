"""Synthetic text-stream example; no USB, firmware or graphical UI access."""
import csv
import io
import math
from pathlib import Path
import re
import unittest


MAX_LINE = 256
DECIMAL = re.compile(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?')


def parse_frame(line):
    if not isinstance(line, str) or len(line) > MAX_LINE:
        raise ValueError('A frame must be bounded text without its line terminator.')
    fields = line.split(',')
    if (len(fields) != 4 or fields[0] != 'READ'
            or any(re.fullmatch(r'[0-9]+', part) is None for part in fields[1:3])
            or DECIMAL.fullmatch(fields[3]) is None):
        raise ValueError('Expected READ,sequence,time_ms,finite_decimal.')
    sequence, time_ms, value = int(fields[1]), int(fields[2]), float(fields[3])
    if not math.isfinite(value):
        raise ValueError('Measurement must be finite.')
    return sequence, time_ms, value


class Replay:
    """Keep accepted plot/CSV input rows; connection events are supplied explicitly."""
    def __init__(self):
        self.connected = True
        self.points = []
        self.invalid_frames = 0
        self.stale_or_duplicate_frames = 0
        self.discarded_partial_frames = 0
        self.buffer = ''
        self.discard_until_newline = False

    def feed(self, text):
        if not self.connected:
            return
        for character in text:
            if character != '\n':
                if not self.discard_until_newline:
                    self.buffer += character
                    if len(self.buffer) > MAX_LINE:
                        self.buffer = ''
                        self.discard_until_newline = True
                        self.invalid_frames += 1
                continue
            if not self.discard_until_newline:
                try:
                    point = parse_frame(self.buffer)
                except ValueError:
                    self.invalid_frames += 1
                else:
                    if self.points and point[0] <= self.points[-1][0]:
                        self.stale_or_duplicate_frames += 1
                    else:
                        self.points.append(point)
            self.buffer = ''
            self.discard_until_newline = False

    def disconnect(self):
        if self.buffer or self.discard_until_newline:
            self.discarded_partial_frames += 1
        self.buffer = ''
        self.discard_until_newline = False
        self.connected = False

    def reconnect(self):
        self.buffer = ''
        self.discard_until_newline = False
        self.connected = True

    def csv_text(self):
        result = io.StringIO(newline='')
        writer = csv.writer(result, lineterminator='\n')
        writer.writerow(('sequence', 'time_ms', 'value'))
        writer.writerows((sequence, time_ms, repr(value)) for sequence, time_ms, value in self.points)
        return result.getvalue()


class ReplayChecks(unittest.TestCase):
    def test_normal_rows_match_shared_csv(self):
        root = Path(__file__).resolve().parent
        replay = Replay()
        replay.feed((root / 'normal_frames.txt').read_text(encoding='utf-8'))
        self.assertEqual([(42, 1000, 1.234), (43, 1100, 1.25), (44, 1200, 1.22)], replay.points)
        self.assertEqual((root / 'expected.csv').read_text(encoding='utf-8'), replay.csv_text())

    def test_invalid_frames_never_become_measurement_points(self):
        replay = Replay()
        replay.feed('READ,1,100,nan\nREAD,2,100,1e999\nOTHER,3,100,1.0\nREAD,-1,100,1.0\n')
        replay.feed('x' * (MAX_LINE + 1) + '\n')
        self.assertEqual([], replay.points)
        self.assertEqual(5, replay.invalid_frames)

    def test_disconnect_clears_partial_and_reconnect_does_not_duplicate_old_points(self):
        replay = Replay()
        replay.feed('READ,42,1000,1.234\nREAD,43,1100,')
        replay.disconnect()
        replay.feed('1.250\n')
        self.assertEqual([(42, 1000, 1.234)], replay.points)
        replay.reconnect()
        replay.feed('READ,42,1000,1.234\nREAD,43,1100,1.250\n')
        self.assertEqual([(42, 1000, 1.234), (43, 1100, 1.25)], replay.points)
        self.assertEqual(1, replay.discarded_partial_frames)
        self.assertEqual(1, replay.stale_or_duplicate_frames)
        self.assertEqual(0, replay.invalid_frames)

    def test_partial_input_waits_for_line_termination(self):
        replay = Replay()
        replay.feed('READ,42,1000,')
        self.assertEqual([], replay.points)
        replay.feed('1.234\n')
        self.assertEqual([(42, 1000, 1.234)], replay.points)

    def test_csv_keeps_the_full_parsed_value(self):
        replay = Replay()
        replay.feed('READ,1,100,1.2345678901234567\n')
        csv_value = list(csv.reader(io.StringIO(replay.csv_text())))[1][2]
        self.assertEqual(replay.points[0][2], float(csv_value))


if __name__ == '__main__':
    unittest.main(verbosity=2)
