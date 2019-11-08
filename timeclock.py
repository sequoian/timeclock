import sqlite3
import argparse
from datetime import datetime
from tabulate import tabulate

class Timeclock:
    def __init__(self):
        self.db = Database("time.db")

    def clock_in(self, args):
        latest_shift = self.get_latest_shift()
        now = datetime.now()
        if self.can_clock_in(latest_shift):
            self.db.clock_in(int(now.timestamp()))
            print("Clocked in at {}".format(self.format_time(now)))
        else:
            delta = now - datetime.fromtimestamp(latest_shift[1])
            print("Already clocked in for {}".format(self.format_delta_seconds(int(delta.total_seconds()))))

    def clock_out(self, args):
        latest_shift = self.get_latest_shift()
        if self.can_clock_in(latest_shift):
            print("Not clocked in")
        else:
            now = datetime.now()
            delta = now - datetime.fromtimestamp(latest_shift[1])
            self.db.clock_out(latest_shift[0], int(now.timestamp()))
            print("Clocked out at {}, worked for {}".format(
                  self.format_time(now), self.format_delta_seconds(int(delta.total_seconds()))))

    def list_shifts(self, args):
        rows = self.db.get_latest_shifts(args.limit)
        if rows:
            self.tabulate_shifts(rows)
        else:
            print("No shifts worked")

    def show_status(self, args):
        latest_shift = self.get_latest_shift()
        if self.can_clock_in(latest_shift):
            print("Currently clocked out")
        else:
            delta = datetime.now() - datetime.fromtimestamp(latest_shift[1])
            print("Currently clocked in for {}".format(self.format_delta_seconds(int(delta.total_seconds()))))

    def show_today(self, args):
        shifts = self.db.get_shifts_today()
        duration = 0
        for shift in shifts:
            if not shift[2]:
                duration += datetime.now().timestamp() - shift[1]
            else:
                duration += shift[2] - shift[1]
        print("------------------------")
        print("Worked today for {}".format(self.format_delta_seconds(int(duration))))
        print("------------------------")

        if shifts:
            self.tabulate_shifts(shifts)

    def get_latest_shift(self):
        latest_shift = self.db.get_latest_shifts(1)
        if not latest_shift:
            return None
        else:
            return latest_shift[0]

    def can_clock_in(self, latest_shift):
        if not latest_shift or latest_shift[2] != None:
            return True
        else:
            return False

    def format_time(self, datetime):
        return datetime.strftime("%I:%M %p")

    def format_delta_seconds(self, seconds):
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        return "{}:{:02d}:{:02d}".format(hours, minutes, seconds)

    def tabulate_shifts(self, rows):
        table = list()
        for row in rows:
            shift = list()
            time = datetime.fromtimestamp(row[1])
            shift.append(time.strftime("%x"))
            shift.append(self.format_time(time))
            if row[2]:
                shift.append(self.format_time(datetime.fromtimestamp(row[2])))
                seconds = row[2] - row[1]
                shift.append(self.format_delta_seconds(seconds))
            else:
                shift.append('')
                shift.append('')
            table.append(shift)
        
        headers = ["Day", "In", "Out", "Time"]
        print(tabulate(table, headers))

    def run(self):
        """ Run the application """
        # Configure argument parser
        parser = argparse.ArgumentParser(prog="clock")
        subparsers = parser.add_subparsers()
        clock_in = subparsers.add_parser("in")
        clock_in.set_defaults(func=self.clock_in)
        clock_out = subparsers.add_parser("out")
        clock_out.set_defaults(func=self.clock_out)
        status = subparsers.add_parser("status")
        status.set_defaults(func=self.show_status)
        listing = subparsers.add_parser("list")
        listing.add_argument("limit", type=int, default=10, nargs="?")
        listing.set_defaults(func=self.list_shifts)
        today = subparsers.add_parser("today")
        today.set_defaults(func=self.show_today)

        args = parser.parse_args()

        try:
            args.func(args)
        except AttributeError:
            parser.print_usage()


class Database:
    def __init__(self, dbpath):
        self.conn = sqlite3.connect(dbpath)
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

    def clock_in(self, intime):
        sql = "INSERT INTO shifts (cin) VALUES (?)"
        self.cursor.execute(sql, (intime,))
        self.conn.commit()
        return self.cursor.lastrowid

    def clock_out(self, uid, outtime):
        sql = "UPDATE shifts SET cout = ? WHERE id = ?"
        self.cursor.execute(sql, (outtime, uid))
        self.conn.commit()
    
    def get_latest_shifts(self, limit=40):
        sql = "SELECT * FROM shifts ORDER BY cin DESC LIMIT ?"
        self.cursor.execute(sql, (limit,))
        return self.cursor.fetchall()

    def get_shifts_today(self):
        start_of_day = int(datetime.now().replace(hour=0, minute=0, 
                           second=0, microsecond=0).timestamp())
        sql = "SELECT * FROM shifts WHERE cin >= ? ORDER BY cin DESC"
        self.cursor.execute(sql, (start_of_day,))
        return self.cursor.fetchall()


if __name__ == "__main__":
    app = Timeclock()
    app.run()