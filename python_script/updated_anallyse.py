from typing import Dict, List, Optional, Set

import pandas as pd


class User:
    """
    Encapsulate the users (Car Owners) into class

    User Class has the following attributes

        first (str): The first Name of the user
        last (str): The last Name of the user
        email (str): The email address of the user
        number (int): The phone number of the user
        licence (list): The licence plates of the car
        Id (int): The identificatiion number of the user.
        Initially set to None - only filled if the user has no email

        Filled late >>>

        licence_status (list): The status of each licence.
            Filled after the licence plate list is populated.
            (Subscription Added or Subscription Removed)
        licence_type: (list): The type of each licence.
            Filled after the licence plate list is populated.
            (First, Additional, Other)
        first_only_licence (list): List of the first vehicles.
            (Used to calculate the max transaction)
        additional_only_licence (list): List of the additional vehicles.
            (Used to calculate the max transaction)
        other_licence: List of cars that are neither first or additional
    """

    def __init__(
        self,
        first: Optional[str],
        last: Optional[str],
        email: Optional[str],
        number: Optional[int],
        licence: str,
        id_num=None,
    ) -> None:
        """
        Initalize all the variables
        """
        self.first = first
        self.last = last
        self.email = email
        self.number = number
        self.licence: Set[str] = {licence}
        #  FIX: I don't think licene status is important
        self.licence_status = []

        self.first_licence = None
        self.additional_licence = None

        # Initially the user ID is set to None and
        # only changed if the user doesn't have a first name or last name
        self.id = id_num

        assert (self.email is None) ^ (self.id is None)
        # Populated later on from the data. Initially set to empty string

    def __len__(self):
        return len(self.licence)

    def __eq__(self, other):
        """
        Parameter other can be int (ID number), string (email), or another user
        """

        if isinstance(other, User):
            if self.email is not None:
                return self.email == other.email

            return self.id == other.id

        if isinstance(other, str):
            return self.email == other

        if isinstance(other, int):
            return self.id == other

        return False

    def __str__(self):

        if self.id is None:
            out = (
                f"First: {self.first}\n"
                + f"Last: {self.last}\n"
                + f"Email: {self.email}\n"
                + f"Car Number: {len(self.licence)}\n _______________________________________________ \n"
            )

        else:
            out = (
                f"ID: {self.id}\n"
                + f"Car Number: {len(self.licence)}\n _______________________________________________ \n"
            )

        return out

    def add_licence(self, licence: str):
        """
        Adds a new licence plate to the list of licence plates for this user
        """
        self.licence.add(licence)


# Reads all the datas to a data Frame

transaction_data = pd.read_csv(
    "~/codes/projects/solomon_project/python_script/data/transaction_data.csv",
    encoding="UTF-16",
    low_memory=False,
)
enterprise_subscription_data = pd.read_csv(
    "~/codes/projects/solomon_project/python_script/data/enterprise_subscription_detail.csv",
    encoding="UTF-16",
)


# Filter the columns by "Enterprise Name".
# Only 1st Vehicle and Additional Vehicle is considered in the analysis


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

# Reset the index to not introduce bugs
enterprise_subscription_data = enterprise_subscription_data.reset_index(drop=True)


# filter out the non useful columns
transaction_data = transaction_data[
    (transaction_data["Subscription Status"] != "Transient")
    & (
        (
            transaction_data["Site Internal Name"]
            == "Kellogg Square Reserved Nest (Minneapolis"
        )
        | (
            transaction_data["Site Internal Name"]
            == "Kellogg Square Garage (Minneapolis"
        )
    )
]


transaction_data = transaction_data.reset_index(drop=True)

print(f"Length of Transaction Data = {len(transaction_data)}. Transient Removed")
print(f"Length of Enterprise Subscription Data = {len(enterprise_subscription_data)}")

# A hash map to store all the users with emial
email_list: Dict[str, User] = {}

# A hash map to store all the users with ID
# Uses the licence plate as the key and the user as a value
id_list: Dict[str, User] = {}


# A hash map to store all the vehicles
plate_list: Dict[str, List[User]] = {}


def add_users(user: User, plate: str):
    """
    Functionality:
        Adds a new user to our user list if it doesn't already exists.
        If it does then only the new licence plate number is added

    Parameter:
        User: The object we are adding to the hash table
        plate: The licence plate of the user from enterprise_subscription_data
    """

    assert len(plate) == 6, "Invalid licence plate found."

    if user.email is not None:
        # The user has an email and not an ID
        # Add user to email list
        if user.email not in email_list:
            email_list[user.email] = user

        # user already in the hash map add the licence plate to set of License
        else:
            email_list[user.email].licence.add(plate)
    else:
        # The user only has an ID and not an email
        # Add user to ID list. Later looked for ID in transaction_data
        if plate not in id_list:
            id_list[plate] = user

        # user already in the id hash map
        else:
            id_list[plate].licence.add(plate)

    # Add the License Plate to the plate list
    # Used for getting duplicates
    if plate in plate_list:
        plate_list[plate].append(user)

    else:
        plate_list[plate] = [user]


# Get the users choice on wheather they want to search through the
user_input = input(
    "Do you want to search for users without registered id?\n"
    + "Type 1, Y or Yes to accept or 0, N, or No to reject.\n"
    + ">>> "
).lower()

while user_input not in ["0", "1", "yes", "no", "y", "n"]:
    print("Incorrect input try again.\n")
    user_input = input(
        "Do you want to search for users without registered id?\n"
        + "Type 0, Y or Yes to accept or 1, N, or No to reject."
    ).lower()


search_permision = True if user_input in ["1", "yes", "y"] else False

# count the number of email and id users
no_email_users = id_users = 0


# Stores the current plate for add user
current_plate: str = ""

# populate the user list by looping through enterprise data
for i in range(len(enterprise_subscription_data)):

    if pd.isna(enterprise_subscription_data.loc[i, "User Email"]):
        # if email is None

        current_plate = enterprise_subscription_data.loc[
            i, "Vehicle License Plate Text"
        ].strip()
        current_user = User(
            first=None,
            last=None,
            email=None,
            number=None,
            licence=current_plate,
            id_num=None,
        )

    else:
        # The user has a unique email
        current_plate = enterprise_subscription_data.loc[
            i, "Vehicle License Plate Text"
        ].strip()
        current_user = User(
            first=enterprise_subscription_data.loc[i, "User First Name"],
            last=enterprise_subscription_data.loc[i, "User Last Name"],
            email=enterprise_subscription_data.loc[i, "User Email"],
            number=enterprise_subscription_data.loc[i, "User Phone Number"],
            licence=current_plate,
        )

    add_users(current_user, current_plate)

print()
print(f"Email Users = {len(email_list)}")
print(f"Users with out Email = {len(id_list)}")


# Loop through the transaction data and group all the transactions by users
# Also look for the user-name, email, and number for id-users

found_users: int = 0

for i in range(len(transaction_data)):
    current_plate = transaction_data.loc[i, "Vehicle License Plate"]

    if current_plate in id_list:
        # Located the vehicles with out an email in transaction_data
        found_users += 1
        id_list[current_plate].id = transaction_data.loc[i, "User Id"]


# Writing the organized list to an excel file
# Initalize the empty DataFrame

out_excel = pd.DataFrame()

index: int = 0
# Populate the DataFrame iteratively
for current_user in email_list.values():
    out_excel.loc[index, "First"] = current_user.first
    out_excel.loc[index, "Last"] = current_user.last
    out_excel.loc[index, "Email"] = current_user.email
    out_excel.loc[index, "License"] = ", ".join(map(str, current_user.licence))
    out_excel.loc[index, "ID"] = current_user.id
    out_excel.loc[index, "Phone Number"] = current_user.number

    index += 1

for current_user in id_list.values():
    out_excel.loc[index, "First"] = current_user.first
    out_excel.loc[index, "Last"] = current_user.last
    out_excel.loc[index, "Email"] = current_user.email
    out_excel.loc[index, "License"] = ", ".join(map(str, current_user.licence))
    out_excel.loc[index, "ID"] = current_user.id
    out_excel.loc[index, "Phone Number"] = current_user.number

    index += 1


# Check if there are duplicate phone numbers or emails or user id
num_duplicate_number = 0
num_duplicate_email = 0
num_duplicate_licence = 0


index_of_duplicate_licence = []  # used to store the duplicate licence plates

# go through user list and get the numebr of duplicate phone numbers, emails, id, and licence


out_excel.to_excel(
    "~/Desktop/python_script/output/Organized Enterprise Subscription.xlsx"
)
