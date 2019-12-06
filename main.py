from db_part import *


def get_current_user_type():
    return request.cookies.get("user_type")


@app.context_processor
def global_vars():
    return dict(user_type=get_current_user_type())


@app.before_request
def check_is_logged_in():
    user_id = request.cookies.get("user_id")
    if not user_id:
        if len(pokaz_user()) != 0:
            if not any(x in request.path for x in ["login", 'static']):
                return redirect(url_for("login"))


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template("index.html")


@app.route('/flights', methods=['GET', 'POST'])
def flights():
    return render_template("flights.html")


@app.route('/schedule', methods=['GET', 'POST'])
def schedule():
    notification = None
    if request.method == "POST":
        req = request.values.to_dict()
        if 'new' in req:
            notification = dodaj_harmonogram(nr_lotu=req['nr_flight'], linia_lotnicza=req['line'],
                                             start_lotnisko=req['from'], finish_lotnisko=req['to'],
                                             dzien_tygodnia=req['day'], start_godzina=req['time_start'],
                                             finish_godzina=req['time_finish'], cena_podstawowa=req['price'])
        elif 'remove' in req:
            notification = usun_harmonogram(nr_lotu=req['remove'])
    linie = pokaz_linie()
    lotniska = pokaz_lotniska()
    harmonogram = pokaz_harmonogram()
    return render_template("schedule.html", linie=linie, lotniska=lotniska, harmonogram=harmonogram, days=days_pl,
                           notification=notification)


@app.route('/lines', methods=['GET', 'POST'])
def lines():
    notification = None
    if request.method == 'POST':
        req = request.values.to_dict()
        if 'new' in req:
            notification = dodaj_linie(req['nazwa'], req['kraj'])
        if 'remove' in req:
            notification = usun_linie(nazwa=req['remove'])
    linie = pokaz_linie()
    kraje = get_countries_list()
    return render_template("lines.html", linie=linie, notification=notification, kraje=kraje)


@app.route('/lines/<line>', methods=['GET', 'POST'])
def line_name(line):
    linia = pokaz_linie(line)
    if not linia:
        abort(404)
    notification = None
    if request.method == 'POST':
        req = request.values.to_dict()
        if 'new-samolot' in req:
            notification = dodaj_samolot(nr_boczny=req['nr_boczny'], marka=req['marka'], model=req['model'],
                                         linia_nazwa=linia.nazwa, pojemnosc=req['pojemnosc'],
                                         zasieg=req['zasieg'])
        elif 'remove-samolot' in req:
            notification = usun_samolot(nr_boczny=req['remove'])
        elif 'new-pilot' in req:
            notification = dodaj_pilota(imie=req['imie'], nazwisko=req['nazwisko'], linia_nazwa=linia.nazwa)
    samoloty = pokaz_samoloty(linia=line)
    piloci = pokaz_pilotow(linia=line)
    return render_template("line.html", linia=linia, samoloty=samoloty, piloci=piloci, notification=notification)


@app.route('/airports', methods=['GET', 'POST'])
def airports():
    notification = None
    if request.method == 'POST':
        req = request.values.to_dict()
        if 'new' in req:
            notification = dodaj_lotnisko(kod=req['code'], kraj=req['country'],
                                          miasto=req['city'], m_na_mapie=req['map'], strefa_czasowa=req['timezone'])
        elif 'edit' in req:
            notification = zmodyfikuj_lotnisko(kod=req['edit'], nowy_kod=req['code'], kraj=req['country'],
                                               miasto=req['city'], m_na_mapie=req['map'],
                                               strefa_czasowa=req['timezone'])
        elif 'remove' in req:
            notification = usun_lotnisko(kod=req['remove'])
    kraje = get_countries_list()
    lotniska = pokaz_lotniska()
    return render_template('airports.html', kraje=kraje, notification=notification, lotniska=lotniska)


@app.route('/account', methods=['GET', 'POST'])
def account():
    return render_template('account.html')


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    notification = None
    if request.method == "POST":
        req = request.values.to_dict()
        if 'new' in req:
            notification = dodaj_user(email=req['email'], password=req['password'],
                                      password_repeat=req['password-repeat'], imie=req['name'], nazwisko=req['surname'],
                                      u_type=req['type'])
        elif 'remove' in req:
            notification = usun_user(user_id=req['remove'])
    users = pokaz_user()
    return render_template('admin.html', users=users, notification=notification)


def log_in(user):
    resp = make_response(redirect(url_for("index")))
    resp.set_cookie("user_id", str(user.user_id))
    resp.set_cookie("user_token", user.token)
    resp.set_cookie("user_type", user.typ)
    return resp


@app.route('/login', methods=["GET", "POST"])
def login():
    notification = None
    if request.method == "POST":
        req = request.values.to_dict()
        if 'login' in req:
            user, notification = check_user_credentials(req['email'], req['current-password'])
            if user:
                # resp = make_response(redirect(index))
                # resp.set_cookie("user_id", str(user.user_id))
                # resp.set_cookie("user_token", user.token)
                # resp.set_cookie("user_type", user.typ)
                return log_in(user)
        elif "signup" in req:
            notification = dodaj_user(imie=req['name'], nazwisko=req['surname'], email=req['email'],
                                      password=req['current-password'], password_repeat=req['password-repeat'],
                                      u_type="user")
            if notification[0] == "success":
                user = pokaz_user(email=req['email'])
                if user:
                    return log_in(user)
    return render_template("login.html", notification=notification)


@app.route("/logout")
def logout():
    resp = make_response(redirect(url_for("login")))
    resp.set_cookie("user_id", "", expires=0)
    resp.set_cookie("user_token", "", expires=0)
    resp.set_cookie("user_type", "", expires=0)
    return resp


if __name__ == '__main__':
    app.run(debug=True)
