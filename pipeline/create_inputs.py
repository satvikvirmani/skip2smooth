import cv2
import os
import csv
import shutil
import logging

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_inputs(retained_indices_path, compressed_video_path, temp_dir):
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    logger.info(f"Extracting frames from {compressed_video_path}...")
    cap = cv2.VideoCapture(compressed_video_path)
    frame_paths = []
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Save frame
        file_path = os.path.join(temp_dir, f"frame_{frame_count:04d}.png")
        cv2.imwrite(file_path, frame)
        frame_paths.append(file_path)
        frame_count += 1

    cap.release()
    logger.info(f"Extracted {len(frame_paths)} frames.")

    indices = []
    if os.path.exists(retained_indices_path):
        with open(retained_indices_path, 'r') as f:
            f.seek(0)
            reader = csv.DictReader(f)
            for row in reader:
                if row['Frame_Index']:
                    indices.append(int(row['Frame_Index']))
    else:
        logger.error(f"Error: {retained_indices_path} not found.")
        return []

    logger.info(f"Loaded {len(indices)} indices.")

    if len(indices) != len(frame_paths):
        logger.warning(f"WARNING: Mismatch between indices count ({len(indices)}) and extracted frames ({len(frame_paths)}).")

    interpolater_inputs = []
    for i in range(len(indices) - 1):
        idx_curr = indices[i]
        idx_next = indices[i+1]
        
        missing_count = idx_next - idx_curr - 1

        input_entry = {
            'frame1_path': frame_paths[i],
            'frame2_path': frame_paths[i+1],
            'times_to_interpolate': missing_count
        }
        interpolater_inputs.append(input_entry)

    active_tasks = sum(1 for x in interpolater_inputs if x['times_to_interpolate'] > 0)
    logger.info(f"Prepared {len(interpolater_inputs)} total segments, {active_tasks} of which require interpolation.")
    return interpolater_inputs