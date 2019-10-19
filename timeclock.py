import sys
import time
from datetime import datetime, timedelta
from threading import Thread
from PySide2 import QtCore, QtWidgets, QtGui
import sqlite3

def strfdelta(seconds):
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)

def getElapsed(after, before):
    elapsed = after - before
    return int(timedelta(seconds=elapsed).total_seconds())

class TimeClock(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Timeclock")

        # data
        self.clockedin = False
        self.intime = None
        self.outtime = None
        self.rowid = None
        self.tabledata = []

        # thread
        self.clock = Thread(target=self.tick, daemon=True)

        # widgets
        self.button = QtWidgets.QPushButton("Clock In")
        self.text = QtWidgets.QLabel("00:00:00")
        self.text.setAlignment(QtCore.Qt.AlignCenter)
        self.table = QtWidgets.QTableWidget(40, 4)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().hide()
        self.table.setItem(1, 1, QtWidgets.QTableWidgetItem("Hello"))

        # layouts
        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addWidget(self.button)
        self.layout.addWidget(self.text)
        self.layout2 = QtWidgets.QVBoxLayout()
        self.layout2.addLayout(self.layout)
        self.layout2.addWidget(self.table)
        self.setLayout(self.layout2)

        # connections
        self.button.clicked.connect(self.buttonPress)

        # query database
        self.db = Database()
        self.tabledata = self.db.getLatestShifts()

        # check if shift is in progress
        try:
            latest = self.tabledata[0]
            if latest[2] is None:
                self.clockedin = True
                self.rowid = latest[0]
                self.intime = latest[1]
                self.button.setText("Clock Out")
                self.clock.start()
        except IndexError:
            pass

        self.button.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_C))
        self.renderTable()
        
    def buttonPress(self):
        self.clockedin = False if self.clockedin else True
        self.clockin() if self.clockedin else self.clockout()

        self.button.setText("Clock Out" if self.clockedin else "Clock In")

        # need to reset shortcut after text change
        self.button.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_C))

    def clockin(self):
        self.intime = time.time()
        self.rowid = self.db.clockin(int(self.intime))
        self.clock.start()
        self.tabledata.insert(0, (self.rowid, int(self.intime), None))
        self.renderTable()

    def clockout(self):
        self.outtime = time.time()
        self.db.clockout(self.rowid, int(self.outtime))
        self.tabledata[0] = (self.rowid, int(self.intime), int(self.outtime))
        self.renderTable()
        self.intime = None
        self.rowid = None
        self.text.setText("00:00:00")
        
        # Create a new thread since threads can only be started once
        self.clock = Thread(target=self.tick, daemon=True)

    def tick(self):
        while (self.clockedin):
            elapsed = getElapsed(time.time(), self.intime)
            self.text.setText(strfdelta(elapsed))
            time.sleep(1) 

    def renderTable(self):
        self.table.setRowCount(len(self.tabledata)+1)

        # print header
        self.table.setItem(0, 0, QtWidgets.QTableWidgetItem("Day"))
        self.table.setItem(0, 1, QtWidgets.QTableWidgetItem("In"))
        self.table.setItem(0, 2, QtWidgets.QTableWidgetItem("Out"))
        self.table.setItem(0, 3, QtWidgets.QTableWidgetItem("Time"))

        # print self.tabledata
        for num, shift in enumerate(self.tabledata):
            inday = datetime.fromtimestamp(shift[1]).strftime("%x")
            intime = datetime.fromtimestamp(shift[1]).strftime("%I:%M:%S %p")
            try:
                outtime = datetime.fromtimestamp(shift[2]).strftime("%I:%M:%S %p")
                elapsed = getElapsed(shift[2], shift[1])
                elapsed = strfdelta(elapsed)
            except TypeError:
                outtime = ""
                elapsed = ""
            
            self.table.setItem(num+1, 0, QtWidgets.QTableWidgetItem(inday))
            self.table.setItem(num+1, 1, QtWidgets.QTableWidgetItem(intime))
            self.table.setItem(num+1, 2, QtWidgets.QTableWidgetItem(outtime))
            self.table.setItem(num+1, 3, QtWidgets.QTableWidgetItem(elapsed))

        self.table.resizeColumnsToContents()

class Database:
    def __init__(self):
        self.conn = sqlite3.connect("test.db")
        self.cursor = self.conn.cursor()

        # Create the tables if they don't exist
        createtable = """
            CREATE TABLE IF NOT EXISTS shifts (
                id integer PRIMARY KEY,
                cin integer NOT NULL,
                cout integer
            )
            """
        self.cursor.execute(createtable)

    def clockin(self, intime):
        sql = "INSERT INTO shifts (cin) VALUES (?)"
        self.cursor.execute(sql, (intime,))
        self.conn.commit()
        return self.cursor.lastrowid

    def clockout(self, uid, outtime):
        sql = "UPDATE shifts SET cout = ? WHERE id = ?"
        self.cursor.execute(sql, (outtime, uid))
        self.conn.commit()
    
    def getLatestShifts(self, limit=40):
        sql = "SELECT * FROM shifts ORDER BY cin DESC LIMIT ?"
        self.cursor.execute(sql, (limit,))
        return self.cursor.fetchall()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = TimeClock()
    widget.resize(300, 250)
    widget.show()

    sys.exit(app.exec_())