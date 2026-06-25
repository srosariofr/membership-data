from faker import Faker
import random
import pandas as pd
from pathlib import Path
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta

fake = Faker("es_ES")
fake.seed_instance(42)

OUTPUT_DIR = Path("data")

NUM_COMPANIES = 300
NUM_APPLICANTS = 5000
NUM_EVENTS = 100

DATA_END_DATE = datetime(2026, 6, 1)

MEMBERSHIP_TYPES = ["Individual", "Corporate", "Student", "Honorary"]
MEMBER_STATUSES = ["Active", "Inactive", "Cancelled", "Pending Renewal"]

APPLICATION_STATUSES_FLOW = [
    "Submitted",
    "Under Review",
    "Pending Payment",
    "Approved",
]

REJECTED_FLOW = [
    "Submitted",
    "Under Review",
    "Rejected",
]

WITHDRAWN_FLOW = [
    "Submitted",
    "Withdrawn",
]

PAYMENT_STATUSES = ["Pending", "Paid", "Failed", "Overdue", "Refunded"]
PAYMENT_METHODS = ["Credit Card", "Bank Transfer", "Cash", "Check", "Online Payment"]
EVENT_TYPES = ["Conference", "Workshop", "Networking", "Webinar", "Training", "Assembly"]
CITIES = [
    "Santo Domingo",
    "Santiago",
    "La Romana",
    "San Pedro de Macorís",
    "Punta Cana",
    "Puerto Plata",
    "San Francisco de Macorís",
]

PROFESSIONS = [
    "Software Engineer",
    "Data Analyst",
    "Accountant",
    "Lawyer",
    "Architect",
    "Project Manager",
    "Business Consultant",
    "Marketing Specialist",
    "Civil Engineer",
    "Financial Analyst",
]

def generate_companies():
    companies = []
    for i in range(NUM_COMPANIES):
        companies.append({
            "company_id": i,
            "company_name": fake.company(),
            "industry": random.choice(["Technology", "Finance", "Legal Services", "Construction", "Consulting",
                                        "Healthcare", "Education", "Retail", "Manufacturing"]),
            "city": random.choice(CITIES),
            "country": "Dominican Republic",
            "phone_number": fake.phone_number(),
            "email": fake.company_email(),
            "created_at": fake.date_time_between(start_date="-5y", end_date=DATA_END_DATE),
        })
    
    return pd.DataFrame(companies)

def generate_membership_applications(companies_df):
    applications = []
    for i in range(NUM_APPLICANTS):
        company_id = random.choice(companies_df["company_id"].tolist())
        final_status = random.choices(
            ["Approved", "Rejected", "Withdrawn", "Pending"],
            weights=[65, 15, 5, 15],
            k=1
        )[0]

        if final_status == "Approved":
            current_status = "Approved"
        elif final_status == "Rejected":
            current_status = "Rejected"
        elif final_status == "Withdrawn":
            current_status = "Withdrawn"
        else:
            current_status = random.choice([
                "Submitted",
                "Under Review",
                "Pending Payment",
            ])
        
        applications.append({
            "application_id": i,
            "applicant_name": f"{fake.first_name()} {fake.last_name()}",
            "email": fake.email(),
            "birthdate": fake.date_of_birth(minimum_age=18, maximum_age=50),
            "profession": random.choice(PROFESSIONS),
            "company_id": company_id,
            "country": "Dominican Republic",
            "city": random.choice(CITIES),
            "application_type": random.choice(MEMBERSHIP_TYPES),
            "status": current_status,
            "submitted_at": fake.date_time_between(start_date="-5y", end_date=DATA_END_DATE),
            "source_channel": random.choice([
                "Website",
                "Referral",
                "Event",
                "Email Campaign",
                "Walk-in",
            ]),
        })
    
    return pd.DataFrame(applications)

def generate_application_status_history(applications_df):
    application_status_history = []
    history_id = 1

    for _, app in applications_df.iterrows():
        submitted_at = app["submitted_at"]
        current_status = app["status"]

        if current_status == "Approved":
            flow = APPLICATION_STATUSES_FLOW
        elif current_status == "Rejected":
            flow = REJECTED_FLOW
        elif current_status == "Withdrawn":
            flow = WITHDRAWN_FLOW
        else:
            possible_flow = [
                "Submitted",
                "Under Review",
                "Pending Payment",
            ]
            current_index = possible_flow.index(current_status)
            flow = possible_flow[:current_index + 1]

        status_start = submitted_at

        for index, status in enumerate(flow):
            if index == len(flow) - 1:
                status_end = None
            else:
                status_end = status_start + pd.Timedelta(days=random.randint(1, 30))

            application_status_history.append({
                "application_status_history_id": history_id,
                "application_id": app["application_id"],
                "status": status,
                "status_start_at": status_start,
                "status_end_at": status_end,
                "changed_by": random.choice([
                    "system",
                    "membership_officer",
                    "review_committee",
                ]),
                # "change_reason": random.choice([
                #     "Initial submission",
                #     "Documents received",
                #     "Manual review",
                #     "Payment validation",
                #     "Applicant response",
                #     "Committee decision",
                #     "Incomplete information",
                # ]),
            })

            history_id += 1

            if status_end is not None:
                status_start = status_end

    return pd.DataFrame(application_status_history)

def generate_members(applications_df, application_status_history_df):
    members = []

    approved_applications = applications_df[
        applications_df["status"] == "Approved"
    ].copy()

    approved_dates = (
        application_status_history_df[
            application_status_history_df["status"] == "Approved"
        ][["application_id", "status_start_at"]]
        .rename(columns={"status_start_at": "approved_at"})
    )

    approved_applications = approved_applications.merge(
        approved_dates,
        on="application_id",
        how="inner"
    )

    for member_id, (_, app) in enumerate(approved_applications.iterrows(), start=1):
        approved_at = app["approved_at"]

        status = "Active"

        members.append({
            "member_id": member_id,
            "application_id": app["application_id"],
            "name": app["applicant_name"],
            "email": app["email"],
            "gender": random.choice(["M", "F"]),
            "birth_date": app["birthdate"],
            "country": app["country"] if "country" in app else "Dominican Republic",
            "city": app["city"] if "city" in app else random.choice(CITIES),
            "profession": app["profession"],
            "company_id": app["company_id"],
            "membership_type": app["application_type"],
            "current_status": status,
            "registered_at": app["submitted_at"],
            "approved_at": approved_at, 
        })

    return pd.DataFrame(members)

def generate_member_status_history(members_df):
    member_status_history = []
    history_id = 1

    for _, member in members_df.iterrows():
        member_id = member["member_id"]
        approved_at = pd.to_datetime(member["approved_at"]).to_pydatetime()

        current_status = "Active"
        status_start = approved_at

        for year in range(approved_at.year + 1, DATA_END_DATE.year + 1):
            renewal_date = datetime(year, 2, 1, 0, 0, 0)  # Renovación anual el 1 de febrero

            # Si la fecha de renovación cae fuera del rango del dataset, no aplica.
            if renewal_date > DATA_END_DATE:
                continue

            # Si ya está cancelado, dejamos de generar historia.
            if current_status == "Cancelled":
                break

            # Si no está activo, no debe entrar a una nueva renovación anual.
            if current_status != "Active":
                continue

            # Cerramos el período Active anterior.
            member_status_history.append({
                "member_status_history_id": history_id,
                "member_id": member_id,
                "status": current_status,
                "status_start_at": status_start,
                "status_end_at": renewal_date,
                "changed_by": "system",
                "change_reason": "Membership active before annual renewal",
            })
            history_id += 1

            # Ahora inicia Pending Renewal.
            pending_start = renewal_date

            pays_renewal = random.choices(
                [True, False],
                weights=[85, 15],
                k=1
            )[0]

            if pays_renewal:
                reactivation_date = renewal_date + timedelta(
                    days=random.randint(1, 180)
                )

                if reactivation_date <= DATA_END_DATE:
                    # Cerramos Pending Renewal cuando paga.
                    member_status_history.append({
                        "member_status_history_id": history_id,
                        "member_id": member_id,
                        "status": "Pending Renewal",
                        "status_start_at": pending_start,
                        "status_end_at": reactivation_date,
                        "changed_by": random.choice([
                            "system",
                            "finance_officer",
                            "membership_officer",
                        ]),
                        "change_reason": "Renewal payment received",
                    })
                    history_id += 1

                    # Vuelve a estar activo.
                    current_status = "Active"
                    status_start = reactivation_date

                else:
                    # Si la fecha simulada de pago cae después del final del dataset,
                    # queda pendiente hasta el final abierto.
                    current_status = "Pending Renewal"
                    status_start = pending_start
                    break

            else:
                inactive_date = renewal_date + relativedelta(months=6)

                if inactive_date <= DATA_END_DATE:
                    # Cerramos Pending Renewal a los 6 meses.
                    member_status_history.append({
                        "member_status_history_id": history_id,
                        "member_id": member_id,
                        "status": "Pending Renewal",
                        "status_start_at": pending_start,
                        "status_end_at": inactive_date,
                        "changed_by": "system",
                        "change_reason": "Renewal overdue for more than 6 months",
                    })
                    history_id += 1

                    # Ahora inicia Inactive.
                    inactive_start = inactive_date
                    cancelled_date = inactive_date + relativedelta(years=1)

                    if cancelled_date <= DATA_END_DATE:
                        # Cerramos Inactive después de un año.
                        member_status_history.append({
                            "member_status_history_id": history_id,
                            "member_id": member_id,
                            "status": "Inactive",
                            "status_start_at": inactive_start,
                            "status_end_at": cancelled_date,
                            "changed_by": "system",
                            "change_reason": "Inactive for more than 1 year",
                        })
                        history_id += 1

                        # Ahora inicia Cancelled.
                        current_status = "Cancelled"
                        status_start = cancelled_date
                        break

                    else:
                        # Queda inactivo como estado actual.
                        current_status = "Inactive"
                        status_start = inactive_start
                        break

                else:
                    # Si todavía no han pasado 6 meses dentro del dataset,
                    # queda en Pending Renewal.
                    current_status = "Pending Renewal"
                    status_start = pending_start
                    break

        # Agregamos el último estado abierto.
        member_status_history.append({
            "member_status_history_id": history_id,
            "member_id": member_id,
            "status": current_status,
            "status_start_at": status_start,
            "status_end_at": None,
            "changed_by": "system",
            "change_reason": "Current member status",
        })
        history_id += 1

    return pd.DataFrame(member_status_history)

def update_member_current_status(members_df, member_status_history_df):
    latest_status = (
        member_status_history_df.sort_values(by=["member_id", "status_start_at"])
        .groupby("member_id")
        .last()
        .rename(columns={
            "status": "current_status",
            "status_start_at": "current_status_start_at",
            })
    )

    members_df = members_df.drop(columns=["current_status"], errors="ignore")

    members_df = members_df.merge(
        latest_status[["current_status", "current_status_start_at"]],
        on="member_id",
        how="left"
    )

    # print(latest_status.head())

    return members_df

def generate_events():
    rows = []

    for i in range(1, NUM_EVENTS + 1):
        event_date = fake.date_time_between(start_date="-5y", end_date=DATA_END_DATE)

        rows.append({
            "event_id": i,
            "event_name": f"{random.choice(EVENT_TYPES)} {event_date.year} #{i}",
            "event_type": random.choice(EVENT_TYPES),
            "event_date": event_date,
            "city": random.choice(CITIES),
            "capacity": random.choice([50, 100, 150, 200, 300, 500]),
        })

    return pd.DataFrame(rows)

def generate_event_attendance(events_df, members_df):
    rows = []
    attendance_id = 1
    member_ids = members_df["member_id"].tolist()

    for _, event in events_df.iterrows():
        capacity = event["capacity"]
        number_registered = random.randint(int(capacity * 0.4), int(capacity * 1.2))
        selected_members = random.sample(member_ids, min(number_registered, len(member_ids)))

        for member_id in selected_members:
            registered_at = event["event_date"] - timedelta(days=random.randint(1, 45))

            attendance_status = random.choices(
                ["Registered", "Attended", "No Show", "Cancelled"],
                weights=[15, 65, 12, 8],
                k=1
            )[0]

            attended_at = None
            if attendance_status == "Attended":
                attended_at = event["event_date"]

            rows.append({
                "event_attendance_id": attendance_id,
                "event_id": event["event_id"],
                "member_id": member_id,
                "attendance_status": attendance_status,
                "registered_at": registered_at,
                "attended_at": attended_at,
            })

            attendance_id += 1

    return pd.DataFrame(rows)

def generate_payments(
    members_df,
    application_status_history_df,
    member_status_history_df,
    events_df,
    event_attendance_df
):
    rows = []
    payment_id = 1

    initial_subscription_amounts = [10000]
    renewal_amounts = [5000]
    event_amounts = [500, 750, 1000, 1500, 2000]

    # ------------------------------------------------------------
    # Asegurar tipos datetime
    # ------------------------------------------------------------

    application_status_history_df = application_status_history_df.copy()
    member_status_history_df = member_status_history_df.copy()
    events_df = events_df.copy()
    event_attendance_df = event_attendance_df.copy()

    application_status_history_df["status_start_at"] = pd.to_datetime(
        application_status_history_df["status_start_at"],
        errors="coerce"
    )
    application_status_history_df["status_end_at"] = pd.to_datetime(
        application_status_history_df["status_end_at"],
        errors="coerce"
    )

    member_status_history_df["status_start_at"] = pd.to_datetime(
        member_status_history_df["status_start_at"],
        errors="coerce"
    )
    member_status_history_df["status_end_at"] = pd.to_datetime(
        member_status_history_df["status_end_at"],
        errors="coerce"
    )

    events_df["event_date"] = pd.to_datetime(
        events_df["event_date"],
        errors="coerce"
    )

    event_attendance_df["registered_at"] = pd.to_datetime(
        event_attendance_df["registered_at"],
        errors="coerce"
    )

    # ------------------------------------------------------------
    # 1. Pagos iniciales: Pending Payment → Approved
    # ------------------------------------------------------------

    approved_applications = application_status_history_df[
        application_status_history_df["status"] == "Approved"
    ][["application_id", "status_start_at"]].rename(
        columns={"status_start_at": "approved_at"}
    )

    pending_payment_applications = application_status_history_df[
        application_status_history_df["status"] == "Pending Payment"
    ][["application_id", "status_start_at"]].rename(
        columns={"status_start_at": "payment_due_at"}
    )

    initial_payments_base = (
        members_df[["member_id", "application_id", "membership_type"]]
        .merge(
            approved_applications,
            on="application_id",
            how="inner"
        )
        .merge(
            pending_payment_applications,
            on="application_id",
            how="left"
        )
    )

    for _, row in initial_payments_base.iterrows():
        due_date = row["payment_due_at"]

        if pd.isna(due_date):
            due_date = row["approved_at"] - timedelta(days=random.randint(1, 15))

        paid_at = row["approved_at"]

        rows.append({
            "payment_id": payment_id,
            "member_id": row["member_id"],
            "application_id": row["application_id"],
            "event_id": None,
            "event_attendance_id": None,
            "invoice_id": fake.uuid4(),
            "payment_type": "Initial Subscription",
            "amount": random.choice(initial_subscription_amounts),
            "currency": "DOP",
            "payment_status": "Paid",
            "payment_method": random.choice(PAYMENT_METHODS),
            "billing_period": str(pd.to_datetime(paid_at).year),
            "due_date": due_date,
            "paid_at": paid_at,
        })

        payment_id += 1

    # ------------------------------------------------------------
    # 2. Pagos de renovación: Pending Renewal → Active
    # ------------------------------------------------------------

    member_history_sorted = member_status_history_df.sort_values(
        ["member_id", "status_start_at"]
    ).copy()

    member_history_sorted["next_status"] = (
        member_history_sorted
        .groupby("member_id")["status"]
        .shift(-1)
    )

    renewal_payments_base = member_history_sorted[
        (member_history_sorted["status"] == "Pending Renewal") &
        (member_history_sorted["next_status"] == "Active") &
        (member_history_sorted["status_end_at"].notna())
    ].copy()

    for _, row in renewal_payments_base.iterrows():
        due_date = row["status_start_at"]
        paid_at = row["status_end_at"]

        rows.append({
            "payment_id": payment_id,
            "member_id": row["member_id"],
            "application_id": None,
            "event_id": None,
            "event_attendance_id": None,
            "invoice_id": fake.uuid4(),
            "payment_type": "Annual Renewal",
            "amount": random.choice(renewal_amounts),
            "currency": "DOP",
            "payment_status": "Paid",
            "payment_method": random.choice(PAYMENT_METHODS),
            "billing_period": str(pd.to_datetime(due_date).year),
            "due_date": due_date,
            "paid_at": paid_at,
        })

        payment_id += 1

    # ------------------------------------------------------------
    # 3. Pagos de eventos: solo miembros activos en la fecha del evento
    # ------------------------------------------------------------

    event_registrations = (
        event_attendance_df
        .merge(
            events_df[["event_id", "event_date", "event_type"]],
            on="event_id",
            how="left"
        )
    )

    event_registrations = event_registrations[
        event_registrations["attendance_status"] != "Cancelled"
    ].copy()

    active_periods = member_status_history_df[
        member_status_history_df["status"] == "Active"
    ][[
        "member_id",
        "status_start_at",
        "status_end_at"
    ]].copy()

    event_registrations = event_registrations.merge(
        active_periods,
        on="member_id",
        how="inner"
    )

    event_registrations = event_registrations[
        (
            event_registrations["event_date"] >= event_registrations["status_start_at"]
        )
        &
        (
            event_registrations["status_end_at"].isna()
            |
            (event_registrations["event_date"] < event_registrations["status_end_at"])
        )
    ].copy()

    # Por seguridad, evitar duplicados si un registro matchea más de una ventana activa.
    event_registrations = event_registrations.drop_duplicates(
        subset=["event_attendance_id"]
    )

    for _, row in event_registrations.iterrows():
        due_date = row["registered_at"]

        if pd.isna(due_date):
            due_date = row["event_date"] - timedelta(days=random.randint(1, 30))

        # Simulamos que algunos pagan antes del evento y otros el mismo día.
        paid_at = due_date + timedelta(
            days=random.randint(0, max(0, (row["event_date"] - due_date).days)),
            hours=random.randint(8, 18),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59),
        )

        # Si por alguna razón paid_at queda después del evento, lo ajustamos.
        if paid_at > row["event_date"]:
            paid_at = row["event_date"]

        rows.append({
            "payment_id": payment_id,
            "member_id": row["member_id"],
            "application_id": None,
            "event_id": row["event_id"],
            "event_attendance_id": row["event_attendance_id"],
            "invoice_id": fake.uuid4(),
            "payment_type": "Event Registration",
            "amount": random.choice(event_amounts),
            "currency": "DOP",
            "payment_status": "Paid",
            "payment_method": random.choice(PAYMENT_METHODS),
            "billing_period": str(pd.to_datetime(row["event_date"]).year),
            "due_date": due_date,
            "paid_at": paid_at,
        })

        payment_id += 1

    payments_df = pd.DataFrame(rows)

    payments_df["due_date"] = pd.to_datetime(
        payments_df["due_date"],
        errors="coerce"
    )

    payments_df["paid_at"] = pd.to_datetime(
        payments_df["paid_at"],
        errors="coerce"
    )

    return payments_df

companies_df = generate_companies()
companies_df.to_csv(OUTPUT_DIR / "companies.csv", index=False)

applications_df = generate_membership_applications(companies_df)
applications_df.to_csv(OUTPUT_DIR / "membership_applications.csv", index=False)

application_status_history_df = generate_application_status_history(applications_df)
application_status_history_df.to_csv(OUTPUT_DIR / "application_status_history.csv", index=False)

members_df = generate_members(applications_df, application_status_history_df)

member_status_history_df = generate_member_status_history(members_df)
member_status_history_df.to_csv(OUTPUT_DIR / "member_status_history.csv", index=False)

members_df = update_member_current_status(members_df, member_status_history_df)
members_df.to_csv(OUTPUT_DIR / "members.csv", index=False)

events_df = generate_events()
events_df.to_csv(OUTPUT_DIR / "events.csv", index=False)

event_attendance_df = generate_event_attendance(events_df, members_df)
event_attendance_df.to_csv(OUTPUT_DIR / "event_attendance.csv", index=False)

payments_df = generate_payments(members_df,
    application_status_history_df,
    member_status_history_df,
    events_df,
    event_attendance_df)
payments_df.to_csv(OUTPUT_DIR / "payments.csv", index=False)