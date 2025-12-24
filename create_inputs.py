import cv2
import os
import csv
import shutil

def create_inputs(retained_indices_path, compressed_video_path, temp_dir):
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    print(f"Extracting frames from {compressed_video_path}...")
    cap = cv2.VideoCapture(compressed_video_path)
    frame_paths = []
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Save frame
        file_path = os.path.join(temp_dir, f"frame_{frame_count:04d}.png")
        frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        cv2.imwrite(file_path, frame)
        frame_paths.append(file_path)
        frame_count += 1

    cap.release()
    print(f"Extracted {len(frame_paths)} frames.")

    indices = []
    if os.path.exists(retained_indices_path):
        with open(retained_indices_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Frame_Index']:
                    indices.append(int(row['Frame_Index']))
    else:
        print(f"Error: {retained_indices_path} not found.")
        return []

    print(f"Loaded {len(indices)} indices.")

    if len(indices) != len(frame_paths):
        print(f"WARNING: Mismatch between indices count ({len(indices)}) and extracted frames ({len(frame_paths)}).")

    interpolater_inputs = []
    for i in range(len(indices) - 1):
        idx_curr = indices[i]
        idx_next = indices[i+1]
        
        missing_count = idx_next - idx_curr - 1

        INPUT_ENTRY = {
            'frame1_path': frame_paths[i],
            'frame2_path': frame_paths[i+1],
            'times_to_interpolate': missing_count
        }
        interpolater_inputs.append(INPUT_ENTRY)

    active_tasks = sum(1 for x in interpolater_inputs if x['times_to_interpolate'] > 0)
    print(f"Prepared {len(interpolater_inputs)} total segments, {active_tasks} of which require interpolation.")
    return interpolater_inputs