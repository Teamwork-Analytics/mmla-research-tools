import os
import subprocess

def run_diarization(folder_path, whisper_model="large-v2", device="cuda", language="en"):
    # Get all files in the specified folder
    files = os.listdir(folder_path)
    
    # Filter for audio files (you can add more extensions if needed)
    audio_extensions = ['.m4a', '.mp4', '.wav', '.ogg', '.flac']
    audio_files = [f for f in files if os.path.splitext(f)[1].lower() in audio_extensions]

    for audio_file in audio_files:
        full_path = os.path.join(folder_path, audio_file)
        
        # Construct the command
        command = f"python diarize.py -a \"{full_path}\" --whisper-model {whisper_model} --device {device} --language {language}"
        
        print(f"Processing: {audio_file}")
        
        # Execute the command using PowerShell
        try:
            result = subprocess.run(["powershell", "-Command", command], 
                                    capture_output=True, text=True, check=True)
            print(f"Output: {result.stdout}")
        except subprocess.CalledProcessError as e:
            print(f"Error processing {audio_file}: {e}")
            print(f"Error output: {e.stderr}")

# Usage
folder_path = r"C:\\Work\\Research\\tools\\peninsula-2024-students-interview-data"  # Replace with your folder path
run_diarization(folder_path)
