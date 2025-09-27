import sys
import pandas as pd
import itertools
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QTextEdit, QVBoxLayout, QCheckBox, QHBoxLayout
)
from PyQt5.QtGui import QPainter, QPen, QFont, QColor, QBrush
from PyQt5.QtCore import Qt, QPointF
import math

def fmt(val):
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return "∞"
    return f"{val:.2f}"

class CircuitWidget(QWidget):
    def __init__(self):
        super().__init__()
        # Default placeholders (all 4 resistors drawn at startup)
        self.rup1 = None
        self.rup2 = None
        self.rdn1 = None
        self.rdn2 = None
        self.Vup = None
        self.Vdn = None
        self.Vout = None

    def set_values(self, up, dn, Vup, Vdn, Vout):
        self.rup1 = up["R1"]
        self.rup2 = up["R2"] if pd.notna(up["R2"]) else None
        self.rdn1 = dn["R1"]
        self.rdn2 = dn["R2"] if pd.notna(dn["R2"]) else None
        self.Vup = Vup
        self.Vdn = Vdn
        self.Vout = Vout
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        mid_x = w // 2
        top_y = 50
        mid_y = h // 2
        bot_y = h - 50

        pen = QPen(Qt.black, 2)
        painter.setPen(pen)

        # --- Voltage boxes ---
        painter.setFont(QFont("Arial", 9, QFont.Bold))
        painter.setBrush(QBrush(QColor("orange")))
        painter.drawRect(mid_x - 60, top_y - 30, 70, 25)
        painter.drawText(mid_x - 55, top_y - 12,
                         f"{self.Vup:.2f} V" if self.Vup is not None else "-- V")

        painter.drawRect(mid_x - 60, bot_y + 5, 70, 25)
        painter.drawText(mid_x - 55, bot_y + 22,
                         f"{self.Vdn:.2f} V" if self.Vdn is not None else "-- V")

        painter.drawRect(mid_x + 65, mid_y - 12, 70, 25)
        painter.drawText(mid_x + 70, mid_y + 5,
                         f"{self.Vout:.3f} V" if self.Vout is not None else "-- V")

        painter.setBrush(Qt.NoBrush)

        # Parallel rails (spread wider apart)
        left_x = mid_x - 60
        right_x = mid_x + 60

        # Vertical rails
        painter.drawLine(left_x, top_y, left_x, bot_y)
        painter.drawLine(right_x, top_y, right_x, bot_y)

        # Connect Vup across rails
        painter.drawLine(left_x, top_y, right_x, top_y)

        # Connect Vdn across rails
        painter.drawLine(left_x, bot_y, right_x, bot_y)

        # Horizontal node at Vout
        painter.drawLine(left_x, mid_y, right_x, mid_y)
        painter.drawLine(mid_x, mid_y, mid_x + 65, mid_y)

        # --- Draw all 4 resistors with extra spacing ---
        self.draw_resistor(painter, left_x, top_y + 60, mid_y - 60,
                           "Rup1", self.rup1)
        self.draw_resistor(painter, right_x, top_y + 60, mid_y - 60,
                           "Rup2", self.rup2)
        self.draw_resistor(painter, left_x, mid_y + 60, bot_y - 60,
                           "Rdn1", self.rdn1)
        self.draw_resistor(painter, right_x, mid_y + 60, bot_y - 60,
                           "Rdn2", self.rdn2)

    def draw_resistor(self, painter, x, y1, y2, name, value):
        """Draw one resistor with zigzag and label always on the right side"""
        # Resistor body
        painter.setBrush(QBrush(QColor("yellow")))
        painter.drawRect(x - 10, y1, 20, (y2 - y1))
        painter.setBrush(Qt.NoBrush)

        # Zigzag
        step = (y2 - y1) // 6
        zigzag = []
        direction = 1
        for i in range(7):
            zigzag.append((x + direction * 8, y1 + i * step))
            direction *= -1
        painter.drawPolyline(*[QPointF(px, py) for px, py in zigzag])

        # Label value formatting
        painter.setFont(QFont("Arial", 8))
        if value is None:
            label_value = "∞ Ω"
        else:
            label_value = f"{value:.2f} Ω"

        # Always draw labels to the right
        text_y = (y1 + y2) // 2
        painter.drawText(x + 20, text_y - 5, name)
        painter.drawText(x + 20, text_y + 10, label_value)


class ResistorDividerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.prepare_pairs()
        self.load_pairs()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Voltage Divider Circuit - Resistor Pair Calculator")
        self.setGeometry(200, 100, 1150, 700)

        main_layout = QVBoxLayout()

        # Inputs
        self.input_v1 = QLineEdit()
        self.input_v2 = QLineEdit("0")
        self.input_vout = QLineEdit()
        main_layout.addWidget(QLabel("Vup:")); main_layout.addWidget(self.input_v1)
        main_layout.addWidget(QLabel("Vdn:")); main_layout.addWidget(self.input_v2)
        main_layout.addWidget(QLabel("Desired Vout:")); main_layout.addWidget(self.input_vout)

        # Override controls
        override_layout = QHBoxLayout()
        self.override_box = QLineEdit()
        self.override_box.setPlaceholderText("Override resistor value (Ω)")
        self.chk_rup = QCheckBox("Override Rup")
        self.chk_rdn = QCheckBox("Override Rdn")
        override_layout.addWidget(self.override_box)
        override_layout.addWidget(self.chk_rup)
        override_layout.addWidget(self.chk_rdn)
        main_layout.addLayout(override_layout)

        # Button
        self.button = QPushButton("Calculate")
        main_layout.addWidget(self.button)
        self.button.clicked.connect(self.calculate_divider)

        # Side-by-side layout
        side_layout = QHBoxLayout()
        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        self.result_area.setMinimumWidth(400)
        side_layout.addWidget(self.result_area)

        self.circuit = CircuitWidget()
        self.circuit.setMinimumSize(650, 450)
        side_layout.addWidget(self.circuit)

        main_layout.addLayout(side_layout)
        self.setLayout(main_layout)

    def prepare_pairs(self):
        base_res = pd.read_csv("resistors.csv")["Resistor"].tolist()
        pairs = []
        seen = set()
        for r in base_res:
            req = round(r, 3)
            if req not in seen:
                pairs.append({"Req": req, "R1": round(r, 3), "R2": None})
                seen.add(req)
        for r1, r2 in itertools.combinations(base_res, 2):
            req = (r1 * r2) / (r1 + r2)
            req_rounded = round(req, 3)
            if req_rounded not in seen:
                pairs.append({"Req": req_rounded, "R1": round(r1, 3), "R2": round(r2, 3)})
                seen.add(req_rounded)
        pd.DataFrame(pairs).to_csv("resistor_pairs.csv", index=False)

    def load_pairs(self):
        self.pairs = pd.read_csv("resistor_pairs.csv").to_dict(orient="records")

    def calculate_divider(self):
        try:
            Vup = float(self.input_v1.text())
            Vdn = float(self.input_v2.text())
            Vout_target = float(self.input_vout.text())
        except ValueError:
            self.result_area.setText("Please enter valid numbers.")
            return

        if not self.pairs:
            self.result_area.setText("No resistor pairs loaded.")
            return

        override_val = None
        if self.override_box.text():
            try:
                override_val = float(self.override_box.text())
            except ValueError:
                self.result_area.setText("Invalid override value.")
                return

        best_error = float("inf")
        best_combo = None

        for up in self.pairs if not (self.chk_rup.isChecked() and override_val) else [{"Req": override_val, "R1": override_val, "R2": None}]:
            for dn in self.pairs if not (self.chk_rdn.isChecked() and override_val) else [{"Req": override_val, "R1": override_val, "R2": None}]:
                Rup = up["Req"]; Rdn = dn["Req"]
                if Rup <= 0 or Rdn <= 0:
                    continue
                Vout_calc = Vdn + (Rdn / (Rup + Rdn)) * (Vup - Vdn)
                error = abs(Vout_calc - Vout_target)
                if error < best_error:
                    best_error = error
                    best_combo = (up, dn, Vout_calc)

        if best_combo:
            up, dn, vcalc = best_combo
            Rup = up["Req"]; Rdn = dn["Req"]
            Vin_required = Vdn + ((Vout_target - Vdn) * (Rup + Rdn)) / Rdn

            def fmt(val): return f"{val:.2f}" if val is not None else "∞"

            result_html = f"""
            <h3>Best Match</h3>
            <table border="1" cellspacing="0" cellpadding="4" 
                   style="border-collapse:collapse; text-align:center;">
                <tr style="background-color:#f0f0f0;">
                    <th>Resistor</th><th>Value (Ω)</th>
                </tr>
                <tr><td>Rup1</td><td>{fmt(up['R1'])}</td></tr>
                <tr><td>Rup2</td><td>{fmt(up['R2'])}</td></tr>
                <tr><td>Rdn1</td><td>{fmt(dn['R1'])}</td></tr>
                <tr><td>Rdn2</td><td>{fmt(dn['R2'])}</td></tr>
                <tr><td><b>Req_up</b></td><td><b>{Rup:.2f}</b></td></tr>
                <tr><td><b>Req_dn</b></td><td><b>{Rdn:.2f}</b></td></tr>
            </table>
            <br>
            <p><b>Vout:</b> {vcalc:.3f} V (Target = {Vout_target:.3f} V)</p>
            <p><b style="color:red;">Error:</b> {best_error:.3f} V</p>
            <p><b style="color:blue;">Required Vin for exact target:</b> {Vin_required:.3f} V</p>
            """

            self.result_area.setHtml(result_html)
            self.circuit.set_values(up, dn, Vup, Vdn, vcalc)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ResistorDividerApp()
    window.show()
    sys.exit(app.exec_())
