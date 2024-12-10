import datetime


def get_timestamp(sync_path: str):
    """
    for a specific sync file, read its start time data.
    :param sync_path: the path of sync.txt
    :return: the timestamp of when pozyx started
    """
    with open(sync_path) as f:
        sync_content = f.readlines()

    positioning_start_line = ""
    for line in sync_content:
        # find the line containing what we want
        if "audio start" in line and "baseline" not in line:
            positioning_start_line = line
            break  # only use the first audio start timestamp,
            # because there might be multiple start timestamp, like session 207

    time_string = positioning_start_line.split("_____")[1]
    # 01-Sep-2021_13-19-37-929 %d-%b-%Y-%H-%M-%S-%f
    date = datetime.datetime.strptime(time_string.strip() + "-+1000", "%Y-%m-%d_%H-%M-%S-%f-%z")
    timestamp = datetime.datetime.timestamp(date)
    return timestamp

