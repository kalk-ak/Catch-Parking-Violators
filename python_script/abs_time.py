from typing import List


def abs_time(visit_t: str, visit_d: str, leave_t: str, leave_d: str) -> List[int]:
    """Calculates an approximate absolute minute value from date and time strings.

    This function manually parses date/time strings and converts them into a
    total minute count. It is designed for a specific, consistent data format.

    Args:
        visit_t: The visit start time string (e.g., "1:30 PM").
        visit_d: The visit start date string (e.g., "6/26/2025").
        leave_t: The visit end time string.
        leave_d: The visit end date string.

    Returns:
        A list of two integers: [approx_visit_minutes, approx_leave_minutes].
    """
    # --- 1. Parse Visit Time and Date ---
    # NOTE: This logic relies on a uniform data format. It assumes dates are
    # always "M/D/YYYY" and times are "H:MM AM/PM". It will fail on any other format.
    visit_t_parts = visit_t.strip().split(" ")
    visit_time_parts = visit_t_parts[0].split(":")
    visit_hour, visit_min = int(visit_time_parts[0]), int(visit_time_parts[1])
    visit_is_pm = visit_t_parts[1].upper() == "PM"

    visit_d_parts = visit_d.strip().split("/")
    visit_month, visit_day, visit_year = (
        int(visit_d_parts[0]),
        int(visit_d_parts[1]),
        int(visit_d_parts[2]),
    )

    # --- 2. Parse Leave Time and Date ---
    leave_t_parts = leave_t.strip().split(" ")
    leave_time_parts = leave_t_parts[0].split(":")
    leave_hour, leave_min = int(leave_time_parts[0]), int(leave_time_parts[1])
    leave_is_pm = leave_t_parts[1].upper() == "PM"

    leave_d_parts = leave_d.strip().split("/")
    leave_month, leave_day, leave_year = (
        int(leave_d_parts[0]),
        int(leave_d_parts[1]),
        int(leave_d_parts[2]),
    )

    # --- 3. Convert 12-hour to 24-hour Format ---
    # Adjust hour for PM times (e.g., 1 PM becomes 13). 12 PM is a special case.
    if visit_is_pm and (visit_hour != 12):
        visit_hour += 12
    # Adjust for midnight (12 AM is hour 0 in 24-hour format).
    elif not visit_is_pm and visit_hour == 12:
        visit_hour = 0

    if leave_is_pm and (leave_hour != 12):
        leave_hour += 12
    elif not leave_is_pm and leave_hour == 12:
        leave_hour = 0

    # --- 4. Calculate Approximate Absolute Minutes ---
    # WARNING: This calculation is an approximation. It does not account for
    # the different number of days in each month or for leap years. It should
    # only be used if precision across month/year boundaries is not required.
    # in this case since this is uniformly applied across all the data it should be ok
    visit = visit_min + (visit_hour * 60) + (visit_day * 1440) + (visit_month * 44640)
    leave = leave_min + (leave_hour * 60) + (leave_day * 1440) + (leave_month * 44640)

    return [visit, leave]
