from sqlalchemy import create_engine, String, Integer, Column, DateTime, Boolean, Text, desc, func, ForeignKey, \
    ForeignKeyConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError, DisconnectionError, ProgrammingError, OperationalError
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.sql.expression import false, true, case, not_, and_
import os, numpy, datetime, warnings, time, random
from multiprocessing import Process, Manager, Semaphore
from multiprocessing.managers import BaseManager
from contextlib import contextmanager

from flask import Flask, url_for, render_template, abort, request
from flask_sqlalchemy import SQLAlchemy
import urllib

app = Flask(__name__)

# create database on your local machine and fill this line with your credentials (replace uppercase words):
#                                               mysql://USERNAME:PASSWORD@localhost/DATABASE?charset=utf8
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://admin_flies:FA$#$3awfa3afsd@localhost/flies?charset=utf8'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

dir_path = os.path.dirname(os.path.realpath(__file__))

@contextmanager
def session_handler():
    session = db.session
    try:
        session.flush()
        yield session
        session.commit()
    except Exception as exp:
        print(exp)
        session.rollback()
    except IntegrityError:
        print("Already exists")
        session.rollback()


def get_countries_list():
    with open(os.path.join(dir_path, "data", "countries")) as file:
        ls = file.read().splitlines()
        return ls


class User(db.Model):
    __tablename__ = 'user'

    user_id = Column('id_u', Integer, primary_key=True, autoincrement=True)
    haslo = Column('haslo', String(32), nullable=False)
    typ = Column('typ', String(32), default='user')
    email = Column('email', String(32), nullable=False)
    imie = Column('imie', String(32), nullable=False)
    nazwisko = Column('nazwisko', String(32), nullable=False)

    rabat = relationship("Rabat", cascade="all")

    def is_admin(self):
        return self.typ == 'admin'


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
            return False, ['danger', f"Samolot z numerem bocznym {nr_boczny} już istnieje ({samolot.linia_lotnicza_nazwa})"]
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
    with session_handler() as db_session:
        if isinstance(imie, str) and isinstance(nazwisko, str):
            if len(imie) < 30 and len(nazwisko) < 30:
                nowy_pilot = Pilot(imie=imie, nazwisko=nazwisko, data_dolaczenia=datetime.datetime.now(), linia_lotnicza_nazwa=linia_nazwa)
                db_session.add(nowy_pilot)
                return ['success', 'Nowy pilot został dodany']
            return ['danger', "Długośc imienia i nazwiska powinna zawierać maksymalnie 30 znakóœ"]
        return ['danger', "Dane nie są typu string. Sprawdż działanie programu"]


def usun_pilota(id_pil):
    # TODO
    pass


def zmodyfikuj_pilota(id_pil, imie, nazwisko):
    # TODO
    pass


db.create_all()


if __name__ == '__main__':
    # db.drop_all()
    pass

