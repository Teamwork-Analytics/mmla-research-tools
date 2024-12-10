from typing import Any, Mapping

from util.db_connect_util import *
from refactor.pozyx_data.pozyx_data_management import get_timestamp


def retrieve_observation_data(simulation_id: str) -> Mapping[str, Any]:
    db = connect_to_mongodb_cluster()
    simulation_data = get_collection(db, "simulations").find_one({{"simulationId": simulation_id}})
    if simulation_data is None:
        raise ValueError(f"could not find any simulation with simulationId : {simulation_id}")
    observation_data = get_collection(db, "observations").find_one(
        {"_id": simulation_data["observation"]})
    if observation_data is None:
        raise ValueError(f"could not find any observations on  simulation with simulation_id : {simulation_id}")
    return observation_data


def extract_timestamps_from_phases(observation_data: Mapping[str, Any], database_config_year: int) -> tuple[
    float, float, float]:
    handover_finish_time = None
    secondary_nurses_enter_time = None
    doctor_enter_time = None

    for item in observation_data["phases"]:
        if item["phaseKey"] == "handover_ends":
            handover_finish_time = item["timestamp"].timestamp()
        elif item["phaseKey"] == "secondary_nurse_enters":
            secondary_nurses_enter_time = item["timestamp"].timestamp()
        elif item["phaseKey"] == "doctor_enters":
            doctor_enter_time = item["timestamp"].timestamp()
        elif item["phaseKey"] == "bed_4":
            pass

    if handover_finish_time is None:
        raise ValueError("Phase key 'handover_ends' is missing.")
    if secondary_nurses_enter_time is None:
        raise ValueError("Phase key 'secondary_nurse_enters' is missing.")
    if doctor_enter_time is None:
        raise ValueError("Phase key 'doctor_enters' is missing.")

    logger().info(f"handover_finish_time: {handover_finish_time}")
    logger().info(f"secondary_nurses_enter_time: {secondary_nurses_enter_time}")
    logger().info(f"doctor_enter_time: {doctor_enter_time}")
    return handover_finish_time, secondary_nurses_enter_time, doctor_enter_time


def extract_timestamps_from_phases_based_on_year(observation_data: Mapping[str, Any], database_config_year: int) -> \
        tuple[float, float, float]:
    handover_finish_time = None
    secondary_nurses_enter_time = None
    doctor_enter_time = None

    if database_config_year == 2022:
        for item in observation_data["phases"]:
            if item["phaseKey"] == "handover":
                handover_finish_time = item[
                    "timestamp"].timestamp()
            elif item["phaseKey"] == "ward_nurse":
                secondary_nurses_enter_time = item[
                    "timestamp"].timestamp()
            elif item["phaseKey"] == "met_doctor":
                doctor_enter_time = item[
                    "timestamp"].timestamp()
            elif item["phaseKey"] == "bed_4":
                pass
    elif database_config_year == 2023:
        for item in observation_data["phases"]:
            if item["phaseKey"] == "handover_ends":
                handover_finish_time = item[
                    "timestamp"].timestamp()
            elif item["phaseKey"] == "secondary_nurse_enters":
                secondary_nurses_enter_time = item[
                    "timestamp"].timestamp()
            elif item["phaseKey"] == "doctor_enters":
                doctor_enter_time = item[
                    "timestamp"].timestamp()
            elif item["phaseKey"] == "bed_4":
                pass
    else:
        raise ValueError(
            "Please enter a valid DATABASE_CONFIGURATION value. Current value: {}. Use the value provided in the list".format(
                database_config_year))

    if handover_finish_time is None:
        raise ValueError("Phase key for  'handover' is missing.")
    if secondary_nurses_enter_time is None:
        raise ValueError("Phase key 'secondary' is missing.")
    if doctor_enter_time is None:
        raise ValueError("Phase key 'doctor' is missing.")

    logger().info(f"handover_finish_time: {handover_finish_time}")
    logger().info(f"secondary_nurses_enter_time: {secondary_nurses_enter_time}")
    logger().info(f"doctor_enter_time: {doctor_enter_time}")
    return handover_finish_time, secondary_nurses_enter_time, doctor_enter_time


def process_observation_timestamps(data_dir, doctor_enter_time, handover_finish_time, secondary_nurses_enter_time):
    audio_start_timestamp = get_timestamp(os.path.join(data_dir, "sync.txt"))
    handover_finish_time -= audio_start_timestamp
    secondary_nurses_enter_time -= audio_start_timestamp
    doctor_enter_time -= audio_start_timestamp
    logger().info(f"audio_start_timestamp:{audio_start_timestamp}")
    logger().info(f"handover_finish_time:{handover_finish_time}")
    logger().info(f"secondary_nurses_enter_time:{secondary_nurses_enter_time}")
    logger().info(f"doctor_enter_time:{doctor_enter_time}")
    return handover_finish_time, secondary_nurses_enter_time, doctor_enter_time
