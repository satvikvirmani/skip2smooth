import streamlit as st
import cv2
import numpy as np
import os
import tempfile
import shutil
import time
import subprocess
import mediapy as media
import logging
from pipeline.create_inputs import create_inputs
from pipeline.google_film.interpolater import Interpolator
from pipeline.image_loader import load_image
from db.retriever import retrieve_files

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Skip2Smooth - Receive Video",
    layout="wide",
    initial_sidebar_state="expanded"
)

def reconstruct_video(inputs, output_path, fps=30, progress_bar=None, status_text_elem=None):
    batch_size = 1 # Keep low for safety on general hardware
    interpolator = Interpolator()
    final_frames_dir = "temp_reconstruction_frames"
    
    if os.path.exists(final_frames_dir):
        shutil.rmtree(final_frames_dir)
    os.makedirs(final_frames_dir, exist_ok=True)

    final_frames = []

    logger.info("Starting interpolation...")

    for i, input_data in enumerate(inputs):
        times_to_interpolate = input_data['times_to_interpolate']
        frame1 = load_image(input_data['frame1_path'])
        frame2 = load_image(input_data['frame2_path'])

        segment_frames = [frame1]

        if times_to_interpolate > 0:
            dt_all = np.linspace(0, 1, num=times_to_interpolate + 2)[1:-1].astype(np.float32)

            for b_start in range(0, len(dt_all), batch_size):
                b_end = min(b_start + batch_size, len(dt_all))
                dt_chunk = dt_all[b_start:b_end]

                current_batch_size = len(dt_chunk)
                x0_batch = np.tile(frame1[np.newaxis, ...], (current_batch_size, 1, 1, 1))
                x1_batch = np.tile(frame2[np.newaxis, ...], (current_batch_size, 1, 1, 1))

                mid_frames = interpolator(x0_batch, x1_batch, dt_chunk)

                segment_frames.extend([mid_frames[j] for j in range(len(mid_frames))])

            logger.info(f"Interpolated segment {i}: added {len(mid_frames)} frames.")
        
        if progress_bar:
            progress_bar.progress(i / len(inputs))

        final_frames.extend(segment_frames)

        if i == len(inputs) - 1:
            final_frames.append(frame2)

    if progress_bar:
        progress_bar.empty()
    if status_text_elem:
        status_text_elem.text("Stitching video...")
    
    # Use ffmpeg to stitch
    logger.info(f'Final video created with {len(final_frames)} frames')
    media.write_video(output_path, final_frames, fps=30)
    
    shutil.rmtree(final_frames_dir)

def main():
    st.title("Receiver")
    st.subheader("Reconstruct Video from Compressed Data")
    
    st.divider()

    video_file_path = None
    indices_file_path = None
    temp_download_dir = "temp_downloads"

    identifier_input = st.text_input("Enter Video Identifier", help="Paste the UUID provided by the sender")
    if st.button("Retrieve Files", type="primary"):
        if identifier_input:
            with st.spinner("Retrieving files from server..."):
                retrieved = retrieve_files(identifier_input.strip(), temp_download_dir)
                if retrieved:
                    st.session_state['retrieved_video'] = retrieved['video_path']
                    st.session_state['retrieved_indices'] = retrieved['indices_path']
                    st.success("Files retrieved successfully!")
                else:
                    st.error("Failed to retrieve files. Check identifier or connection.")
        else:
            st.warning("Please enter an identifier.")
        
    if 'retrieved_video' in st.session_state and os.path.exists(st.session_state['retrieved_video']):
        video_file_path = st.session_state['retrieved_video']
        indices_file_path = st.session_state['retrieved_indices']
        st.info(f"Using retrieved files: {os.path.basename(video_file_path)}")

    if video_file_path and indices_file_path:
         st.success("Files ready. Starting reconstruction setup...")
         
         if st.button("✨ Reconstruct Video", type="primary"):
             temp_dir = "temp_frames_receiver"
             output_video_path = "reconstructed_video.mp4"
             
             with st.spinner("Preparing segments..."):
                 logger.info(f"Video file: {video_file_path}")
                 logger.info(f"Indices file: {indices_file_path}")
                 logger.info(f"Temp dir: {temp_dir}")
                 inputs = create_inputs(indices_file_path, video_file_path, temp_dir)
                 
             st.info(f"Interpolating {len(inputs)} segments...")
             progress_bar = st.progress(0)
             status_text_elem = st.empty()
             
             try:
                 reconstruct_video(inputs, output_video_path, progress_bar=progress_bar, status_text_elem=status_text_elem)
                 st.success("Reconstruction Complete!")
                 st.video(output_video_path)
                 
                 # Cleanup temp reconstruction frames
                 if os.path.exists(temp_dir):
                     shutil.rmtree(temp_dir)
             except Exception as e:
                 st.error(f"Error during reconstruction: {str(e)}")
                 logger.error(f"Error during reconstruction: {str(e)}")

             # Cleanup downloaded files if in retrieval mode (optional, maybe user wants to keep them for a bit)
             # For now, let's leave them in temp_downloads until next run or OS cleanup.

if __name__ == "__main__":
    main()