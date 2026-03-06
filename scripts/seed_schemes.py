#!/usr/bin/env python3
"""
Seed script: loads initial government scheme data into DynamoDB and OpenSearch.
Run once on environment setup: python3 scripts/seed_schemes.py --env dev
"""
import boto3
import json
import argparse
import sys
from decimal import Decimal
from datetime import datetime

SCHEMES = [
    {
        "scheme_id": "PM-KISAN-2024",
        "sk": "VERSION#latest",
        "name_en": "PM Kisan Samman Nidhi",
        "name_hi": "प्रधानमंत्री किसान सम्मान निधि",
        "ministry": "Ministry of Agriculture & Farmers Welfare",
        "categories": ["agriculture", "income_support"],
        "benefit_amount": Decimal("6000"),
        "benefit_frequency": "annual",
        "eligible_states": ["ALL"],
        "eligible_occupations": ["farmer"],
        "eligibility_criteria": {
            "occupation": ["farmer"],
            "max_land_acres": Decimal("5"),
            "excluded_categories": ["government_employee", "income_taxpayer", "institutional_landholders"]
        },
        "required_documents": ["aadhaar", "bank_account", "land_records"],
        "application_url": "https://pmkisan.gov.in",
        "last_verified": "2024-01-10",
        "active": True,
        "description_en": "PM-KISAN provides income support of Rs 6000 per year to all land-holding farmer families in India. Amount is transferred directly to bank accounts in three equal installments of Rs 2000 each.",
        "description_hi": "पीएम-किसान योजना के तहत सभी भूमिधारी किसान परिवारों को प्रति वर्ष 6000 रुपये की आय सहायता दी जाती है।"
    },
    {
        "scheme_id": "PMAY-G-2024",
        "sk": "VERSION#latest",
        "name_en": "Pradhan Mantri Awaas Yojana - Gramin",
        "name_hi": "प्रधानमंत्री आवास योजना - ग्रामीण",
        "ministry": "Ministry of Rural Development",
        "categories": ["housing", "rural_development"],
        "benefit_amount": Decimal("120000"),
        "benefit_frequency": "one_time",
        "eligible_states": ["ALL"],
        "eligible_occupations": ["ALL"],
        "eligibility_criteria": {
            "housing_status": ["houseless", "kutcha_house"],
            "bpl_category": True,
            "excluded_categories": ["government_employee", "motorized_vehicle_owner"]
        },
        "required_documents": ["aadhaar", "bank_account", "bpl_card", "land_proof"],
        "application_url": "https://pmayg.nic.in",
        "last_verified": "2024-01-10",
        "active": True,
        "description_en": "PMAY-G provides financial assistance of Rs 1.20 lakh in plain areas and Rs 1.30 lakh in hilly/NE states for construction of pucca houses to eligible rural poor.",
        "description_hi": "पीएमएवाई-ग्रामीण के तहत पात्र ग्रामीण गरीबों को पक्का मकान बनाने के लिए 1.20 लाख रुपये की आर्थिक सहायता दी जाती है।"
    },
    {
        "scheme_id": "MGNREGS-2024",
        "sk": "VERSION#latest",
        "name_en": "Mahatma Gandhi NREGS",
        "name_hi": "महात्मा गांधी राष्ट्रीय ग्रामीण रोजगार गारंटी अधिनियम",
        "ministry": "Ministry of Rural Development",
        "categories": ["employment", "rural_development"],
        "benefit_amount": None,
        "benefit_frequency": "per_day",
        "eligible_states": ["ALL"],
        "eligible_occupations": ["ALL"],
        "eligibility_criteria": {
            "residence": ["rural"],
            "adult_willing_to_work": True,
        },
        "required_documents": ["aadhaar", "job_card", "bank_account"],
        "application_url": "https://nrega.nic.in",
        "last_verified": "2024-01-10",
        "active": True,
        "description_en": "MGNREGS guarantees 100 days of unskilled wage employment per year to every rural household whose adult members volunteer to do unskilled manual work.",
        "description_hi": "मनरेगा के तहत हर ग्रामीण परिवार के वयस्क सदस्यों को वर्ष में 100 दिन के अकुशल मजदूरी रोजगार की गारंटी है।"
    },
    {
        "scheme_id": "PMJDY-2024",
        "sk": "VERSION#latest",
        "name_en": "Pradhan Mantri Jan Dhan Yojana",
        "name_hi": "प्रधानमंत्री जन धन योजना",
        "ministry": "Ministry of Finance",
        "categories": ["finance", "banking"],
        "benefit_amount": None,
        "benefit_frequency": "one_time",
        "eligible_states": ["ALL"],
        "eligible_occupations": ["ALL"],
        "eligibility_criteria": {
            "unbanked": True,
            "age_gte": 10
        },
        "required_documents": ["aadhaar", "pan_or_form60"],
        "application_url": "https://pmjdy.gov.in",
        "last_verified": "2024-01-10",
        "active": True,
        "description_en": "PMJDY ensures access to financial services, namely Banking/Savings & Deposit Accounts, Remittance, Credit, Insurance, Pension in an affordable manner.",
        "description_hi": "पीएमजेडीवाई वित्तीय सेवाओं तक पहुंच सुनिश्चित करता है, जैसे कि बैंकिंग/बचत और जमा खाते, प्रेषण, क्रेडिट, बीमा, पेंशन किफायती तरीके से।"
    },
    {
        "scheme_id": "PMJJBY-2024",
        "sk": "VERSION#latest",
        "name_en": "Pradhan Mantri Jeevan Jyoti Bima Yojana",
        "name_hi": "प्रधानमंत्री जीवन ज्योति बीमा योजना",
        "ministry": "Ministry of Finance",
        "categories": ["finance", "insurance", "life"],
        "benefit_amount": Decimal("200000"),
        "benefit_frequency": "one_time",
        "eligible_states": ["ALL"],
        "eligible_occupations": ["ALL"],
        "eligibility_criteria": {
            "age_gte": 18,
            "age_lte": 50,
            "has_bank_account": True
        },
        "required_documents": ["aadhaar", "bank_account"],
        "application_url": "https://jansuraksha.gov.in",
        "last_verified": "2024-01-10",
        "active": True,
        "description_en": "PMJJBY is a one-year life insurance scheme renewable from year to year offering coverage for death due to any reason.",
        "description_hi": "यह एक वर्षीय जीवन बीमा योजना है जिसका हर साल नवीनीकरण किया जा सकता है। यह किसी भी कारण से होने वाली मृत्यु पर कवरेज प्रदान करती है।"
    },
    {
        "scheme_id": "PMSBY-2024",
        "sk": "VERSION#latest",
        "name_en": "Pradhan Mantri Suraksha Bima Yojana",
        "name_hi": "प्रधानमंत्री सुरक्षा बीमा योजना",
        "ministry": "Ministry of Finance",
        "categories": ["finance", "insurance", "accident"],
        "benefit_amount": Decimal("200000"),
        "benefit_frequency": "one_time",
        "eligible_states": ["ALL"],
        "eligible_occupations": ["ALL"],
        "eligibility_criteria": {
            "age_gte": 18,
            "age_lte": 70,
            "has_bank_account": True
        },
        "required_documents": ["aadhaar", "bank_account"],
        "application_url": "https://jansuraksha.gov.in",
        "last_verified": "2024-01-10",
        "active": True,
        "description_en": "PMSBY is an accident insurance scheme offering accidental death and disability cover for death or disability on account of an accident.",
        "description_hi": "यह एक दुर्घटना बीमा योजना है जो दुर्घटना के कारण मृत्यु या विकलांगता को कवर करती है।"
    },
    {
        "scheme_id": "PMJAY-2024",
        "sk": "VERSION#latest",
        "name_en": "Ayushman Bharat PM-JAY",
        "name_hi": "आयुष्मान भारत - प्रधानमंत्री जन आरोग्य योजना",
        "ministry": "Ministry of Health and Family Welfare",
        "categories": ["health", "insurance"],
        "benefit_amount": Decimal("500000"),
        "benefit_frequency": "annual",
        "eligible_states": ["ALL"],
        "eligible_occupations": ["ALL"],
        "eligibility_criteria": {
            "bpl_category": True
        },
        "required_documents": ["aadhaar", "ration_card"],
        "application_url": "https://pmjay.gov.in",
        "last_verified": "2024-01-10",
        "active": True,
        "description_en": "PM-JAY provides a health cover of Rs. 5 lakhs per family per year for secondary and tertiary care hospitalization to over 12 crores poor and vulnerable families.",
        "description_hi": "पीएम-जय गरीब परिवारों को अस्पताल में माध्यमिक और तृतीयक देखभाल के लिए प्रति परिवार प्रति वर्ष 5 लाख रुपये का स्वास्थ्य कवर प्रदान करता है।"
    },
]

ELIGIBILITY_RULES = [
    {
        "scheme_id": "PM-KISAN-2024",
        "sk": "RULES#latest",
        "application_url": "https://pmkisan.gov.in",
        "required_documents": ["aadhaar", "bank_account", "land_records"],
        "criteria": [
            {"field": "occupation", "operator": "in", "value": ["farmer", "agriculture"], "weight": 2.5, "message_hi_pass": "आप किसान हैं", "message_hi_fail": "यह योजना केवल किसानों के लिए है", "message_en_pass": "You are a farmer", "message_en_fail": "This scheme is only for farmers"},
            {"field": "annual_income", "operator": "lte", "value": 200000, "weight": 1.0, "message_hi_pass": "आय पात्रता सीमा के अंदर है", "message_hi_fail": "वार्षिक आय बहुत अधिक है", "message_en_pass": "Income within limit", "message_en_fail": "Annual income too high"},
            {"field": "land_holdings_acres", "operator": "between", "value": [0.1, 5.0], "weight": 2.0, "message_hi_pass": "भूमि जोत पात्र है", "message_hi_fail": "भूमि जोत सीमा से बाहर है", "message_en_pass": "Land holding eligible", "message_en_fail": "Land holding out of range"},
        ]
    },
    {
        "scheme_id": "MGNREGS-2024",
        "sk": "RULES#latest",
        "application_url": "https://nrega.nic.in",
        "required_documents": ["aadhaar", "job_card", "bank_account"],
        "criteria": [
            {"field": "age", "operator": "gte", "value": 18, "weight": 2.0, "message_hi_pass": "आयु पात्र है", "message_hi_fail": "18 वर्ष से कम आयु", "message_en_pass": "Age eligible", "message_en_fail": "Below 18 years"},
        ]
    },
    {
        "scheme_id": "PMJDY-2024",
        "sk": "RULES#latest",
        "application_url": "https://pmjdy.gov.in",
        "required_documents": ["aadhaar"],
        "criteria": [
            {"field": "age", "operator": "gte", "value": 10, "weight": 2.0, "message_hi_pass": "आयु 10 वर्ष से अधिक है", "message_hi_fail": "आयु 10 वर्ष से कम है", "message_en_pass": "Age is over 10 years", "message_en_fail": "Age is under 10 years"},
        ]
    },
    {
        "scheme_id": "PMJJBY-2024",
        "sk": "RULES#latest",
        "application_url": "https://jansuraksha.gov.in",
        "required_documents": ["aadhaar", "bank_account"],
        "criteria": [
            {"field": "age", "operator": "between", "value": [18, 50], "weight": 3.0, "message_hi_pass": "आयु 18 से 50 वर्ष के बीच है", "message_hi_fail": "आयु 18-50 वर्ष के बीच होनी चाहिए", "message_en_pass": "Age between 18 and 50", "message_en_fail": "Must be between 18-50 years"},
        ]
    },
    {
        "scheme_id": "PMSBY-2024",
        "sk": "RULES#latest",
        "application_url": "https://jansuraksha.gov.in",
        "required_documents": ["aadhaar", "bank_account"],
        "criteria": [
            {"field": "age", "operator": "between", "value": [18, 70], "weight": 3.0, "message_hi_pass": "आयु 18 से 70 वर्ष के बीच है", "message_hi_fail": "आयु 18-70 वर्ष के बीच होनी चाहिए", "message_en_pass": "Age between 18 and 70", "message_en_fail": "Must be between 18-70 years"},
        ]
    },
    {
        "scheme_id": "PMJAY-2024",
        "sk": "RULES#latest",
        "application_url": "https://pmjay.gov.in",
        "required_documents": ["aadhaar", "ration_card"],
        "criteria": [
            {"field": "annual_income", "operator": "lte", "value": 120000, "weight": 3.0, "message_hi_pass": "कम आय वाला परिवार", "message_hi_fail": "आय सीमा से अधिक है", "message_en_pass": "Low income family", "message_en_fail": "Income exceeds BPL limit"},
        ]
    },
    {
        "scheme_id": "PMAY-G-2024",
        "sk": "RULES#latest",
        "application_url": "https://pmayg.nic.in",
        "required_documents": ["aadhaar", "job_card", "bank_account", "swachh_bharat_mission_number"],
        "criteria": [
            {"field": "annual_income", "operator": "lte", "value": 150000, "weight": 4.0, "message_hi_pass": "आय आवश्यकता को पूरा करती है", "message_hi_fail": "आय सीमा से अधिक है", "message_en_pass": "Meets income criteria for rural housing", "message_en_fail": "Income above rural housing threshold"},
        ]
    },
    {
        "scheme_id": "MGNREGS-2024",
        "sk": "RULES#latest",
        "application_url": "https://nrega.nic.in",
        "required_documents": ["aadhaar", "bank_account", "photograph"],
        "criteria": [
            {"field": "age", "operator": "gte", "value": 18, "weight": 5.0, "message_hi_pass": "वयस्क नागरिक", "message_hi_fail": "नाबालिग नागरिक", "message_en_pass": "Adult citizen", "message_en_fail": "Minor citizen"},
        ]
    }
]


def seed(env: str):
    dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
    
    schemes_table = dynamodb.Table(f"sahayak-{env}-schemes")
    rules_table = dynamodb.Table(f"sahayak-{env}-eligibility-rules")

    print(f"Seeding schemes into sahayak-{env}-schemes...")
    for scheme in SCHEMES:
        schemes_table.put_item(Item={**scheme, "seeded_at": datetime.utcnow().isoformat()})
        print(f"  Seeded: {scheme['scheme_id']}")

    print(f"Seeding eligibility rules into sahayak-{env}-eligibility-rules...")
    for rules in ELIGIBILITY_RULES:
        rules_table.put_item(Item={**rules, "seeded_at": datetime.utcnow().isoformat()})
        print(f"  Seeded rules: {rules['scheme_id']}")

    print("Seeding complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", default="dev", choices=["dev", "staging", "prod"])
    args = parser.parse_args()
    
    if args.env == "prod":
        confirm = input("WARNING: Seeding PRODUCTION. Type 'yes' to confirm: ")
        if confirm != "yes":
            print("Aborted.")
            sys.exit(0)
    
    seed(args.env)
