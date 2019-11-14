from flask import Flask, url_for, render_template

app = Flask(__name__)


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
    return render_template("lines.html")

@app.route('/account', methods=['GET', 'POST'])
def account():
    return render_template('account.html')

if __name__ == '__main__':
    app.run(debug=True)
