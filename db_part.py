from sqlalchemy import create_engine, String, Integer, Column, DateTime, Boolean, Text, desc, func, ForeignKey, \
    ForeignKeyConstraint, Float, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError, DisconnectionError, ProgrammingError, OperationalError
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.sql.expression import false, true, case, not_, and_
import os, numpy, datetime, warnings, time, random, json
from multiprocessing import Process, Manager, Semaphore
from multiprocessing.managers import BaseManager
from contextlib import contextmanager

from flask import Flask, url_for, render_template, abort, request, redirect, make_response
from flask_sqlalchemy import SQLAlchemy
import urllib, re
from passlib.hash import bcrypt
from string import ascii_letters, digits

app = Flask(__name__)

with open("data/db_credentials") as file:
    db_credentials = json.load(file)

#   Go to the data/db_credentials file
# | data
# | --> db_credentials
#   and replace credentials with your created before


app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://{username}:{password}@{host}/{db_name}?charset=utf8'.format(
    username=db_credentials['username'],
    password=db_credentials['password'],
    host=db_credentials['host'],
    db_name=db_credentials['database_name']
)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

dir_path = os.path.dirname(os.path.realpath(__file__))


def check_empty(x):
    if isinstance(x, list):
        if all([y != "" for y in x]):
            return False
    return True

@contextmanager
def session_handler():
    session = db.session
    try:
        session.flush()
        yield session
        session.commit()
    except IntegrityError:
        print("Already exists")
        session.rollback()
    except Exception as exp:
        print(exp)
        session.rollback()


def get_countries_list():
    with open(os.path.join(dir_path, "data", "countries")) as file:
        ls = file.read().splitlines()
        return ls


days_pl = {
    0: "Poniedziałek",
    1: "Wtorek",
    2: "Środa",
    3: "Czwartek",
    4: "Piątek",
    5: "Sobota",
    6: "Niedziela"
}


class User(db.Model):
    __tablename__ = 'user'

    user_id = Column('id_u', Integer, primary_key=True, autoincrement=True)
    haslo = Column('haslo', String(300), nullable=False)
    typ = Column('typ', String(32), default='user')
    email = Column('email', String(32), nullable=False)
    imie = Column('imie', String(32), nullable=False)
    nazwisko = Column('nazwisko', String(32), nullable=False)
    token = Column("token", String(64), nullable=False)

    def __init__(self, email, password, name, surname, type):
        self.email = email
        self.haslo = bcrypt.encrypt(password)
        self.imie = name
        self.nazwisko = surname
        self.typ = type
        self.token = "".join([random.choice(ascii_letters+digits) for _ in range(64)])

    def validate_password(self, password):
        return bcrypt.verify(password, self.haslo)

    rabat = relationship("Rabat", cascade="all")

    def is_admin(self):
        return self.typ == 'admin'

    def get_type(self):
        return "Użytkownik" if self.typ == "user" else "Administrator"


class Rabat(db.Model):
    __tablename__ = 'rabat'

    kod = Column('kod', String(10), primary_key=True, nullable=False)
    procent = Column('procent', Integer, nullable=False)
    data_waznosci = Column('data_waznosci', DateTime, nullable=False)

    user_id = Column("user_id_u", Integer, ForeignKey(User.user_id), nullable=False)
    user = relationship("User")


class LiniaLotnicza(db.Model):
    __tablename__ = 'linia_lotnicza'

    nazwa = Column('nazwa', String(25), primary_key=True, nullable=False)
    kraj = Column('kraj', String(25))
    data_zalozenia = Column('data_zalozenie', DateTime, nullable=False)

    samolot = relationship('Samolot', cascade="all")
    pilot = relationship('Pilot', cascade='all')
    harmonogram = relationship("Harmonogram", cascade='all')

    def liczba_samolotow(self):
        return pokaz_samoloty_linia(self.nazwa)

    def get_nazwa_safe(self):
        return urllib.parse.quote(self.nazwa.replace(" ", "_"))


class Samolot(db.Model):
    __tablename__ = 'samolot'

    nr_boczny = Column('nr_boczny', String(10), primary_key=True, nullable=False)
    max_zasieg = Column('max_zasieg', Integer, default=0)
    marka = Column('marka', String(15), nullable=False)
    model = Column('model', String(15), nullable=False)
    przebieg = Column('przebieg', Integer, default=0)
    pojemnosc = Column('pojemnosc', Integer, nullable=False)

    linia_lotnicza_nazwa = Column('linia_lotnicza_nazwa', String(25), ForeignKey(LiniaLotnicza.nazwa), nullable=False)
    linia_lotnicza = relationship('LiniaLotnicza')


class Pilot(db.Model):
    __tablename__ = 'pilot'

    id_pil = Column('id_pil', Integer, primary_key=True, autoincrement=True)
    imie = Column('imie', String(30), nullable=False)
    nazwisko = Column('nazwisko', String(30), nullable=False)
    data_dolaczenia = Column('data_dolaczenia', DateTime)

    linia_lotnicza_nazwa = Column('linia_lotnicza_nazwa', String(25), ForeignKey(LiniaLotnicza.nazwa), nullable=False)
    linia_lotnicza = relationship('LiniaLotnicza')


class Lotnisko(db.Model):
    __tablename__ = 'lotnisko'

    kod = Column('kod_miedzynarodowy', String(4), primary_key=True)
    m_na_mapie = Column('miejsce_na_mapie', String(100), nullable=False)
    kraj = Column('kraj', String(30), nullable=False)
    miasto = Column('miasto', String(20), nullable=False)
    strefa_czasowa = Column('strefa_czasowa', Integer, nullable=False)

    harmonogram_start = relationship("Harmonogram", foreign_keys="[Harmonogram.start_lotnisko_nazwa]", cascade="delete")
    harmonogram_finish = relationship("Harmonogram", foreign_keys="[Harmonogram.finish_lotnisko_nazwa]",
                                      cascade="delete")


class Harmonogram(db.Model):
    __tablename__ = 'harmonogram'

    nr_lotu = Column("nr_lotu", String(8), primary_key=True)
    dzien_tygodnia = Column("dzien_tygodnia", Integer, nullable=False)
    start_godzina = Column("start_godzina", Time, nullable=False)
    finish_godzina = Column("finish_godzina", Time, nullable=False)
    cena_podstawowa = Column("cena_podstawowa", Float(precision=2), nullable=False)

    start_lotnisko_nazwa = Column("start_lotnisko", ForeignKey(Lotnisko.kod), nullable=False)
    start_lotnisko = relationship("Lotnisko", foreign_keys=[start_lotnisko_nazwa])

    finish_lotnisko_nazwa = Column("finish_lotnisko", ForeignKey(Lotnisko.kod), nullable=False)
    finish_lotnisko = relationship("Lotnisko", foreign_keys=[finish_lotnisko_nazwa])

    linia_lotnicza_nazwa = Column("linia_lotnicza", ForeignKey(LiniaLotnicza.nazwa), nullable=False)
    linia_lotnicza = relationship("LiniaLotnicza", foreign_keys=[linia_lotnicza_nazwa])

    def get_dzien_tygodnia(self):
        return days_pl[self.dzien_tygodnia]

    def get_start_godzina(self):
        return datetime.time.strftime(self.start_godzina, "%H:%M")

    def get_finish_godzina(self):
        return datetime.time.strftime(self.finish_godzina, "%H:%M")


##############################################
#           FUNKCJE
##############################################

# ######### samoloty

def pokaz_samoloty_linia(nazwa):
    with session_handler() as db_session:
        liczba = len(db_session.query(Samolot).filter(Samolot.linia_lotnicza_nazwa == nazwa).all())
        return liczba


def check_data_samolot(nr_boczny, marka, model, linia_nazwa, pojemnosc):
    with session_handler() as db_session:
        samolot = db_session.query(Samolot).filter(Samolot.nr_boczny == nr_boczny).first()
        if samolot:
            return False, ['danger',
                           f"Samolot z numerem bocznym {nr_boczny} już istnieje ({samolot.linia_lotnicza_nazwa})"]
        if len(marka) > 15 or len(model) > 15:
            return False, ['danger', "Długość atrybutów marka i model powinna być nie większa niż 15"]
        if not pokaz_linie(linia_nazwa):
            return False, ['danger', f"Linia lotnicza {linia_nazwa} nie istnieje. Spróbuj jeszcze raz"]
        if not isinstance(pojemnosc, int):
            if isinstance(pojemnosc, str):
                if not pojemnosc.isnumeric():
                    return False, ['danger', "Pojemnośc powinna być liczbą"]
            else:
                return False, ['danger', "Pojemnośc powinna być liczbą"]
        return True, None


def dodaj_samolot(nr_boczny, marka, model, linia_nazwa, pojemnosc, zasieg=None):
    with session_handler() as db_session:
        good, message = check_data_samolot(nr_boczny, marka, model, linia_nazwa, pojemnosc)
        if not good:
            return message
        pojemnosc = int(pojemnosc)
        nowy_samolot = Samolot(nr_boczny=nr_boczny, marka=marka, model=model, pojemnosc=pojemnosc,
                               linia_lotnicza_nazwa=linia_nazwa, max_zasieg=zasieg)
        db_session.add(nowy_samolot)
        db_session.commit()
        return ['success', "Samolot został dodany"]


def usun_samolot(nr_boczny):
    with session_handler() as db_session:
        samolot = db_session.query(Samolot).filter(Samolot.nr_boczny == nr_boczny).first()
        if not samolot:
            return ['danger', f'Samolot o numerze bocnzym {nr_boczny} nie istnieje']
        db_session.delete(samolot)
        return ['success', f"Samolot o numerze bocznym {nr_boczny} został usunięty"]


def pokaz_samoloty(linia=None):
    with session_handler() as db_session:
        if linia:
            samoloty = db_session.query(Samolot).filter(Samolot.linia_lotnicza_nazwa == linia).all()
        else:
            samoloty = db_session.query(Samolot).all()
        return samoloty


# ######## linie


def dodaj_linie(nazwa, kraj=None, data_zalozenia=datetime.datetime.now()):
    with session_handler() as db_session:
        linia_nazwa = db_session.query(LiniaLotnicza).filter(LiniaLotnicza.nazwa == nazwa).first()
        if linia_nazwa:
            return ['danger', "Linia lotnicza z taką nazwą już istnieje"]
        nowa_linia = LiniaLotnicza(nazwa=nazwa, kraj=kraj, data_zalozenia=data_zalozenia)
        db_session.add(nowa_linia)
        return ['success', "Linia została dodana"]


def usun_linie(nazwa):
    with session_handler() as db_session:
        linia = db_session.query(LiniaLotnicza).filter(LiniaLotnicza.nazwa == nazwa).first()
        if not linia:
            return ['danger', "Nie istnieje linii lotniczej o podanej nazwie"]
        db_session.delete(linia)
        return ['success', "Linia została usunięta"]


def pokaz_linie(line=None):
    with session_handler() as db_session:
        if line:
            linie = db_session.query(LiniaLotnicza).filter(LiniaLotnicza.nazwa == line).first()
        else:
            linie = db_session.query(LiniaLotnicza).all()
        return linie


def zmodyfikuj_linie(nazwa, new_nazwa, kraj):
    # TODO
    pass


# ######## piloci


def pokaz_pilotow(linia=None):
    with session_handler() as db_session:
        if linia:
            piloci = db_session.query(Pilot).filter(Pilot.linia_lotnicza_nazwa == linia).all()
        else:
            piloci = db_session.query(Pilot).all()
        return piloci


def dodaj_pilota(imie, nazwisko, linia_nazwa):
    if isinstance(imie, str) and isinstance(nazwisko, str):
        if len(imie) < 30 and len(nazwisko) < 30:
            with session_handler() as db_session:
                nowy_pilot = Pilot(imie=imie, nazwisko=nazwisko, data_dolaczenia=datetime.datetime.now(),
                                   linia_lotnicza_nazwa=linia_nazwa)
                db_session.add(nowy_pilot)
                return ['success', 'Nowy pilot został dodany']
        return ['danger', "Długośc imienia i nazwiska powinna zawierać maksymalnie 30 znakóœ"]
    return ['danger', "Dane nie są typu string. Sprawdż działanie programu"]


def usun_pilota(id_pil):
    with session_handler() as db_session:
        pilot = db_session.query(Pilot).filter(Pilot.id_pil == id_pil).first()
        if not pilot:
            return ['danger', "Pilot o danym identyfikatorze nie istnieje"]
        else:
            name = pilot.imie
            surname = pilot.nazwisko
            db_session.delete(pilot)
            return ["success", f"Pilot {name} {surname} został usunięty"]


def zmodyfikuj_pilota(id_pil, imie, nazwisko):
    with session_handler() as db_session:
        # TODO
        pass


# ############### lotniska


def pokaz_lotniska():
    with session_handler() as db_session:
        result = db_session.query(Lotnisko).order_by(Lotnisko.kod).all()
        return result


def dodaj_lotnisko(kod, m_na_mapie, kraj, miasto, strefa_czasowa):
    if any([x == "" for x in [kod, m_na_mapie, kraj, miasto, strefa_czasowa]]):
        return ['danger', "Żadne pole nie może być puste"]
    if len(kod) > 4:
        return ["danger", "Długość kodu międzynarodowego jest większa od dozwolonej (4)"]
    if len(m_na_mapie) > 100:
        return ["danger", "Długość miejsca na mapie jest większa od dozwolonej (100)"]
    if len(kraj) > 30:
        return ["danger", "Długość nazwy kraju jest większa od dozwolonej (30)"]
    if len(miasto) > 20:
        return ["danger", "Długość nazwy miasta jest większa od dozwolonej (20)"]
    if not isinstance(strefa_czasowa, str):
        return ["danger", "Strefa czasowa jest pusta"]
    if not strefa_czasowa.isnumeric():
        return ['danger', "Strefa czasowa musi być liczbą"]
    with session_handler() as db_session:
        ex_lotnisko = db_session.query(Lotnisko).filter(Lotnisko.kod == kod).first()
        if ex_lotnisko:
            return ['danger', "Lotnisko z podanym kodem międzynarodowym już zostało dodane"]
        new_lotnisko = Lotnisko(kod=kod, m_na_mapie=m_na_mapie, kraj=kraj, miasto=miasto, strefa_czasowa=strefa_czasowa)
        db_session.add(new_lotnisko)
        return ['success', f"Lotnisko {kod} zostało dodane"]


def zmodyfikuj_lotnisko(kod, nowy_kod, m_na_mapie, kraj, miasto, strefa_czasowa):
    # TODO
    pass


def usun_lotnisko(kod):
    with session_handler() as db_session:
        lotnisko = db_session.query(Lotnisko).filter(Lotnisko.kod == kod).first()
        if lotnisko:
            db_session.delete(lotnisko)
            return ['success', f"Lotnisko {kod} zostało usunięte"]
        else:
            return ['danger', f"Lotnisko o kodzie {kod} nie istnieje"]


# ############# harmonogram

def pokaz_harmonogram(linia_lotnicza=None):
    with session_handler() as db_session:
        if linia_lotnicza:
            result = db_session.query(Harmonogram).filter(Harmonogram.linia_lotnicza_nazwa == linia_lotnicza).order_by(
                Harmonogram.nr_lotu).all()
        else:
            # if it doesn't work - log into your root account on mysql and enter:
            #           SET GLOBAL sql_mode=(SELECT REPLACE(@@sql_mode,'ONLY_FULL_GROUP_BY',''));
            result = db_session.query(Harmonogram).group_by(Harmonogram.linia_lotnicza_nazwa).order_by(
                Harmonogram.nr_lotu).all()
        return result


def dodaj_harmonogram(nr_lotu, linia_lotnicza, start_lotnisko, finish_lotnisko, dzien_tygodnia, start_godzina,
                      finish_godzina, cena_podstawowa):
    if any(x == "" for x in
           [linia_lotnicza, start_lotnisko, finish_lotnisko, dzien_tygodnia, start_godzina, finish_godzina,
            cena_podstawowa]):
        return ['danger', "Wszystkie pola są obowiązkowe"]
    if len(nr_lotu) != 8:
        return ["danger", "Długośc numeru lotu musi być równa 8"]
    with session_handler() as db_session:
        if db_session.query(Harmonogram).filter(Harmonogram.nr_lotu).first():
            return ['danger', "Lot o danym numerze już istnieje"]
        for lotnisko in [start_lotnisko, finish_lotnisko]:
            if not db_session.query(Lotnisko).filter(Lotnisko.kod == lotnisko).first():
                return ["danger", "Lotnisko o danym kodzie międzynarodowym nie istnieje"]
        if not db_session.query(LiniaLotnicza).filter(LiniaLotnicza.nazwa == linia_lotnicza).first():
            return ["danger", "Taka linia lotnicza nie istnieje"]
        if not isinstance(dzien_tygodnia, str) or not dzien_tygodnia.isnumeric() or int(dzien_tygodnia) not in range(7):
            return ['danger', "Niepoprawny dzień tygodnia"]
        try:
            time_start = datetime.datetime.strptime(start_godzina, "%H:%M")
            time_finish = datetime.datetime.strptime(finish_godzina, "%H:%M")
        except:
            return ['danger', "Niepoprawny format godziny startu bądż lądowania"]
        if not isinstance(cena_podstawowa, str) or not cena_podstawowa.isnumeric():
            return ["danger", "Niepoprawny format ceny"]
        new_harmonogram = Harmonogram(nr_lotu=nr_lotu, linia_lotnicza_nazwa=linia_lotnicza, start_godzina=time_start,
                                      finish_godzina=time_finish, start_lotnisko_nazwa=start_lotnisko, dzien_tygodnia=int(dzien_tygodnia),
                                      finish_lotnisko_nazwa=finish_lotnisko, cena_podstawowa=float(cena_podstawowa))
        db_session.add(new_harmonogram)
        return ["success", f"Nowy wpis o numerze lotu {nr_lotu} został dodany"]


def usun_harmonogram(nr_lotu):
    with session_handler() as db_session:
        harmonogram = db_session.query(Harmonogram).filter(Harmonogram.nr_lotu == nr_lotu).first()
        if not harmonogram:
            return ["danger", f"Lot o numerze {nr_lotu} nie istnieje"]
        else:
            db_session.delete(harmonogram)
            return ["success", f"Lot o numerze {nr_lotu} został usunięty"]


def zmodyfikuj_harmonogram(nr_lotu, nowy_nr_lotu, linia_lotnicza, start_lotnisko, finish_lotnisko, dzien_tygodnia, start_godzina,
                      finish_godzina, cena_podstawowa):
    # TODO
    pass

# ############ user


def pokaz_user(user_id=None, email=None):
    with session_handler() as db_session:
        if user_id:
            result = db_session.query(User).filter(User.user_id == user_id).first()
        elif email:
            result = db_session.query(User).filter(User.email == email).first()
        else:
            result = db_session.query(User).all()
        return result


def dodaj_user(imie, nazwisko, email, password, password_repeat, u_type):
    if check_empty([imie, nazwisko, email, password, password_repeat, type]):
        return ["danger", "Wszystkie atrybuty są obowiązkowe"]
    if not isinstance(email, str) or email.index("@") == -1:
        return ['danger', "Niepoprawny format email"]
    if not re.search(r'\d', password) or not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password):
        return ["danger", "Hasło jest bardzo słabe. Musi zawierać conajmniej 1 liczbę, co najmniej 1 dużą literę i co najmniej jedbą małą"]
    if password != password_repeat:
        return ["danger", "Hasła wprowadzone w dwóch polach nie są równe"]
    if u_type not in ["user", "admin"]:
        return ["danger", "Niepoprawny typ hasła"]
    with session_handler() as db_session:
        ex_user = db_session.query(User).filter(User.email == email).first()
        if ex_user:
            return ['danger', "Użytkownik o podanym email już istnieje"]
        new_user = User(name=imie, surname=nazwisko, email=email, password=password, type=u_type)
        db_session.add(new_user)
        return ["success", "Użytkownik został dodany"]
    pass


def usun_user(user_id):
    with session_handler() as db_session:
        user = db_session.query(User).filter(User.user_id == user_id).first()
        if not user:
            return ["danger", "Użytkownik o danym identyfikatorze nie istnieje"]
        else:
            name = user.imie
            surname = user.nazwisko
            db_session.delete(user)
            return ["success", f"Użytkownik {name} {surname} został usunięty"]


def check_user_credentials(email, password):
    with session_handler() as db_session:
        user = db_session.query(User).filter(User.email == email).first()
        if not user:
            return None, ["danger", "Użytkownik z takim email nie istnieje"]
        if not user.validate_password(password):
            return None, ["danger", "Niepoprawne hasło"]
        return user, None


db.create_all()

if __name__ == '__main__':
    # db.drop_all()
    pass
