Voltage Divider Calculator
--------------------------

This tool calculates the resistor divider network for a given target output voltage.

How to use:
1. Run "ResistorDivider.exe".
2. Enter:
   - Vup (top voltage)
   - Vdn (bottom voltage, default = 0)
   - Desired Vout (target output voltage)
3. (Optional) Override:
   - Enter a resistor value in the override box.
   - Tick "Override Rup" to fix the upper resistor(s).
   - Tick "Override Rdn" to fix the lower resistor(s).
   - The program will then search only the other side for the best match.
4. Click "Calculate".
5. The program will display:
   - Rup1, Rup2, Rdn1, Rdn2 values (to 2 decimals).
   - Equivalent resistances (Req_up, Req_dn).
   - Vout and error (to 3 decimals).
   - A circuit diagram with resistors and voltages.

CSV Files:
- resistors.csv → Input file with a list of resistor values (you provide).
- resistor_pairs.csv → Auto-generated at startup with all unique resistor/parallel combinations.
  NOTE: Do not edit resistor_pairs.csv manually; it is recreated each run.

Notes:
- Keep resistors.csv in the same folder as the exe.
- Vout and error values are shown to 3 decimals for accuracy.
- No Python installation required. This exe is standalone.
