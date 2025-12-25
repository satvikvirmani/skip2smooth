import streamlit as st
import cv2
import numpy as np
import os
import tempfile
import shutil
import pandas as pd
import uuid
import logging
from pipeline.create_inputs import create_inputs
from video_compressor import KeyframeSelector
from db.uploader import upload_files

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Skip2Smooth - Send Video",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("Skip2Smooth")
    st.subheader("Send Video to the Peer")

    with st.sidebar:
        st.header("Instructions")
        st.info("1. Upload Video\n2. Compute Metrics\n3. Select Target Reduction\n4. Compress & Process")

    uploaded_file = st.file_uploader("Upload Video", type=['mp4', 'mov', 'avi'])

    # Initialize session state with snake_case keys
    if 'processed' not in st.session_state:
        st.session_state.processed = False
    if 'inputs_created' not in st.session_state:
        st.session_state.inputs_created = False
    if 'metrics_computed' not in st.session_state:
        st.session_state.metrics_computed = False
    if 'compress_ready' not in st.session_state:
        st.session_state.compress_ready = False
    if 'reductions' not in st.session_state:
        st.session_state.reductions = []
    if 'compressed_path' not in st.session_state:
        st.session_state.compressed_path = None
    if 'indices_path' not in st.session_state:
        st.session_state.indices_path = None

    if uploaded_file is not None:
        if 'video_path' not in st.session_state or st.session_state.uploaded_file_name != uploaded_file.name:
            # Create temp file with descriptive name
            temp_video_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            temp_video_file.write(uploaded_file.read())
            st.session_state.video_path = temp_video_file.name
            st.session_state.uploaded_file_name = uploaded_file.name
            st.session_state.compressed_file_name = None
            logger.info(f"Video uploaded: {uploaded_file.name}, saved to {temp_video_file.name}")

            st.session_state.processed = False
            st.session_state.metrics_computed = False
            st.session_state.compress_ready = False
            st.session_state.inputs_created = False
            st.session_state.reductions = []
        
        video_path = st.session_state.video_path
        
        video_column, details_column = st.columns(2)
        with video_column:
            st.video(video_path)
            st.caption("Original Video")

        if 'selector' not in st.session_state:
            st.session_state.selector = KeyframeSelector(video_path, verbose=False)
            
        selector = st.session_state.selector

        st.divider()
        st.header("Analysis")
        
        if not st.session_state.metrics_computed:
            if st.button("Compute Metrics", type="primary"):
                def make_callback(progress_bar, status_text_elem):
                    def callback(p, msg):
                        progress_bar.progress(p)
                        status_text_elem.text(msg)
                    return callback

                progress_bar = st.progress(0, text="Computing metrics (LPIPS, SSIM, MSE)")
                status_text_elem = st.empty()
                
                with st.spinner("Computing metrics (LPIPS, SSIM, MSE)..."):
                    logger.info("Starting metric computation...")
                    selector.compute_metrics(callback=make_callback(progress_bar, status_text_elem))
                    st.session_state.reductions = selector.set_reductions(n=200)
                    logger.info("Metric computation completed.")
                
                progress_bar.empty()
                status_text_elem.empty()
                st.session_state.metrics_computed = True
                st.rerun()

        if st.session_state.metrics_computed:
            st.text("Difference between consecutive frames")
            metrics_dataframe = pd.DataFrame(selector.metrics, columns=["MSE", "Inv SSIM", "LPIPS", "Difference"])
            st.line_chart(metrics_dataframe[["Difference"]], height=200)
            
            st.header("Compression Settings")
            
            reductions = st.session_state.reductions
            min_reduction = min(r['reduction_percent'] for r in reductions)
            max_reduction = max(r['reduction_percent'] for r in reductions)
            
            target_reduction = st.slider(
                "Target Size Reduction (%)", 
                min_value=min_reduction, 
                max_value=max_reduction, 
                value=(min_reduction + max_reduction)/2,
                format="%.1f%%"
            )
            
            best_match = min(reductions, key=lambda x: abs(x['reduction_percent'] - target_reduction))
            
            st.info(f"Paramters: Abs={best_match['abs_thres']:.2f}, Delta={best_match['delta_thres']:.2f}, Adapt={best_match['adapt_factor']:.2f}")

            if st.button("Compress Video", type="primary"):
                def make_callback(progress_bar, status_text_elem):
                    def callback(p, msg):
                        progress_bar.progress(p)
                        status_text_elem.text(msg)
                    return callback
                
                progress_bar = st.progress(0, text="Selecting keyframes and compressing video")
                status_text_elem = st.empty()
                
                # Generate unique identifier for this compression job
                identifier = str(uuid.uuid4())
                st.session_state.identifier = identifier
                logger.info(f"Started compression job with identifier: {identifier}")

                with st.spinner("Selecting keyframes and compressing..."):
                    selector.select_keyframes(
                        abs_thres=best_match['abs_thres'],
                        delta_thres=best_match['delta_thres'],
                        adapt_factor=best_match['adapt_factor']
                    )
                    
                    selector.create_retained_indices_file()
                    selector.create_compressed_video(callback=make_callback(progress_bar, status_text_elem))
                    
                    progress_bar.empty()
                    status_text_elem.empty()
                    
                    # Rename files to match identifier
                    original_compressed_path = selector.output_video
                    # Assuming default naming convention from KeyframeSelector, we'll need to robustly find it if possible
                    # but since we can't see KeyframeSelector code, we rely on selector.output_video being correct.
                    
                    # Construct expected indices path based on previous code logic
                    video_name_no_ext = os.path.splitext(os.path.basename(video_path))[0]
                    original_indices_path = os.path.join(selector.metrics_dir, f"{video_name_no_ext}_retained_indices.csv")
                    
                    new_compressed_name = f"{identifier}.mp4"
                    new_indices_name = f"{identifier}_indices.csv"
                    
                    new_compressed_path = os.path.join(os.path.dirname(original_compressed_path), new_compressed_name)
                    new_indices_path = os.path.join(os.path.dirname(original_indices_path), new_indices_name)
                    
                    # Rename
                    try:
                        os.rename(original_compressed_path, new_compressed_path)
                        logger.info(f"Renamed compressed video to {new_compressed_path}")
                    except OSError as e:
                        logger.error(f"Failed to rename compressed video: {e}")

                    if os.path.exists(original_indices_path):
                        try:
                            os.rename(original_indices_path, new_indices_path)
                            logger.info(f"Renamed indices file to {new_indices_path}")
                        except OSError as e:
                            logger.error(f"Failed to rename indices file: {e}")
                    else:
                        logger.warning(f"Indices file not found at {original_indices_path}")

                    st.session_state.compressed_path = new_compressed_path
                    st.session_state.compressed_file_name = new_compressed_name
                    st.session_state.indices_path = new_indices_path
                    st.session_state.indices_file_name = new_indices_name
                    
                    # Update selector path so get_sizes works if it checks the file
                    selector.output_video = new_compressed_path 
                    
                    orig_size, comp_size = selector.get_sizes()

                    st.session_state.orig_size = orig_size
                    st.session_state.comp_size = comp_size
                    st.session_state.reduction = (1 - (comp_size / orig_size)) * 100
                    st.session_state.processed = True
                    logger.info("Compression and processing completed.")
                    st.rerun()

        if st.session_state.processed:
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            with metric_col1:
                st.metric("Original Size", f"{st.session_state.orig_size:.2f} MB")
            with metric_col2:
                st.metric("Compressed Size", f"{st.session_state.comp_size:.2f} MB")
            with metric_col3:
                st.metric("Size Reduction", f"{st.session_state.reduction:.1f}%", delta_color="normal")

            with details_column:
                if st.session_state.compressed_path and os.path.exists(st.session_state.compressed_path):
                    st.video(st.session_state.compressed_path)
                    st.caption("Compressed Video (Keyframes Only)")
                else:
                    st.error("Output video file not found.")

            st.divider()
            st.header("Send Video to Peer")
                
            if st.button("Send", type="primary"):
                identifier = st.session_state.identifier
                with st.spinner("Sending"):
                    logger.info(f"Uploading files for identifier {identifier}")
                    try:
                        with open(st.session_state.compressed_path, "rb") as video_file, \
                             open(st.session_state.indices_path, "rb") as indices_file:
                            
                            returned_id = upload_files(
                                identifier=identifier,
                                video_file=video_file,
                                video_filename=st.session_state.compressed_file_name,
                                indices_file=indices_file,
                                indices_filename=st.session_state.indices_file_name
                            )
                        st.success("Files Sent Successfully - Copy the below string to send to peers")
                        st.info(returned_id)
                    except Exception as e:
                        st.error(f"Failed to send files: {e}")
                        logger.error(f"Upload failed: {e}")

if __name__ == "__main__":
    main()