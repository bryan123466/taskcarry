# Synthetic USB serial stream contract

This small fixture gives the three engineering chats something concrete to share and review. It contains simulated text inputs and PC-side parsing/replay checks. It does not connect to a USB device, implement firmware, draw a graphical interface, or prove any hardware behavior.

The first milestone uses UTF-8 text with one LF-terminated measurement per line:

```text
READ,42,1000,1.234
```

| Field | Meaning |
| --- | --- |
| `READ` | Fixed measurement record type. |
| `42` | Nonnegative sequence number, increasing across this simulated connection and reconnection. |
| `1000` | Nonnegative simulated elapsed time in milliseconds. |
| `1.234` | Finite decimal measurement value; no physical unit is asserted by this fixture. |

`normal_frames.txt` supplies three measurements. `expected.csv` contains the corresponding three curve-input/CSV rows. A row is accepted only after its line terminator arrives. Malformed records, non-finite values, and lines longer than 256 characters are rejected. Older or duplicate sequence numbers do not create extra points.

Disconnection clears an incomplete frame and does not manufacture measurements. Data supplied while disconnected is ignored. Reconnection keeps accepted points, starts with an empty input buffer, and expects sequence numbering to continue. A real device that restarts its counter needs an explicit session/epoch contract; this fixture does not silently infer a device reset.

Run the local checks with Python 3.11 or newer:

```sh
python replay.py
```

The checks cover the shared sample, invalid frames, partial input, and disconnection/reconnection. A passing result establishes these synthetic parsing outcomes only. Actual serial timing, firmware output, live chart rendering, CSV file interactions, and device testing remain separate engineering acceptance work. Wireless support is outside this first milestone.
