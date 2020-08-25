from flask import Flask, render_template, request, send_from_directory, redirect, url_for
import sqlite3 as sql
import csv
import datetime
import json
import pandas as pd

app = Flask(__name__)

dict_ = {}


def write_file(rows):
    f = open('static/download.csv', 'w')
    c = csv.writer(f, dialect='excel')
    c.writerow(["id", "date", "time"])
    for row in rows:
        c.writerow([row["id"], row["date"], row["time"]])
    f.close()


@app.route('/', methods=['GET', 'POST'])
def home():
    error = None
    search_id = ""
    con = sql.connect("static/users.db")
    con.row_factory = sql.Row
    cur = con.cursor()

    if request.method == 'POST':
        error = None
        result = request.form

        if "search_id" in result.keys():
            search_id = result["search_id"]
        else:
            id_ = result["id"]
            from_ = result["from"]
            till_ = result["till"]
            print(till_ == "")
            if cur.execute("select * from users where `id`= ? order by `date` ASC", (id_,)).fetchone() is None:
                error = "Enter a valid ID"

            else:
                if from_ == "" and till_ == "":
                    print("only id")
                    cur.execute("select * from users where `id`= ? order by `date` ASC",
                                (id_,))
                elif from_ == "" and till_ != "":
                    print("no date1")
                    cur.execute("select * from users where `id`= ? and `date` <= ? order by `date` ASC",
                                (id_, till_))
                elif from_ != "" and till_ == "":
                    print("no date2")
                    cur.execute("select * from users where `id`= ? and `date` >= ? order by `date` ASC",
                                (id_, from_))

                else:
                    if from_ > till_:
                        print("d1>d2")
                        error = "Enter valid dates"
                    else:
                        cur.execute(
                            "select * from users where `id`= ? and `date` >= ? and `date` <= ? order by `date` ASC",
                            (id_, from_, till_))
                rows = cur.fetchall();
                n = len(rows)

                # print(rows, type(rows))

                ####################################

                from datetime import timedelta

                if (n > 0):
                    sdate = datetime.datetime.strptime(rows[0]["date"], '%Y-%m-%d').date()  # start date
                    edate = datetime.datetime.strptime(rows[-1]["date"], '%Y-%m-%d').date()  # end date

                    delta = edate - sdate  # as timedelta
                    for i in range(delta.days + 1):
                        day = sdate + timedelta(days=i)
                        dict_[str(day)] = 0

                    for row in rows:
                        dict_[row["date"]] = dict_[row["date"]] + 1

                # for key in dict_:
                #     print(key,dict_[key])

                # labels = [1,2,3,4]
                labels = []
                values = []
                for key in dict_:
                    labels.append(key)
                    values.append(dict_[key])
                labels = json.dumps(labels)
                values = json.dumps(values)
                print(labels)
                if error is None:
                    write_file(rows)
                    return render_template("search_result.html", rows=rows, id=id_, date1=from_, date2=till_, n=n,
                                           max=5, labels=labels, values=values)

    if search_id == "":
        cur.execute("select DISTINCT `id` FROM users order by `id` ASC")
    else:
        search_id = "%" + search_id + "%"
        cur.execute("select DISTINCT `id` FROM users where `id` like ? order by `id` ASC", (search_id,))
    rows = cur.fetchall();
    ids, counts, date1, date2 = [], [], [], []
    for row in rows:
        cur_id = row["id"]
        # print(len(cur_id), cur_id)
        ids.append(cur_id)
        cur.execute("select `date` FROM users where `id`=?", (cur_id,))
        cur_l = cur.fetchall()
        date1.append(cur_l[0]["date"])
        date2.append(cur_l[-1]["date"])
        count = len(cur_l)
        counts.append(count)
    l = len(ids)
    dict_.clear()
    cur.execute("select * from users")
    rows = cur.fetchall();
    write_file(rows)
    return render_template("index.html", ids=ids, counts=counts, date1=date1, date2=date2, length=l, error=error)


@app.route('/download')
def download():
    return send_from_directory('static/', 'download.csv', as_attachment=True)


@app.route('/back')
def back():
    return redirect(url_for('home'))


@app.route('/graph')
def graph():
    labels = []
    values = []
    for key in dict_:
        labels.append(key)
        values.append(dict_[key])
    return render_template('graph.html', title='Usage Tracker', max=5, labels=labels, values=values)


if __name__ == "__main__":
    app.run(debug=True)
