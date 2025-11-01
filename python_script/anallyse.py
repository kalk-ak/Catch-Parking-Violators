import os

import pandas as pd

path_of_read: str = os.getcwd() + "/data/"
path_of_write: str = os.getcwd() + "/test_output/"


class User:
    """
     Organize the users (Car Owners) into class

    User Class has the following attributes

         first (str): The first Name of the user
         last (str): The last Name of the user
         email (str): The email address of the user
         number (int): The phone number of the user
         licence (list): The licence plate of the car
         Id (int): The identificatiion number of the user. Initially set to None - only filled if the user has no email in the enterprise  subscription data

         Filled late >>>

         licence_status (list): The status of each licence. Filled after the licence plate list is populated. (Subscription Added or Subscription Removed)
         licence_type: (list): The type of each licence. Filled after the licence plate list is populated. (First, Additional, Other)
         first_only_licence (list): List of the first vehicles. (Used to calculate the max transaction)
         additional_only_licence (list): List of the additional vehicles. (Used to calculate the max transaction)
         other_licence: List of cars that are neither first or additional
    """

    def __init__(
        self, first: str, last: str, email: str, number: int, licence: str, id=None
    ) -> None:
        """
        Initalize all the variables
        """
        self.first = first
        self.last = last
        self.email = email
        self.number = number
        self.licence = []
        self.licence.append(licence)
        self.licence_status = []
        self.licence_type = []

        self.first_only_licence = []
        self.additional_only_licence = []
        self.other_licence = []

        self.first_licence = None
        self.additional_licence = None

        # Initially the user ID is set to None and only changed if the user doesn't have a first name or last name
        self.id = id

        assert (self.email == None) ^ (self.id == None)
        # Populated later on from the data. Initially set to empty string

    def __len__(self):
        return len(license)

    def __eq__(self, other):
        """
        Parameter other can be int (ID number), string (email), or another user
        """
        if isinstance(other, User):
            if self.email != None:
                return self.email == other.email

            else:
                return self.id == other.id

        elif isinstance(other, str):
            return self.email == other

        elif isinstance(other, int):
            return self.id == other

        return False

    def has_first(self):
        return self.first_vehicle != ""

    def has_additional(self):
        return self.additional_vehicle != ""

    def add_licence(self, license_str):
        self.licence.append(license_str)

    def __str__(self):
        if self.id == None:
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


# Get the current script's directory
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory
parent_dir = os.path.dirname(current_dir)


# Reads all the datas to a data Frame

transaction_data = pd.read_csv(
    path_of_read + "transaction_data.csv", encoding="UTF-16", low_memory=False
)
enterprise_subscription_data = pd.read_csv(
    path_of_read + "enterprise_subscription_detail.csv", encoding="UTF-16"
)

# Filter the columns by "Enterprise Name". Only 1st Vehicle and Additional Vehicle is considered in the analysis
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
enterprise_subscription_data = enterprise_subscription_data.reset_index(drop=True)

# Filter out the transient data
transaction_data = transaction_data[
    transaction_data["Subscription Status"] != "Transient"
]
transaction_data = transaction_data.reset_index(drop=True)

# Filter out the non useful columns
transaction_data = transaction_data[
    (
        transaction_data["Site Internal Name"]
        == "Kellogg Square Reserved Nest (Minneapolis"
    )
    | (transaction_data["Site Internal Name"] == "Kellogg Square Garage (Minneapolis")
]
transaction_data = transaction_data.reset_index(drop=True)

print(f"Length of Transaction Data = {len(transaction_data)}. Transient Removed")
print(f"Length of Enterprise Subscription Data = {len(enterprise_subscription_data)}")


def add_user(user_list, this_user) -> int:
    """
    Functionality:
        Adds a new user to our user list if it doesn't already exists. If it does then only the new licence plate number is added

    Parameter:
        user_list: The list of users we have
        this_user: The current user to be added.

    Return Value:
        1: if a new user is added to the list
        0: if a new licence plate is added but the user already exists
        -1: The user exists and the licence plate is already added
    """
    licence_plate = this_user.licence[
        0
    ]  # There is only 1 licece plate and it is indexed in the first position

    if this_user.email != None:  # The user has an email and not an Id
        for current_user in user_list:
            # if the user is already in the list only the licence plate number is added
            if current_user == this_user:
                # only add the licence plate if it is not already added
                if licence_plate in current_user.licence:
                    return -1

                current_user.add_licence(licence_plate)
                return 0

        user_list.append(this_user)
        return 1

    else:  # This user has no email rather has an ID
        for current_user in user_list:
            # if the user is already in the list only the licence plate number is added
            if current_user.id == this_user.id:
                # only add the licence plate if it is not already added
                if licence_plate in current_user.licence:
                    return -1

                current_user.add_licence(licence_plate)
                return 0

        user_list.append(this_user)
        return 1


# Populate our user list: A list of all the users
user_list = []

# Used to track the number of users with and without email
no_email_users = 0
id_users = 0

# Populate the user list by looping through enterprise data
# if there is a user without an email their User Id is searched through transaction data and added if found
for i in range(len(enterprise_subscription_data)):
    if pd.isna(enterprise_subscription_data["User Email"][i]):  # If email cell is None
        # search through transient data for the user ID because the user didn't input their first and last name
        no_email_users += 1

        for index in range(len(transaction_data)):
            if (
                transaction_data["Vehicle License Plate"][index]
                == enterprise_subscription_data["Vehicle License Plate Text"][i]
            ):
                current_user = User(
                    first=enterprise_subscription_data["User First Name"][i],
                    last=enterprise_subscription_data["User Last Name"][i],
                    email=None,
                    number=enterprise_subscription_data["User Phone Number"][i],
                    licence=enterprise_subscription_data["Vehicle License Plate Text"][
                        i
                    ].strip(),
                    id=transaction_data["User Id"][index],
                )
                id_users += 1
                break

    else:  # The user has a unique email so no need for an id number
        current_user = User(
            first=enterprise_subscription_data["User First Name"][i],
            last=enterprise_subscription_data["User Last Name"][i],
            email=enterprise_subscription_data["User Email"][i].strip(),
            number=enterprise_subscription_data["User Phone Number"][i],
            licence=enterprise_subscription_data["Vehicle License Plate Text"][
                i
            ].strip(),
        )

    add_user(user_list, current_user)


print()
print(f"Length of users = {len(user_list)}")
print(f"No email users = {no_email_users}")
print(
    f"Unknown User (no email or ID number) - not in the excel  = {no_email_users - id_users}"
)


# Writing the organized list to an excel file
# Initialize an empty DataFrame
out_excel = pd.DataFrame(
    columns=[
        "First",
        "Last",
        "Email",
        "License",
        "ID",
        "Phone Number",
        "Duplicate License Plate",
    ]
)

# Populate the DataFrame iteratively
for i in range(len(user_list)):
    out_excel.loc[i, "First"] = user_list[i].first
    out_excel.loc[i, "Last"] = user_list[i].last
    out_excel.loc[i, "Email"] = user_list[i].email
    out_excel.loc[i, "License"] = ", ".join(map(str, user_list[i].licence))
    out_excel.loc[i, "ID"] = user_list[i].id
    out_excel.loc[i, "Phone Number"] = user_list[i].number


# Check if there are duplicate phone numbers or emails or user id
num_duplicate_number = 0
num_duplicate_email = 0
num_duplicate_licence = 0


index_of_duplicate_licence = []  # used to store the duplicate licence plates

# go through user list and get the numebr of duplicate phone numbers, emails, id, and licence
for i in range(len(user_list)):
    for j in range(i + 1, len(user_list)):
        if user_list[i].number == user_list[j].number:  # get the duplicate phone number
            num_duplicate_number += 1

        if (user_list[i].email != None) and (
            user_list[i].email == user_list[j].email
        ):  # Get the duplicate email
            num_duplicate_email += 1

        # check the number of duplicate licece and adds the index
        for k in range(len(user_list[i].licence)):
            if user_list[i].licence[k] in user_list[j].licence:
                num_duplicate_licence += 1
                index_of_duplicate_licence.append((i, j))
                out_excel.loc[i, "Duplicate License Plate"] = f"Duplicate {j}"
                out_excel.loc[j, "Duplicate License Plate"] = f"Duplicate {i}"


out_excel.to_excel(path_of_write + "Before: Organized Enterprise Subscription.xlsx")
print()
print(
    f"There are {num_duplicate_email} duplicate Email\nThere are {num_duplicate_number} duplicate Phone Number\nThere are {num_duplicate_licence} duplicate Licence Plate"
)

# Print the index of the duplicate license
if num_duplicate_licence > 0:
    print("\033[37m................\033[0m")  # White color for dots

    for pair in index_of_duplicate_licence:
        print(
            f"There is a duplicate license in index >>> \033[31m{pair[0]}, {pair[1]}\033[0m"
        )  # Red color for indices

    print("\033[37m................\033[0m")  # White color for dots


# Populate the licence types and the subscription status for each user
for user in user_list:
    # populated with none with the length of the user licence plates
    user.licence_status = [None for i in range(len(user.licence))]
    user.licence_type = [None for i in range(len(user.licence))]
    if user.email != None:
        for i in range(len(user.licence)):
            license_plate = user.licence[i]
            for j in range(len(enterprise_subscription_data)):
                current_email = enterprise_subscription_data["User Email"][j]
                current_plate = enterprise_subscription_data[
                    "Vehicle License Plate Text"
                ][j]

                if (current_email == user.email) and (current_plate == license_plate):
                    # get the information for the licence plate and subscription status
                    current_plate = enterprise_subscription_data[
                        "Vehicle License Plate Text"
                    ][j]
                    current_status = enterprise_subscription_data[
                        "Current Status (description)"
                    ][j]
                    licence_type = enterprise_subscription_data["Enterprise Name"][j]

                    licence_type = (
                        "First"
                        if licence_type == "Kellogg Square Residents - 1 st Vehicle"
                        else "Additional"
                    )

                    user.licence_status[i] = current_status
                    user.licence_type[i] = licence_type
"""
            else: 
                if (current_email == None) and (current_plate == license_plate):
                    # get the infromation for the licence plate
                    current_plate = enterprise_subscription_data["Vehicle License Plate Text"][j]
                    current_status = enterprise_subscription_data["Current Status (description)"][j]
                    licence_type = enterprise_subscription_data["Enterprise Name"][j]

                    licence_type = "First" if licence_type == "Kellogg Square Residents - 1 st Vehicle" else "Additional"

                    user.licence_status[i] = current_status
                    user.licence_type[i] = licence_type
"""

# Assert that the licence status is correctly filled and their isn't any Null Value
for user in user_list:
    if user.email != None:
        for i in range(len(user.licence)):
            assert user.licence_status[i] != None
            assert user.licence_type[i] != None


# Writing the organized list to an excel file
# Initialize an empty DataFrame
out_excel = pd.DataFrame(
    columns=[
        "First",
        "Last",
        "Email",
        "License",
        "ID",
        "Phone Number",
        "License Status",
        "License Type",
    ]
)

# Populate the DataFrame iteratively
for i in range(len(user_list)):
    out_excel.loc[i, "First"] = user_list[i].first
    out_excel.loc[i, "Last"] = user_list[i].last
    out_excel.loc[i, "Email"] = user_list[i].email
    out_excel.loc[i, "License"] = ", ".join(map(str, user_list[i].licence))
    out_excel.loc[i, "ID"] = user_list[i].id
    out_excel.loc[i, "Phone Number"] = user_list[i].number
    out_excel.loc[i, "License Status"] = ", ".join(
        map(str, user_list[i].licence_status)
    )
    out_excel.loc[i, "License Type"] = ", ".join(map(str, user_list[i].licence_type))

out_excel.to_excel(path_of_write + "Before: Licence Status.xlsx")


# Organize each licence plate as first, Additional or other
for user in user_list:
    for i in range(len(user.licence)):
        licence_type = user.licence_type[i]

        if licence_type == "Additional":
            user.additional_only_licence.append(user.licence[i])

        elif licence_type == "First":
            user.first_only_licence.append(user.licence[i])

        else:
            user.other_licence.append(user.licence[i])


# Flags all the cars that violated the first vehicle and additional vehicle policy
for user in user_list:
    if user.email != None:  # Handles the case for users with email
        # Flags all the extra first vehicle
        first_transaction_frequency = [
            0 for i in range(len(user.first_only_licence))
        ]  # Populates the frequency list for all the
        for i in range(len(user.first_only_licence)):
            licence_plate = user.first_only_licence[i]
            for index in range(len(transaction_data)):
                transaction_licence = transaction_data["Vehicle License Plate"][index]
                if licence_plate == transaction_licence:
                    first_transaction_frequency[i] += 1

        # Flaggs all the additional vehicle
        additional_transaction_frequency = [
            0 for i in range(len(user.additional_only_licence))
        ]

        for i in range(len(user.additional_only_licence)):
            licence_plate = user.additional_only_licence[i]
            for index in range(len(transaction_data)):
                transaction_licence = transaction_data["Vehicle License Plate"][index]
                if licence_plate == transaction_licence:
                    additional_transaction_frequency[i] += 1

        if (len(first_transaction_frequency)) != 0:
            maximum_frequency = max(first_transaction_frequency)
            max_index = first_transaction_frequency.index(maximum_frequency)
            user.first_licence = user.first_only_licence[max_index]

        if len(additional_transaction_frequency) != 0:
            maximum_frequency = max(additional_transaction_frequency)
            max_index = additional_transaction_frequency.index(maximum_frequency)
            user.additional_licence = user.additional_only_licence[max_index]


# ouputs the flag status as an excel flag
# The car is flagged if it a psudo first vehicle is used in a transaction
output = pd.DataFrame(
    columns=[
        "Email",
        "Visit Start Date",
        "Visit Start Time",
        "Visit End Date",
        "Visit Exit Time",
        "Visit Duration (minutes)",
        "License Plate",
        "User Id",
        "Flagged",
        "No First",
        "Total",
    ]
)
for user in user_list:
    total: int = 0  # Used to calclulate the total duration length
    if user.email != None:  # handles the case for only users with email
        for i in range(len(user.licence)):
            licence_plate = user.licence[
                i
            ]  # Used to find the licence vehicle in transaction

            flag = None
            first_flag = "No first"

            # Traverses the whole transaction data
            for index in range(len(transaction_data)):
                transaction_licence = transaction_data["Vehicle License Plate"][index]

                if licence_plate == transaction_licence:
                    visit_start_date = transaction_data["Visit Start Date (local)"][
                        index
                    ]
                    visit_start_time = transaction_data["Visit Start Time (local)"][
                        index
                    ]
                    visit_end_date = transaction_data["Visit End Date (local)"][index]
                    visit_end_time = transaction_data["Visit Start Time (local)"][index]
                    visit_duration = transaction_data["Visit Duration (minutes)"][index]
                    user_id = transaction_data["User Id"][index]

                    if (licence_plate != user.first_licence) and (
                        licence_plate != user.additional_licence
                    ):
                        flag = "Flagged"
                        total += float(visit_duration)

                    if len(user.first_only_licence) > 0:
                        first_flag = None

                    output.loc[len(output)] = [
                        user.email,
                        visit_start_date,
                        visit_start_time,
                        visit_end_date,
                        visit_end_time,
                        visit_duration,
                        licence_plate,
                        user_id,
                        flag,
                        first_flag,
                        total,
                    ]


# Post-process to replace duplicate emails with None
output["Email"] = output["Email"].mask(output["Email"].duplicated(), None)

output.to_excel(path_of_write + "Before: Final report.xlsx")

