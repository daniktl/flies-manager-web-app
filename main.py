from db_part import *


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template("index.html")


@app.route('/flights', methods=['GET', 'POST'])
def flights():
    return render_template("flights.html")


@app.route('/schedule', methods=['GET', 'POST'])
def schedule():
    return render_template("schedule.html")


@app.route('/lines', methods=['GET', 'POST'])
def lines():
    notification = None
    if request.method == 'POST':
        req = request.values.to_dict()
        if 'new' in req:
            notification = dodaj_linie(req['nazwa'], req['kraj'])
    linie = pokaz_linie()
    return render_template("lines.html", linie=linie, notification=notification)


@app.route('/lines/<line>', methods=['GET', 'POST'])
def line_name(line):
    linia = pokaz_linie(line)
    if not linia:
        abort(404)
    samoloty = pokaz_samoloty(linia=line)
    return render_template("line.html", linia=linia, samoloty=samoloty)


@app.route('/account', methods=['GET', 'POST'])
def account():
    return render_template('account.html')


if __name__ == '__main__':
    app.run(debug=True)
