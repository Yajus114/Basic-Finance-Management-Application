import pandas as pd
import os
from dotenv import dotenv_values
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

"""
    The finance manager excel file will have columns:
    1. Date
    2. Amount in the account
    3. Salary amount received
    4. Total amount in account (Amount in the account + Salary amount received)
    5. Total amount to be saved in the account until next salary (20% of principal amount + salary)
    6. Spendable amount

    The finance manager will ask the user to enter the following details:
    1. Date
    2. Amount in the account
    3. Salary amount received

    The starting date is 11th May 2024. The user will enter the date in the format "DD-MM-YYYY".
    The app should start with the initial amount in the account as ₹7625.43 and the amount to be saved as 20% of this amount = ₹1526.086
    The app should also round off the amount to be saved to the nearest integer value.
"""
env = dotenv_values("secrets.env")

SCOPES = env.get("SCOPES")
ID = env.get("ID")
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{ID}"
TOKEN_PATH = env.get("TOKEN_PATH")
CREDENTIALS_PATH = env.get("CREDENTIALS_PATH")


def get_credentials():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())
    return creds


def get_sheet():
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()
    return sheet


def append_to_sheet(sheet):
    date = input("Would you like to enter the date or use the current date? (1/2): ")
    if date == "1":
        date = input("Enter the date in the format DD-MM-YYYY: ")
    else:
        from datetime import datetime

        date = datetime.now().strftime("%d-%m-%Y")

    amount = float(input("Enter the amount in the account: "))
    salary = input(
        "Would you like to enter the salary amount received or use the default value? (1/2): "
    )
    if salary == "1":
        salary = float(input("Enter the salary amount received: "))
    else:
        salary = float(env.get("SALARY"))

    total_amount = amount + salary
    amount_to_save = round(total_amount * 0.2)
    spendable_amount = round(total_amount - amount_to_save)

    values_table = [
        [date, amount, salary, total_amount, amount_to_save, spendable_amount]
    ]
    body = {"values": values_table}
    sheet.values().append(
        spreadsheetId=ID,
        range="Sheet1",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body=body,
    ).execute()


if __name__ == "__main__":
    try:
        sheet = get_sheet()
        if sheet:
            print("Successfully connected to the Google Sheets API.")
            values = sheet.values().get(spreadsheetId=ID, range="Sheet1").execute()
            data = values.get("values", [])
            if not data:
                print("No data found.")
            else:
                df = pd.DataFrame(data[1:], columns=data[0])
                print(df)
            append_to_sheet(sheet, values)
            print(
                "Data successfully appended to the Google Sheet. You can check the sheet here:",
                SHEET_URL,
            )
        else:
            print("Failed to connect to the Google Sheets API.")
    except HttpError as e:
        print(f"An error occurred: {e}")
