from typing import Optional, Set

import pandas as pd


class User:
    """Represents a single user, holding their personal info and parking data.

    This class encapsulates all data related to a specific car owner, including
    their contact details, registered license plates, and a history of their
    parking transactions.

    Attributes:
        first (Optional[str]): The user's first name.
        last (Optional[str]): The user's last name.
        email (Optional[str]): The user's primary email address.
        id (Optional[str]): The user's unique identification number, often
            retrieved from transaction data, especially for users without an email.
        number (Optional[int]): The user's phone number.
        license (Set[str]): A set of all license plates registered to this user.
        transactions (pd.DataFrame): A DataFrame containing all parking
            transactions associated with this user. It is initially empty.
        primary_plate (str): A placeholder for the user's main license plate,
            to be populated later if needed.
    """

    def __init__(
        self,
        first: Optional[str],
        last: Optional[str],
        email: Optional[str],
        number: Optional[int],
        license: str,
        id_num: Optional[str] = None,
    ) -> None:
        """Initializes a User object with their details."""
        self.first = first
        self.last = last
        self.email = email
        self.number = number
        self.id = id_num

        # The 'license' attribute is a set because it needs to automatically handle duplicates.
        self.license: Set[str] = {license}

        # Each user gets an empty DataFrame to store their specific transactions.
        self.transactions: pd.DataFrame = pd.DataFrame()

    def __len__(self) -> int:
        """Returns the number of license plates associated with the user."""
        return len(self.license)

    def __eq__(self, other) -> bool:
        """Defines equality for a User object.

        Compares this User object to another object. The comparison logic
        changes based on the type of the 'other' object.

        Args:
            other: An object to compare against. Can be another User instance,
                a string (email), or an integer (ID number).

        Returns:
            True if the objects are considered equal, False otherwise.
        """
        if isinstance(other, User):
            # For User-to-User comparison, email is primary, ID is fallback.
            if self.email is not None and other.email is not None:
                return self.email == other.email
            return self.id is not None and self.id == other.id

        if isinstance(other, str):
            # Allows comparing a User directly to an email string.
            return self.email == other

        if isinstance(other, int):
            # Allows comparing a User directly to an ID number.
            return self.id == other

        return False

    def __str__(self) -> str:
        """Provides a user-friendly string representation of the User."""
        if self.email is not None:
            # Display format for users identified by email.
            out = (
                f"First: {self.first}\n"
                f"Last: {self.last}\n"
                f"Email: {self.email}\n"
                f"Car Number: {len(self.license)}\n"
                "_______________________________________________ \n"
            )
        else:
            # Display format for users identified only by ID.
            out = (
                f"ID: {self.id}\n"
                f"Car Number: {len(self.license)}\n"
                "_______________________________________________ \n"
            )
        return out

    def add_license(self, license: str) -> None:
        """Adds a new, unique license plate to the user's set of plates."""
        self.license.add(license)
