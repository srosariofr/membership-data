from faker import Faker
import random
import pandas as pd
from pathlib import Path

fake = Faker("es_ES")
fake.seed_instance(42)

OUTPUT_DIR = Path("data")

NUM_COMPANIES = 300
NUM_APPLICANTS = 5000
NUM_EVENTS = 300

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
            "created_at": fake.date_time_between(start_date="-5y", end_date="now"),
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
            "submited_at": fake.date_time_between(start_date="-5y", end_date="now"),
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
    rows = []
    history_id = 1

    for _, app in applications_df.iterrows():
        submitted_at = app["submited_at"]
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

            rows.append({
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

    return pd.DataFrame(rows)

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

        status = random.choices(
            MEMBER_STATUSES,
            weights=[75, 5, 10, 10],
            k=1
        )[0]

        cancelled_at = None
        if status == "Cancelled":
            cancelled_at = approved_at + pd.Timedelta(days=random.randint(60, 900))


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
            "registered_at": app["submited_at"],
            "approved_at": approved_at,
            "cancelled_at": cancelled_at,
        })

    return pd.DataFrame(members)

companies_df = generate_companies()
companies_df.to_csv(OUTPUT_DIR / "companies.csv", index=False)

applications_df = generate_membership_applications(companies_df)
applications_df.to_csv(OUTPUT_DIR / "membership_applications.csv", index=False)

application_status_history_df = generate_application_status_history(applications_df)
application_status_history_df.to_csv(OUTPUT_DIR / "application_status_history.csv", index=False)

members_df = generate_members(applications_df, application_status_history_df)
members_df.to_csv(OUTPUT_DIR / "members.csv", index=False)