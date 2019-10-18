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

        # data
        self.clockedin = False
        self.intime = None
        self.outtime = None
        self.rowid = None

        # thread
        self.clock = Thread(target=self.tick, daemon=True)

        # widgets
        self.button = QtWidgets.QPushButton("Clock In")
        self.text = QtWidgets.QLabel("00:00:00")
        self.text.setAlignment(QtCore.Qt.AlignCenter)

        # layouts
        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addWidget(self.button)
        self.layout.addWidget(self.text)
        self.setLayout(self.layout)

        # connections
        self.button.clicked.connect(self.buttonPress)

        # database
        self.db = Database()

        # check if a shift is in progress
        shifts = self.db.getLatestShifts()
        latest = shifts[0]
        if latest[2] is None:
            self.clockedin = True
            self.rowid = latest[0]
            self.intime = latest[1]
            self.button.setText("Clock Out")
            self.clock.start()
            
        # print shifts
        # for x in shifts:
        #     inday = datetime.fromtimestamp(x[1]).strftime("%x")
        #     intime = datetime.fromtimestamp(x[1]).strftime("%I:%M:%S")
        #     outtime = datetime.fromtimestamp(x[2]).strftime("%I:%M:%S")
        #     elapsed = getElapsed(x[2], x[1])
        #     elapsed = strfdelta(elapsed)
        #     print("Day: {}, In: {}, Out: {}, Time: {}".format(inday, intime, outtime, elapsed))

    def buttonPress(self):
        self.clockedin = False if self.clockedin else True
        self.clockin() if self.clockedin else self.clockout()

        self.button.setText("Clock Out" if self.clockedin else "Clock In")

    def clockin(self):
        self.intime = time.time()
        self.rowid = self.db.clockin(int(self.intime))
        self.clock.start()

    def clockout(self):
        self.outtime = time.time()
        self.db.clockout(self.rowid, int(self.outtime))
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
    widget.resize(200, 100)
    widget.show()

    sys.exit(app.exec_())