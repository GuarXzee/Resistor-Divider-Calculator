import sys
import pandas as pd
import itertools
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QTextEdit, QVBoxLayout, QCheckBox, QHBoxLayout
)
from PyQt5.QtGui import QPainter, QPen, QFont, QColor, QBrush
from PyQt5.QtCore import Qt, QPointF


class CircuitWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.rup1 = None
        self.rup2 = None
        self.rdn1 = None
        self.rdn2 = None
        self.Vup = None
        self.Vdn = None
        self.Vout = None

    def set_values(self, up, dn, Vup, Vdn, Vout):
        """Update resistor values and voltages for drawing"""
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

        # Coordinates
        w = self.width()
        h = self.height()
        mid_x = w // 2
        top_y = 50
        mid_y = h // 2
        bot_y = h - 50

        pen = QPen(Qt.black, 2)
        painter.setPen(pen)

        # --- Draw Vup (orange box) ---
        if self.Vup is not None:
            painter.setBrush(QBrush(QColor("orange")))
            painter.drawRect(mid_x - 60, top_y - 30, 70, 25)
            painter.setFont(QFont("Arial", 9, QFont.Bold))
            painter.drawText(mid_x - 55, top_y - 12, f"{self.Vup:.2f} V")

        # --- Draw Vdn (orange box) ---
        if self.Vdn is not None:
            painter.setBrush(QBrush(QColor("orange")))
            painter.drawRect(mid_x - 60, bot_y + 5, 70, 25)
            painter.setFont(QFont("Arial", 9, QFont.Bold))
            painter.drawText(mid_x - 55, bot_y + 22, f"{self.Vdn:.2f} V")

        # --- Draw Vout (orange box) ---
        if self.Vout is not None:
            painter.setBrush(QBrush(QColor("orange")))
            painter.drawRect(mid_x + 65, mid_y - 12, 70, 25)
            painter.setFont(QFont("Arial", 9, QFont.Bold))
            painter.drawText(mid_x + 70, mid_y + 5, f"{self.Vout:.3f} V")

        # Reset brush
        painter.setBrush(Qt.NoBrush)

        # Draw wires
        painter.drawLine(mid_x, top_y, mid_x, bot_y)       # vertical
        painter.drawLine(mid_x, mid_y, mid_x + 65, mid_y)  # Vout branch

        # Draw resistors
        self.draw_resistor(painter, mid_x, top_y + 20, mid_y - 20,
                           label_up=self.rup1, label_down=self.rup2, name="Rup")
        self.draw_resistor(painter, mid_x, mid_y + 20, bot_y - 20,
                           label_up=self.rdn1, label_down=self.rdn2, name="Rdn")

    def draw_resistor(self, painter, x, y1, y2, label_up=None, label_down=None, name="R"):
        """Draw a resistor symbol (zigzag) with labels"""
        painter.setBrush(QBrush(QColor("yellow")))
        painter.drawRect(x - 20, y1, 40, (y2 - y1))
        painter.setBrush(Qt.NoBrush)

        # Zigzag
        step = (y2 - y1) // 6
        zigzag = []
        direction = 1
        for i in range(7):
            zigzag.append((x + direction * 10, y1 + i * step))
            direction *= -1
        painter.drawPolyline(*[QPointF(px, py) for px, py in zigzag])

        painter.setFont(QFont("Arial", 8))
        if label_up:
            painter.drawText(x + 25, (y1 + y2) // 2 - 10, f"{name}1={label_up:.2f} Ω")
        if label_down:
            painter.drawText(x + 25, (y1 + y2) // 2 + 10, f"{name}2={label_down:.2f} Ω")


class ResistorDividerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.prepare_pairs()
        self.load_pairs()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Voltage Divider Circuit - Resistor Pair Calculator")
        self.setGeometry(200, 100, 1000, 700)

        layout = QVBoxLayout()

        # Inputs
        self.input_v1 = QLineEdit()
        self.input_v2 = QLineEdit("0")
        self.input_vout = QLineEdit()
        layout.addWidget(QLabel("Vup:")); layout.addWidget(self.input_v1)
        layout.addWidget(QLabel("Vdn:")); layout.addWidget(self.input_v2)
        layout.addWidget(QLabel("Desired Vout:")); layout.addWidget(self.input_vout)

        # Override controls
        override_layout = QHBoxLayout()
        self.override_box = QLineEdit()
        self.override_box.setPlaceholderText("Override resistor value (Ω)")
        self.chk_rup = QCheckBox("Override Rup")
        self.chk_rdn = QCheckBox("Override Rdn")
        override_layout.addWidget(self.override_box)
        override_layout.addWidget(self.chk_rup)
        override_layout.addWidget(self.chk_rdn)
        layout.addLayout(override_layout)

        # Button
        self.button = QPushButton("Calculate")
        layout.addWidget(self.button)
        self.button.clicked.connect(self.calculate_divider)

        # Result area
        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        layout.addWidget(self.result_area)

        # Circuit drawing
        self.circuit = CircuitWidget()
        self.circuit.setMinimumHeight(350)
        layout.addWidget(self.circuit)

        self.setLayout(layout)

    def prepare_pairs(self):
        """Generate resistor pairs with 3-decimal precision"""
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
        df = pd.DataFrame(pairs)
        df.to_csv("resistor_pairs.csv", index=False)

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
            self.result_area.setText(
                f"Best Match:\n"
                f" Rup1 = {up['R1']:.2f} Ω, Rup2 = {up['R2'] if pd.notna(up['R2']) else '-'}\n"
                f" Rdn1 = {dn['R1']:.2f} Ω, Rdn2 = {dn['R2'] if pd.notna(dn['R2']) else '-'}\n"
                f" Req_up = {up['Req']:.2f} Ω\n"
                f" Req_dn = {dn['Req']:.2f} Ω\n"
                f" Vout ≈ {vcalc:.3f} V (target {Vout_target:.3f} V)\n"
                f" Error = {best_error:.3f} V"
            )
            self.circuit.set_values(up, dn, Vup, Vdn, vcalc)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ResistorDividerApp()
    window.show()
    sys.exit(app.exec_())
