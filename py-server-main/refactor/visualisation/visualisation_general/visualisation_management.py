import pandas as pd
from dotenv import load_dotenv
from hive_data_mnagement import hive_data
from refactor.observation_data.observation_data_management import *
from refactor.visualisation.visualisation_general.pozyx_data_conversion import *
from util.file_handling_util import *
from util.video_transcode_util import transcode_video
from vad.pozyx_extraction import get_timestamp_from_sync, generate_single_file

def generate_visualization(simulation_id: str):
    """

    """
    # loading the .env file
    base_path = _config_data_save_location()
    observation_data = retrieve_observation_data(simulation_id)
    handover_finish_time, secondary_nurses_enter_time, doctor_enter_time = extract_timestamps_from_phases(
        observation_data)
    data_dir, audio_folder, raw_audio_folder, processed_audio_folder, hive_data_folder, hive_positioning_data_folder, hive_csv_output_folder, result_dir = _configure_folders(
        simulation_id, base_path)
    session = simulation_id
    process_observation_timestamps(data_dir,
                                    handover_finish_time,
                                    secondary_nurses_enter_time,
                                    doctor_enter_time)
    json_csv_output_path, raw_pozyx_data_path, sync_txt_path = _configure_paths(data_dir, result_dir, session)
    logger().info("copy sync.txt to result")
    copy_file(sync_txt_path, result_dir)
    logger().info("All data processing complete!")

    logger().info("---pozyx_json_to_csv conversion started-----")
    pozyx_json_to_csv(session, raw_pozyx_data_path, json_csv_output_path)
    logger().info("----pozyx_json_to_csv conversion finished------")

    _generate_positioning_csv_files(hive_positioning_data_folder,
                                    raw_pozyx_data_path, sync_txt_path)
    _generate_csv_files_for_hive(hive_csv_output_folder, hive_positioning_data_folder, processed_audio_folder,
                                raw_audio_folder, result_dir, session)
    logger().info("video transcoding started.")
    transcode_video(simulation_id, data_dir, result_dir)
    logger().info("video transcoding finished.")

    logger().info("generate_visualisation method ends successfully")


def _generate_csv_files_for_hive(hive_csv_output_folder, hive_positioning_data_folder, processed_audio_folder,
                                raw_audio_folder, result_dir, session):
    hive_data("RED", session, raw_audio_folder, processed_audio_folder, hive_positioning_data_folder,
              hive_csv_output_folder)
    hive_data("YELLOW", session, raw_audio_folder, processed_audio_folder, hive_positioning_data_folder,
              hive_csv_output_folder)
    hive_data("BLUE", session, raw_audio_folder, processed_audio_folder, hive_positioning_data_folder,
              hive_csv_output_folder)
    hive_data("GREEN", session, raw_audio_folder, processed_audio_folder, hive_positioning_data_folder,
              hive_csv_output_folder)
    hive_data("BLACK", session, raw_audio_folder, processed_audio_folder, hive_positioning_data_folder,
              hive_csv_output_folder)
    hive_data("WHITE", session, raw_audio_folder, processed_audio_folder, hive_positioning_data_folder,
              hive_csv_output_folder)

    df = pd.concat(map(pd.read_csv, [
        '{}/{}_RED.csv'.format(hive_csv_output_folder, session),
        '{}/{}_YELLOW.csv'.format(hive_csv_output_folder, session),
        '{}/{}_BLUE.csv'.format(hive_csv_output_folder, session),
        '{}/{}_GREEN.csv'.format(hive_csv_output_folder, session)]), ignore_index=True)
    df = df.sort_values(by='audio time')
    df.to_csv("{}/{}_all.csv".format(result_dir, session),
              sep=',', encoding='utf-8', index=False)
    logger().info("finish creating hive file.")


def _config_data_save_location() -> str:
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '.env')
    load_dotenv(dotenv_path)
    USE_ABSOLUTE_PATH = os.getenv('USE_ABSOLUTE_PATH')
    if USE_ABSOLUTE_PATH == 'false':
        BASE_PATH = "C:\\develop\\saved_data"
    else:
        BASE_PATH = os.getenv('VISUALISATION_DIR')
    logger().info(f"BASE_PATH DIRECTORY: {BASE_PATH}")
    return BASE_PATH

def _configure_folders(simulation_id: str, base_path: str):
    try:
        session = simulation_id
        data_dir = os.path.join(base_path, str(session))
        audio_folder = os.path.join(data_dir, "audio")
        raw_audio_folder = os.path.join(data_dir)
        processed_audio_folder = create_path(
            os.path.join(audio_folder, "processed_audio"))
        logger().info(f"data dir :{data_dir}")
        logger().info(f"audio_folder :{audio_folder}")
        logger().info(f"raw_audio_folder :{raw_audio_folder}")
        logger().info(f"processed_audio_folder :{processed_audio_folder}")

        hive_data_folder = create_path(
            os.path.join(data_dir, "hive_data_folder"))
        hive_positioning_data_folder = create_path(
            os.path.join(hive_data_folder, "pos"))
        hive_csv_output_folder = create_path(
            os.path.join(hive_data_folder, "result"))
        logger().info(f"hive_data_folder:{hive_data_folder}")
        logger().info(f"hive_positioning_data_folder:{hive_positioning_data_folder}")
        logger().info(f"hive_csv_output_folder:{hive_csv_output_folder}")

        result_dir = create_path(os.path.join(data_dir, "result"))
        logger().info(f"result_dir:{result_dir}")
        return data_dir, audio_folder, raw_audio_folder, processed_audio_folder, hive_data_folder, hive_positioning_data_folder, hive_csv_output_folder, result_dir

    except Exception:
        logger().exception("Failed to create folder")
        raise

def _configure_paths(data_dir, result_dir, session):
    json_csv_output_path = os.path.join(
        result_dir, "{}.csv".format(session))
    raw_pozyx_data_path = os.path.join(data_dir, "{}.json".format(session))
    sync_txt_path = os.path.join(data_dir, "sync.txt")
    logger().info(f"json_csv_output_path:{json_csv_output_path}")
    logger().info(f"raw_pozyx_data_path:{raw_pozyx_data_path}")
    logger().info(f"sync_txt_path:{sync_txt_path}")
    return json_csv_output_path, raw_pozyx_data_path, sync_txt_path


def _generate_positioning_csv_files(hive_positioning_data_folder, raw_pozyx_data_path, sync_txt_path):
    positioning_start_timestamp = get_timestamp_from_sync(
        sync_txt_path, "positioning")
    audio_start_timestamp = get_timestamp_from_sync(sync_txt_path, "audio")
    generate_single_file(raw_pozyx_path=raw_pozyx_data_path, output_folder_path=hive_positioning_data_folder,
                         audio_start_timestamp=audio_start_timestamp)
    logger().info(f"positioning_start_timestamp:{positioning_start_timestamp}")
    logger().info(f"audio_start_timestamp:{audio_start_timestamp}")
    logger().info("generating positioning csv finished")
    return positioning_start_timestamp, audio_start_timestamp



"""
send get request to localhost:5000/audio-pos
"""
if __name__ == '__main__':
    # app.run(host="0.0.0.0", port=5050, debug=False)
    # 286--> working
    generate_visualization("286")
    # test_formation_detection("225")
    # os.system("ffmpeg -i {audio_in} - ar 48000 {audio_out}")

    # stream = ffmpeg.input("test.wav")
    # audio = stream.audio
    # stream = ffmpeg.output(audio, "result.wav", **{'ar': '48000'})#, 'acodec': 'flac'})
    # ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
