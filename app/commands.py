import stripe
import click
from flask.cli import with_appcontext
from app.models import Plan
from app import db

LIMITS = {
    "free": {
        "box_count": 1,
        "duration": 1800,
        "memory": 256,
        "cpu": 512,
        "bandwidth": 1000,
        "forwards": 2,
        "reserved_config": 1,
        "cost": 0,
    },
    "waiting": {
        "box_count": 0,
        "duration": 0,
        "memory": 0,
        "cpu": 0,
        "bandwidth": 0,
        "forwards": 0,
        "reserved_config": 0,
        "cost": 0,
    },
    "beta": {
        "box_count": 1,
        "duration": 1800,
        "memory": 256,
        "cpu": 512,
        "bandwidth": 1000,
        "forwards": 2,
        "reserved_config": 1,
        "cost": 0,
    },
    "paid": {
        "box_count": 2,
        "duration": 28800,
        "memory": 512,
        "cpu": 1024,
        "bandwidth": 10000,
        "forwards": 10,
        "reserved_config": 2,
        "cost": 999,
    },
}


@click.group()
def plan():
    """ Manage Plan Tables """
    pass


@plan.command("stripe_product")
@with_appcontext
def create_product_command():
    create_product()


def create_product():
    """ Create Stripe Products for Userland """
    for plan in Plan.query.all():
        if plan.cost == 0:
            continue

        stripe.Product.create(name="Userland.io", type="service", id=plan.name)
        stripe_plan = stripe.Plan.create(
            product=plan.name,
            nickname=f"Userland Service: {plan.name}",
            interval="month",
            currency="usd",
            amount=plan.cost,
        )

        plan.stripe_id = stripe_plan["product"]
        db.session.add(plan)

    db.session.commit()


@plan.command("populate")
@with_appcontext
def populate_command():
    populate()


def populate():
    """ Create DB Entries for Userland Cloud Plans"""

    for plan_name, plan in LIMITS.items():
        p = Plan(**{"name": plan_name}, **plan)
        db.session.add(p)

    db.session.commit()
