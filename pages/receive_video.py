import streamlit as st
import cv2
import numpy as np
import os
import tempfile
import shutil
import time
import subprocess
import mediapy as media
from pipeline.create_inputs import create_inputs
from pipeline.google_film.interpolater import Interpolator
from pipeline.image_loader import load_image

st.set_page_config(
    page_title="Skip2Smooth - Receive Video",
    layout="wide",
    initial_sidebar_state="expanded"
)

# # --- Custom Styling (Reuse) ---
# st.markdown("""
#     <style>
#     .main {
#         padding: 0rem 1rem;
#     }
#     .stButton>button {
#         width: 100%;
#         border-radius: 8px;
#         font-weight: 600;
#         transition: all 0.3s ease;
#     }
#     .success-box {
#         padding: 1rem;
#         background-color: #d4edda;
#         color: #155724;
#         border-radius: 8px;
#         margin-top: 1rem;
#     }
#     </style>
# """, unsafe_allow_html=True)

def reconstruct_video(inputs, output_path, fps=30, prog_bar=None, status_text=None):
    BATCH_SIZE = 1 # Keep low for safety on general hardware
    interpolator = Interpolator()
    final_frames_dir = "temp_reconstruction_frames"
    
    if os.path.exists(final_frames_dir):
        shutil.rmtree(final_frames_dir)
    os.makedirs(final_frames_dir, exist_ok=True)

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

            print(f"Interpolated segment {i}: added {len(mid_frames)} frames.")
        
        prog_bar.progress(i / len(inputs))

        final_frames.extend(segment_frames)

        if i == len(inputs) - 1:
            final_frames.append(frame2)

    prog_bar.empty()
    status_text.text("Stitching video...")
    
    # Use ffmpeg to stitch
    print(f'Final video created with {len(final_frames)} frames')
    media.write_video(output_path, final_frames, fps=30)
    
    shutil.rmtree(final_frames_dir)

def main():
    st.title("📥 Receiver")
    st.subheader("Reconstruct Video from Compressed Data")
    
    # --- Input Section ---
    st.divider()
    
    col1, col2 = st.columns(2)
    
    video_file = None
    indices_file = None
    
    with col1:
        st.info("Upload Compressed Video (.mp4)")
        video_upload = st.file_uploader("Compressed Video", type=['mp4'], key="vid_up")
        if video_upload:
            tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            tfile.write(video_upload.read())
            video_file = tfile.name
    
    with col2:
        st.info("Upload Indices CSV")
        csv_upload = st.file_uploader("Retained Indices", type=['csv'], key="csv_up")
        if csv_upload:
            with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="wb") as tmp:
                tmp.write(csv_upload.getbuffer())
                indices_file = tmp.name


    # --- Local Load Option ---
    if st.checkbox("Or load latest local files (Development Mode)"):
        # Attempt to find latest in output_videos and metrics
        try:
             # Basic finding logic - hardcoded for demo or list dir
             # Assuming standard paths:
             # ./output_videos and ./metrics
             pass
        except:
             st.warning("Could not auto-load files.")

    if video_file and indices_file:
         st.success("Files loaded. Ready to reconstruct.")
         
         if st.button("✨ Reconstruct Video", type="primary"):
             temp_dir = "temp_frames_receiver"
             output_video_path = "reconstructed_video.mp4"
             
             with st.spinner("Preparing segments..."):
                 print(video_file)
                 print(indices_file)
                 print(temp_dir)
                 inputs = create_inputs(indices_file, video_file, temp_dir)
                 
             st.info(f"Interpolating {len(inputs)} segments...")
             prog_bar = st.progress(0)
             status_text = st.empty()
             
             try:
                 reconstruct_video(inputs, output_video_path, prog_bar=prog_bar, status_text=status_text)
                 st.success("Reconstruction Complete!")
                 st.video(output_video_path)
                 
                 # Cleanup
                 if os.path.exists(temp_dir):
                     shutil.rmtree(temp_dir)
             except Exception as e:
                 st.error(f"Error during reconstruction: {str(e)}")

if __name__ == "__main__":
    main()