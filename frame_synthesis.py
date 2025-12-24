from interpolater import Interpolator, interpolate_recursively
import mediapy as media
import requests
import numpy as np
import tensorflow as tf

retained_indices_path = "./metrics/videoplayback2_retained_indices.csv"
compressed_video_path = "./output_videos/videoplayback2_keyframes.mp4"
temp_dir = "./temp_frames"
BATCH_SIZE = 5


interpolator = Interpolator()

inputs = create_inputs(retained_indices_path, compressed_video_path, temp_dir)

final_frames = []

print("Starting interpolation...")

for i, input_data in enumerate(inputs):
  times_to_interpolate = input_data['times_to_interpolate']
  frame1 = load_image(input_data['frame1_path'])
  frame2 = load_image(input_data['frame2_path'])

  segment_frames = [frame1]

  if times_to_interpolate > 0:
     dt_all = np.linspace(0, 1, num=times_to_interpolate + 2)[1:-1].astype(np.float32)

     for b_start in range(0, len(dt_all), BATCH_SIZE):
         b_end = min(b_start + BATCH_SIZE, len(dt_all))
         dt_chunk = dt_all[b_start:b_end]

         current_batch_size = len(dt_chunk)
         x0_batch = np.tile(frame1[np.newaxis, ...], (current_batch_size, 1, 1, 1))
         x1_batch = np.tile(frame2[np.newaxis, ...], (current_batch_size, 1, 1, 1))

         mid_frames = interpolator(x0_batch, x1_batch, dt_chunk)

         segment_frames.extend([mid_frames[j] for j in range(len(mid_frames))])

     if i % 100:
        print(f"Interpolated segment {i}: added {len(mid_frames)} frames.")

  final_frames.extend(segment_frames)

  if i == len(inputs) - 1:
      final_frames.append(frame2)


print(f'Final video created with {len(final_frames)} frames')
media.write_video('output.mp4', final_frames, fps=30)