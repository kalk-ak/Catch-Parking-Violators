from typing import Dict, List, Optional, Set  # Used for static typing to reduce errors

import pandas as pd
from abs_time import (
    abs_time,
)  # Function that converts time and date into a minutes time scale that i can compare
from User import User  # Class to encapsulate users and all thier transactions


# Define ANSI escape codes as constants to make print statements in color
class AnsiColors:
    RED = "\033[91m"
    RESET = "\033[0m"  # Resets all text attributes to default
    LIGHT_BLUE = "\033[94m"


# ===================================================================================
# SCRIPT PURPOSE: Flag Violation Vehicle Parking Transactions
# ===================================================================================

# OVERVIEW:
# This script analyzes parking transaction data to enforce the one-vehicle-per-subscription rule.
# According to the enterprise subscription terms, a user can only have one registered vehicle
# parked at any given time. This code identifies and flags transactions that violate this rule.

# DATA SOURCES:
# 1. Enterprise Subscription Data: Contains a registry of all active users and their
#    associated license plates.
# 2. Transaction Data: A log of all individual parking transactions, linked to the
#    subscription data via the license plate. For security, this data is anonymized
#    and does not contain personal user information.
#
#    The only information this code uses to associate each transaction to the subscribed user
#    is the vehicles license plate.

# LOGIC:
# The script reads both data sources and checks for overlapping parking times for the
# same license plate. If two vehicles associated with the same subscription are found
# to be parked concurrently, the second transaction is marked as "delinquent."


# ==================================================================================
#  SECTION 1: Convert the CSV data to Data Frames that are processable
# ==================================================================================

# Select only the necessary columns from the transaction data to improve performance.
path_of_read: str = "~/codes/projects/solomon_project/python_script/data/"
transaction_data: pd.DataFrame = pd.read_csv(
    (path_of_read + "transaction_data.csv"),
    usecols=[
        "Site Internal Name",
        "Visit Start Date (local)",
        "Visit Start Time (local)",
        "Visit End Date (local)",
        "Visit End Time (local)",
        "Visit Duration (minutes)",
        "Vehicle License Plate",
        "License Plate State",
        "User Id",
        "User Registered Date",
        "Subscription Status",
    ],
    encoding="UTF-16",
    low_memory=False,
)

# Read the enterprise subscription data
enterprise_subscription_data: pd.DataFrame = pd.read_csv(
    path_of_read + "enterprise_subscription_detail.csv",
    encoding="UTF-16",
)


# Filter out the columns names to   the sites we are interested in
# Only 1st Vehicle and Additional Vehicle is considered in the analysis
# TODO: Remove Additional Veshicle
enterprise_subscription_data = enterprise_subscription_data[
    (
        enterprise_subscription_data["Enterprise Name"]
        == "Kellogg Square Residents - 1 st Vehicle"
    )
    | (
        enterprise_subscription_data["Enterprise Name"]
        == "Kellogg Square Residents -Additional Vehicle"
    )
]

# Reset the index so that we can use index based looping across the data frame
enterprise_subscription_data = enterprise_subscription_data.reset_index(drop=True)


# Transient transactions are short parking stays the user already paid for
transaction_data = transaction_data[
    (
        transaction_data["Subscription Status"] != "Transient"
    )  # Remove transient transactions
    & (
        (
            transaction_data[
                "Site Internal Name"
            ]  # Filter the parking sites we are interested in
            == "Kellogg Square Reserved Nest (Minneapolis"
        )
        | (
            transaction_data["Site Internal Name"]
            == "Kellogg Square Garage (Minneapolis"
        )
    )
]

# Reset the index so that we can use index based looping across the data frame
transaction_data = transaction_data.reset_index(drop=True)


# Assert that both transaction_data and enterprise_subscription_data are instances of a data frame before continuing
# Although filtering a data frame returns a data frame, this code is just to be safe
assert isinstance(transaction_data, pd.DataFrame), (
    "Filtering did not return a DataFrame!"
)
assert isinstance(enterprise_subscription_data, pd.DataFrame), (
    "Filtering did not return a DataFrame!"
)


# ===================================================================================
# SECTION 2: Organize the Data and transactions made by the subscribed users
# ===================================================================================

# ------------- List of Collections to organize users and their transactions ----------------

# A dictionary mapping user emails (str) to their corresponding User object.
# This registry is populated by the `add_user` function.
users_by_email: Dict[str, User] = {}

# A dictionary mapping each license plate to a set of user emails associated with it.
# This is primarily used to detect if a single license plate is improperly registered
# to more than one user account.
plate_to_emails: Dict[str, Set[str]] = {}

# A counter to keep track of the number of users without an email
no_email_users: int = 0

# A fallback registry for users who don't have an associated email.
# - Key: License plate (str)
# - Value: The User object instance.
unidentified_users: Dict[str, User] = {}


def add_user(user: User, plate: str) -> None:
    """
    Registers a user and their license plate in either users_by_email or unidentified_users.

    The function's behavior is determined by the user's email attribute

    - If email exists: The user is added/updated in `users_by_email` dictionary
    - If no email exists: The user is added to `unidentified_users` using the license plate as a key

    Args:
        user (User): The user object to process.
        plate (str): The license plate to associate with the user.

    Returns:
        None

    Side Effects:
        - `users_by_email`: Adds a new user or updates an existing one.
        - `plate_to_emails`: Adds the plate-to-email link for duplicate checks.
        - `unidentified_users`: Adds the user if they have no email.
        - `no_email_users`: Incremented if the user has no email.
    """

    if user.email is not None:
        # --- Handle users identified by an email address ---

        # If the user is new, add them to the main registry.
        # Otherwise, add the new license plate to the existing user's record.
        if user.email not in users_by_email:
            users_by_email[user.email] = user
        else:
            users_by_email[user.email].add_license(plate)

        # Now, update the reverse-lookup table to track which emails use this plate.
        # This is how we detect if one plate is improperly used by multiple accounts.
        if plate in plate_to_emails:
            plate_to_emails[plate].add(user.email)
        else:
            plate_to_emails[plate] = {user.email}

    else:
        # --- Handle users without an email (identified by license plate) ---

        # Add the user to the fallback dictionary keyed by their license plate.
        unidentified_users[plate] = user


# Process enterprise data to group all vehicles under their respective users.
# After initial grouping, this also aggregates unidentified users by license plate
# to validate that each plate is associated with only one user.
for label, row in enterprise_subscription_data.iterrows():
    # Extract and clean the license plate.
    current_plate = str(row["Vehicle License Plate Text"]).strip()

    # Check if the user email is missing in this record.
    if pd.isna(row["User Email"]):  # type: # pyright: ignore
        # If email is missing, create a placeholder User object.
        # This user is identified only by their license plate for now.
        current_user = User(
            first=None,
            last=None,
            email=None,
            number=None,
            license=current_plate,
            id_num=None,
        )
    else:
        # If email exists, create a complete User object with all details.
        current_user = User(
            first=str(row["User First Name"]),
            last=str(row["User Last Name"]),
            email=str(row["User Email"]),
            number=int(row["User Phone Number"]),
            license=current_plate,
        )

    # Pass the user and plate to our main function to populate the global registries
    # (users_by_email, plate_to_emails, unidentified_users)
    add_user(current_user, current_plate)


# If there are unidentified users that made a transaction then we can
# get their User Id from the transaction data

# This counter variable keeps count of the found users
found_users: int = 0


# Loop through the transaction data and group all the transactions by users
# Also look for the user-name, email, and number for id-users
for label, row in transaction_data.iterrows():
    current_plate: str = str(row["Vehicle License Plate"])
    current_user: Optional[User] = None

    # --------------Part 2---------------
    # Check if the transaction was made by a user who is subscribed to the enterprise

    # First check if the current plate is associated with an email in our enterprise
    if current_plate in plate_to_emails:
        # Retrieve the user object via their email.
        # NOTE: We take the first email from the set, assuming one plate maps to one primary user.
        # If there are multiple emails associated with this license get a random email from the set
        associated_email: str = next(iter(plate_to_emails[current_plate]))
        current_user = users_by_email[associated_email]

        # If this is the first time we saw the user
        # get their User Id from transaction data
        if current_user.id is None:
            current_user.id = int(row["User Id"])

    # Then check if the transaction was made by an unidentified_users in our enterprise
    elif current_plate in unidentified_users:
        # Since we can get the User Id from the transaction data
        # We can identify the user by their User Id
        # NOTE: User Id for some reason isn't available in enterprise data and only available in transaction data
        current_user = unidentified_users[current_plate]

        # If this is the first time we've seen a transaction for this user,
        # we can finally get their ID and count them as "found".
        if current_user.id is None:
            current_user.id = int(row["User Id"])
            found_users += 1

    # ----------------Part 2-----------------------------
    # If the transaction was made by a user in our enterprise
    # group each transaction under each user object so that it gets easier
    # when searching for delinquent transactions later
    if current_user is not None:
        # Create a DataFrame for the current transaction row.
        current_transaction_series = transaction_data.loc[label].copy()

        # Get the start/end time and date for the transaction
        visit_time = str(row["Visit Start Time (local)"])
        visit_date = str(row["Visit Start Date (local)"])
        end_time = str(row["Visit End Time (local)"])
        end_date = str(row["Visit End Date (local)"])

        # Calculate the absolute start and end times in minutes for the transaction.
        # abs_time is defined in abs_time.py as a helper function
        transaction_times: List[int] = abs_time(
            visit_time, visit_date, end_time, end_date
        )

        # Add the calculated absolute times in minute as a column to the current_transaction
        current_transaction_series["Absolute Visit Time"] = transaction_times[0]
        current_transaction_series["Absolute Leave Time"] = transaction_times[1]

        # If users park two or more vehicles at the same time
        # all the transactions other than the first is marked as a violation
        current_transaction_series["Violation"] = ""  # To be populated later

        # Add the transaction data to the data frame in each user
        current_user.transactions = pd.concat(
            # NOTE: Before concatinating a series to frame we must first transpose it
            [current_user.transactions, current_transaction_series.to_frame().T],
            ignore_index=True,
        )


# ===================================================================================
# SECTION 3: Organize the enterprise subscription data
# ===================================================================================

# A list to store emails from accounts that share a license plate with another account.
# This indicates a data mismatch where one plate is registered to multiple users.
emails_with_plate_mismatch: Set[str] = set()


# This Data Frame will hold transactions made by each user and would mark the violator transactions
# NOTE: This is the final desired output
organized_transaction = pd.DataFrame()


# NOTE: Previous version of code built the data frame row by row
# A more efficient approach would be to Populate a list of dictionary and make the data frame at the end

# list is fixed in size with placeholder for efficiency so that it doesn't get resided
user_records: List[Optional[Dict]] = [None] * (
    len(users_by_email) + len(unidentified_users)
)


for current_user in users_by_email.values():
    # -------- 1 -----------
    # Sort the user transactions by end time so that we can use a faster greedy algorithm to get violator transactions
    if not current_user.transactions.empty:
        current_user.transactions.sort_values(
            by="Absolute Leave Time", ignore_index=True
        )

    # --------- 2-----------
    # Check for License Plate Registrations mismatch
    # NOTE: current_user.licence is a set and mismatch's happen because of a flow in the Registrations system
    has_mismatch: str = ""
    for plate in current_user.license:
        # check if this email is associated with more than 1 email
        if len(plate_to_emails[plate]) > 1:
            has_mismatch = "Yes"
            emails_with_plate_mismatch.add(current_user.email)

    # --------- 3 -------------
    # Populate the list of dictionary for creating an organized data frame at the end
    # This dictionary represents a single row in the data frame
    record = {
        "First": current_user.first,
        "Last": current_user.last,
        "Email": current_user.email,
        "ID": current_user.id,
        "Phone Number": current_user.number,
        "License": ", ".join(map(str, current_user.license)),
        "Has mismatch": has_mismatch,
    }

    # This is the list that finally gets converted to a frame
    user_records.append(record)

# Iterate through each unidentified users to group them after the users with email.
for current_user in unidentified_users.values():
    # ------------ 4 -------------

    # Unidentified users are guaranteed by our logic to have only one license plate.
    # This assertion will halt the program if that assumption is ever violated.
    assert len(current_user.license) == 1, (
        f"Unidentified user has multiple plates: {current_user.license}"
    )
    current_plate = next(iter(current_user.license))

    # Sort the transactions made by unidentified_users
    if not current_user.transactions.empty:
        current_user.transactions.sort_values(
            by="Absolute Leave Time", ignore_index=True
        )

    # -------- 5 -----------
    # Check for mismatch
    # NOTE: we can not directly check if unidentified_users have mismatched plates
    # Instead what this code does is checks if the plate has an associated email

    has_mismatch = ""  # Assume no mismatch by default
    email_found = ""

    # A mismatch occurs if this plate is also found in our `plate_to_emails` lookup,
    # meaning parkers registered the vehicle twice. Once with email and the other one without
    if current_plate in plate_to_emails:
        has_mismatch = "Yes"
        email_found = "Email Found"

    # -------- 6 ---------
    # Create a Dictionary Record for this Unidentified user
    # This record is added after the users with an email are added
    record = {
        "First": current_user.first,
        "Last": current_user.last,
        "Email": current_user.email,
        "ID": current_user.id,
        "Phone Number": current_user.number,
        "License": ", ".join(map(str, current_user.license)),
        "Has mismatch": has_mismatch,
        "email_found": email_found,
    }
    # append the transaction record to list.
    # It is finally converted to a data frame
    user_records.append(record)


# ---------- 7 -----------
# creating the data frame
# Each Users with plate mismatch is marked and all the license plates are grouped under their associated email
assert user_records[-1] != None, (
    "Logic error detected in populating List with transactions. \nArray Length shorter than expected"
)
organized_subscription = pd.DataFrame(user_records)


# ===================================================================================
# SECTION 4: Organize the transaction data and flag the violating transactions
# ===================================================================================
# NOTE: This is the main section of the code
# All the codes before were a set up and pre-processing for this part of code

index: int = 0
for current_user in users_by_email.values():
    # --- Prepare for Processing ---

    # Get the number of transactions for this user; skip if there are none.
    n = len(current_user.transactions)
    if n == 0:
        continue

    # Ensure the index is a clean 0-based sequence for reliable .loc access.
    current_user.transactions.reset_index(drop=True, inplace=True)

    # --- Two-Pointer Algorithm to Find Parking Violations ---
    # This algorithm checks for overlapping parking times for a single user.
    # 'i' serves as the anchor, pointing to the last known valid transaction.
    # 'j' is the scanner, checking the next transaction against the anchor.
    i = 0
    j = 1

    while j < n:
        # Get the departure time of the anchor vehicle.
        parked = int(current_user.transactions.loc[i, "Absolute Leave Time"])
        # Get the arrival time of the next vehicle.
        next_arrival = int(current_user.transactions.loc[j, "Absolute Visit Time"])

        # Core Logic: If the next vehicle arrives before the anchor vehicle has left,
        # it's a violation of the "one-vehicle-at-a-time" rule.
        if next_arrival < parked:
            current_user.transactions.loc[j, "Violation"] = "Violator"
        else:
            # If there's no overlap, this transaction is valid and becomes the new anchor.
            i = j

        # --- Populate the Consolidated 'organized_transaction' DataFrame ---
        # For each transaction processed by the scanner (j), copy its details and
        # violation status into the final, combined DataFrame.
        organized_transaction.loc[index, "Email"] = current_user.email
        organized_transaction.loc[index, "Visit Start Date"] = (
            current_user.transactions.loc[j, "Visit Start Date (local)"]
        )
        organized_transaction.loc[index, "Visit Start Time"] = (
            current_user.transactions.loc[j, "Visit Start Time (local)"]
        )
        organized_transaction.loc[index, "Visit End Date"] = (
            current_user.transactions.loc[j, "Visit End Date (local)"]
        )
        organized_transaction.loc[index, "Visit End Time"] = (
            current_user.transactions.loc[j, "Visit End Time (local)"]
        )
        organized_transaction.loc[index, "Visit Duration (minutes)"] = (
            current_user.transactions.loc[j, "Visit Duration (minutes)"]
        )
        organized_transaction.loc[index, "License Plate"] = (
            current_user.transactions.loc[j, "Vehicle License Plate"]
        )
        organized_transaction.loc[index, "User Id"] = current_user.id

        # Ensure the 'Violation' status is copied over correctly.
        # This handles cases where the column might not have been created yet.
        organized_transaction.loc[index, "Violation"] = current_user.transactions.loc[
            j, "Violation"
        ]

        # Increment both the scanner and the master index for the next loop.
        j += 1
        index += 1

# print the results
print("\n")
print(f"{AnsiColors.LIGHT_BLUE}--- Initial Data Summary ---{AnsiColors.RESET}")
print(
    f"Total Transactions Read = {AnsiColors.RED}{len(transaction_data)}{AnsiColors.RESET}"
)
print(
    f"Total Subscriptions Read = {AnsiColors.RED}{len(enterprise_subscription_data)}{AnsiColors.RESET}"
)
print("\n")

print(f"{AnsiColors.LIGHT_BLUE}--- User Processing Status ---{AnsiColors.RESET}")
print(
    f"Users identified with Email = {AnsiColors.RED}{len(users_by_email)}{AnsiColors.RESET}"
)
print(f"Users without Email = {AnsiColors.RED}{no_email_users}{AnsiColors.RESET}")
print(
    f"Users without email found in transaction data = {AnsiColors.RED}{found_users}{AnsiColors.RESET}"
)
print("\n")

print(f"{AnsiColors.LIGHT_BLUE}--- Data Integrity Checks ---{AnsiColors.RESET}")
print(
    f"Total unique license plates found = {AnsiColors.RED}{len(plate_to_emails)}{AnsiColors.RESET}"
)
print(
    f"Users involved in a plate mismatch = {AnsiColors.RED}{len(emails_with_plate_mismatch)}{AnsiColors.RESET}"
)
print("\n")


# Define the output directory for the final Excel reports.
path: str = "~/codes/projects/solomon_project/python_script/test_output/"

# For a cleaner final report, mask duplicate emails in the transaction list,
# showing an email only on its first appearance for a given user.
organized_transaction["Email"] = organized_transaction["Email"].mask(
    organized_transaction["Email"].duplicated(), ""
)

# Save the two main DataFrames to separate Excel files.
# `index=False` is used to prevent writing the pandas index as a column.
organized_subscription.to_excel(
    path + "Organized Enterprise Subscription.xlsx", index=False
)
organized_transaction.to_excel(path + "Final Report.xlsx", index=False)

print(
    f"{AnsiColors.LIGHT_BLUE}Successfully generated Excel reports in: {AnsiColors.RESET}{path}"
)
