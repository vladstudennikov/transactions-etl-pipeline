import os
from decimal import Decimal
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy.exc import IntegrityError

from app.db import SessionLocal, engine
from app.models import Base, Party

fake = Faker()
Faker.seed(12345)

PARTIES_RAW = [
("ACME Corp","DE89370400440532013000"),
("John Doe","GB29NWBK60161331926819"),
("Alpha Ltd","FR1420041010050500013M02606"),
("Beta LLC","ES9121000418450200051332"),
("Gamma GmbH","AT611904300234573201"),
("Delta SA","BE68539007547034"),
("Epsilon BV","NL91ABNA0417164300"),
("Zeta Oy","FI2112345600000785"),
("Eta SRL","IT60X0542811101000000123456"),
("Theta Inc","CH9300762011623852957"),
("Iota Co","SE4550000000058398257466"),
("Kappa KG","DK5000400440116243"),
("Lambda AB","NO9386011117947"),
("Mu SpA","PL61109010140000071219812874"),
("Nu Ltd","CZ6508000000192000145399"),
("Xi Corp","HU42117730161111101800000000"),
("Omicron LLC","GR1601101250000000012300695"),
("Pi Enterprises","PT50000201231234567890154"),
("Rho Group","IE29AIBK93115212345678"),
("Sigma Partners","LU280019400644750000"),
]

def iso_country_from_iban(iban):
    if not iban or len(iban) < 2:
        return None
    return iban[:2]

def currency_from_country(country_iso):
    mapping = {
        "DE":"EUR","GB":"GBP","FR":"EUR","ES":"EUR","AT":"EUR","BE":"EUR","NL":"EUR","FI":"EUR",
        "IT":"EUR","CH":"CHF","SE":"SEK","DK":"DKK","NO":"NOK","PL":"PLN","CZ":"CZK","HU":"HUF",
        "GR":"EUR","PT":"EUR","IE":"EUR","LU":"EUR"
    }
    return mapping.get(country_iso, "EUR")

def create_parties():
    session = SessionLocal()
    created = 0
    for idx, (name, iban) in enumerate(PARTIES_RAW, start=1):
        country = iso_country_from_iban(iban)
        currency = currency_from_country(country)
        p = Party(
            name=name,
            iban=iban,
            mean_sum=Decimal("1000.00"),
            country=country,
            currency=currency,
            account_status = fake.random_element(elements=("active","suspended","closed")),
            risk_score = round(fake.random.uniform(0, 100), 2),
            annual_turnover = Decimal(str(round(fake.random.uniform(1e4, 5e7), 2))),
            num_transactions = fake.random_int(min=1, max=20000),
            last_tx_date = datetime.utcnow() - timedelta(days=fake.random_int(min=0, max=365)),
            contact_email = fake.company_email() if " " not in name else fake.email(),
            contact_phone = fake.phone_number(),
            address = fake.address().replace("\n", ", "),
            notes = fake.sentence(nb_words=12),
            is_corporate = (not name.lower().strip().endswith("doe") and "john" not in name.lower()),
        )
        try:
            session.add(p)
            session.commit()
            created += 1
        except IntegrityError:
            session.rollback()
            print(f"Skipping duplicate IBAN: {iban}")
    session.close()
    print(f"Created {created} parties.")


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    create_parties()