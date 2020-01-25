from db_part import *


def get_current_user_type():
    return request.cookies.get("user_type")


def get_current_user_id():
    return request.cookies.get("user_id")


def check_city_code(code):
    def check_code(airport):
        return code == airport.kod

    return check_code


def convert_data_format(data_wrong):
    return ".".join(list(reversed(data_wrong.split("-"))))


@app.context_processor
def global_vars():
    return dict(user_type=get_current_user_type(), suma_biletow=suma_biletow, enumerate=enumerate,
                check_city_code=check_city_code, filter=filter, list=list, czas_podrozy=policz_czas_podrozy,
                czas_przesiadki=policz_czas_przesiadki, isinstance=isinstance, licz_bilet=licz_bilet)


# @app.before_request
# def check_is_logged_in():
#     user_id = request.cookies.get("user_id")
#     if not user_id:
#         if len(pokaz_user()) != 0:
#             if not any(x in request.path for x in ["login", 'static']):
#                 return redirect(url_for("login"))


@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    request_data = None
    if request.method == "POST":
        req = request.values.to_dict()
        if 'from' in req:
            result = szukaj_podrozy(req['from'], req['to'], req['go-date'])
            request_data = {"from": req["from"], "to": req["to"], "go-date": convert_data_format(req["go-date"])}
    lotniska = pokaz_lotniska()
    return render_template("index.html", result=result, request_data=request_data, lotniska=lotniska)


@app.route("/order", methods=["GET", "POST"])
def order():
    notification = None
    ls_realizacji = []
    page_mode = None
    user = None
    rabaty = None
    to_reconfirm = False
    r_nums = request.args.get("r_nums")
    if get_current_user_type() == "user":
        if request.method == "POST":
            req = request.values.to_dict()
            # returns for example: {'discount': 'WSXVIWSCSD', 'cena': '1872.5', 'agree': 'on', 'r_nums': '69;89;'}
            if r_nums:
                if 'agree' not in req or req['agree'] != 'on':
                    notification = ["danger", "Musisz potwierdzić warunki korzystania z serwisu"]
                else:
                    notification = dodaj_podroz(r_nums.split(";")[:-1], req['cena'], get_current_user_id(),
                                                rabat=req['discount'] if 'dicount' in req else None, bagaz=req['bagaz'])
            else:
                notification = ["danger", "Loty nie zostali wybrane. Spróbuj ponownie"]
        elif request.method == "GET" or to_reconfirm:
            if r_nums:
                page_mode = "confirm_order"
                for r_num in r_nums.split(";"):
                    if isinstance(r_num, str) and r_num.isnumeric():
                        ls_realizacji.append(pokaz_realizacje_lotow(id_rlotu=int(r_num)))
            if not page_mode:
                notification = ["danger", "Niepoprawny dostęp do strony. Spróbuj jeszcze raz"]
            user = pokaz_user(user_id=get_current_user_id())
            rabaty = pokaz_rabaty(user_id=get_current_user_id())
    return render_template("order.html", ls_realizacji=ls_realizacji, user=user, rabaty=rabaty,
                           notification=notification)


@app.route('/flights', methods=['GET', 'POST'])
def flights():
    notification = None
    if request.method == "POST":
        req = request.values.to_dict()
        if 'update-all' in req:
            notification = zauktualizuj_realizacje_lotow()
        if 'new' in req:
            notification = dodaj_harmonogram(nr_lotu=req['nr_flight'], linia_lotnicza=req['line'],
                                             start_lotnisko=req['from'], finish_lotnisko=req['to'],
                                             dzien_tygodnia=req['day'], start_godzina=req['time_start'],
                                             czas_trwania=req['czas_trwania'], cena_podstawowa=req['price'])
        elif 'edit' in req:
            notification = zmodyfikuj_harmonogram(nr_lotu=req['edit'], linia_lotnicza=req['line'],
                                                  start_lotnisko=req['from'], finish_lotnisko=req['to'],
                                                  dzien_tygodnia=req['day'], start_godzina=req['time_start'],
                                                  czas_trwania=req['czas_trwania'], cena_podstawowa=req['price'])
        elif 'remove' in req:
            notification = usun_harmonogram(nr_lotu=req['remove'])
    linie = pokaz_linie()
    lotniska = pokaz_lotniska()
    harmonogram = pokaz_harmonogram()
    return render_template("schedule.html", linie=linie, lotniska=lotniska, harmonogram=harmonogram, days=days_pl,
                           notification=notification)


@app.route('/flights/<nr_lotu>', methods=["GET", "POST"])
def flight(nr_lotu):
    harm_note = pokaz_harmonogram(nr_lotu=nr_lotu)
    if not harm_note:
        abort(404)
    notification = None
    if request.method == "POST":
        req = request.values.to_dict()
        if 'edit' in req:
            notification = zmodyfikuj_realizacje_lotu(id_rlotu=req['edit'], new_samolot=req['samolot'],
                                                      new_pilot1=req['pilot-1'], new_pilot2=req['pilot-2'])
    realizacje = pokaz_realizacje_lotow(nr_lotu=nr_lotu)
    samoloty = pokaz_samoloty(linia=harm_note.linia_lotnicza_nazwa)
    piloci = pokaz_pilotow(linia=harm_note.linia_lotnicza_nazwa)
    return render_template("flights.html", notification=notification, realizacje=realizacje, harm_note=harm_note,
                           samoloty=samoloty, piloci=piloci)


@app.route('/lines', methods=['GET', 'POST'])
def lines():
    notification = None
    if request.method == 'POST':
        req = request.values.to_dict()
        if 'new' in req:
            notification = dodaj_linie(req['nazwa'], req['kraj'])
        elif 'edit' in req:
            # TODO
            notification = zmodyfikuj_linie(req['edit'], req['edit'], req['kraj'])
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
        elif 'edit-samolot' in req:
            notification = zmodyfikuj_samolot(nr_boczny=req['edit-samolot'], marka=req['marka'], model=req['model'],
                                              linia_nazwa=linia.nazwa, pojemnosc=req['pojemnosc'], zasieg=req['zasieg'])
        elif 'remove-samolot' in req:
            notification = usun_samolot(nr_boczny=req['remove-samolot'])
        elif 'new-pilot' in req:
            notification = dodaj_pilota(imie=req['imie'], nazwisko=req['nazwisko'], linia_nazwa=linia.nazwa)
        elif 'edit-pilot' in req:
            notification = zmodyfikuj_pilota(id_pil=req['edit-pilot'], imie=req['name'], nazwisko=req['surname'])
        elif 'remove-pilot' in req:
            notification = usun_pilota(id_pil=req['remove-pilot'])
    samoloty = pokaz_samoloty(linia=line)
    piloci = pokaz_pilotow(linia=line)
    harmonogram = pokaz_harmonogram(linia_lotnicza=line)
    return render_template("line.html", linia=linia, samoloty=samoloty, piloci=piloci, harmonogram=harmonogram,
                           notification=notification)


@app.route('/airports', methods=['GET', 'POST'])
def airports():
    notification = None
    if request.method == 'POST':
        req = request.values.to_dict()
        if 'new' in req:
            notification = dodaj_lotnisko(kod=req['code'], kraj=req['country'],
                                          miasto=req['city'], m_na_mapie=req['map'], strefa_czasowa=req['timezone'])
        elif 'edit' in req:
            notification = zmodyfikuj_lotnisko(kod=req['edit'], nowy_kod=req['edit'], kraj=req['country'],
                                               miasto=req['city'], m_na_mapie=req['map'],
                                               strefa_czasowa=req['timezone'])
        elif 'remove' in req:
            notification = usun_lotnisko(kod=req['remove'])
    kraje = get_countries_list()
    lotniska = pokaz_lotniska()
    return render_template('airports.html', kraje=kraje, notification=notification, lotniska=lotniska)


@app.route('/account', methods=['GET', 'POST'])
@app.route('/account/<user_id>', methods=['GET', 'POST'])
def account(user_id=None):
    if user_id and get_current_user_type() != "admin" or \
            isinstance(user_id, type(None)) and get_current_user_type() == "admin":
        return redirect(url_for('index'))
    notification = None
    if request.method == "POST":
        req = request.values.to_dict()
        if "new" in req:
            notification = dodaj_rabat(user_id if user_id else get_current_user_id(), req['procent'],
                                       req['data_waznosci'])
        elif "remove-rabat" in req:
            notification = usun_rabat(req['remove-rabat'])
        elif "edit-user" in req:
            notification = zmodyfikuj_user(user_id=user_id, imie=req['imie'], nazwisko=req['nazwisko'],
                                           email=req['email'], new_password=req['new-password'],
                                           new_r_password=req['new-password-repeat'])
        elif "cancel-podroz" in req:
            notification = usun_podroz(nr_rezerwacji=req['cancel-podroz'])
        elif "remove-podroz" in req:
            notification = usun_podroz(nr_rezerwacji=req['cancel-podroz'])
    admin = False
    u_id = get_current_user_id()
    if not isinstance(user_id, type(None)):
        user = pokaz_user(user_id=user_id)
        admin = True
    else:
        user = pokaz_user(user_id=u_id)
    rabaty = pokaz_rabaty(user.user_id)
    podroze_tmp = pokaz_podroz(user_id=user.user_id)
    podroze = {}
    for podroz in podroze_tmp:
        if not podroz[1].realizacja_lotu:
            podroze[podroz[0]] = None
        if podroz[0] not in podroze.keys():
            podroze[podroz[0]] = [podroz[1]]
        else:
            if isinstance(podroze[podroz[0]], list):
                podroze[podroz[0]].append(podroz[1])
    return render_template('account.html', user=user, rabaty=rabaty, u_id=u_id, notification=notification, admin=admin,
                           podroze=podroze)


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    notification = None
    if request.method == "POST":
        req = request.values.to_dict()
        if 'new' in req:
            notification = dodaj_user(email=req['email'], password=req['password'],
                                      password_repeat=req['password-repeat'], imie=req['name'], nazwisko=req['surname'],
                                      u_type=req['type'])
        elif 'edit' in req:
            notification = zmodyfikuj_user(user_id=req['edit'], imie=req['name'], nazwisko=req['surname'],
                                           email=req['email'], new_password=req['password'],
                                           new_r_password=req['password-repeat'], typ=req['u_type'])
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
    resp = make_response(redirect(url_for("index")))
    resp.set_cookie("user_id", "", expires=0)
    resp.set_cookie("user_token", "", expires=0)
    resp.set_cookie("user_type", "", expires=0)
    return resp


if __name__ == '__main__':
    app.run(debug=True)
