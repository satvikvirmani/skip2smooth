import streamlit as st
import cv2
import numpy as np
import os
import tempfile
import shutil
import pandas as pd
from pipeline.create_inputs import create_inputs
from video_compressor import KeyframeSelector

st.set_page_config(
    page_title="Skip2Smooth - Send Video",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# # --- Custom Styling ---
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
#     .metric-card {
#         background-color: #f0f2f6;
#         padding: 1rem;
#         border-radius: 10px;
#         text-align: center;
#         box-shadow: 0 2px 4px rgba(0,0,0,0.05);
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

def main():
    st.title("🎬 Skip2Smooth")
    st.subheader("Intelligent Video Keyframe Selector & Processor")

    # --- Sidebar ---
    with st.sidebar:
        st.header("Instructions")
        st.info("1. Upload Video\n2. Compute Metrics\n3. Select Target Reduction\n4. Compress & Process")

    # --- Main Content ---
    uploaded_file = st.file_uploader("Upload Video", type=['mp4', 'mov', 'avi'])

    # Initialize Session State
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
        # Check if new file uploaded
        if 'video_path' not in st.session_state or st.session_state.uploaded_file_name != uploaded_file.name:
            tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            tfile.write(uploaded_file.read())
            st.session_state.video_path = tfile.name
            st.session_state.uploaded_file_name = uploaded_file.name
            # Reset state
            st.session_state.processed = False
            st.session_state.metrics_computed = False
            st.session_state.compress_ready = False
            st.session_state.inputs_created = False
            st.session_state.reductions = []
        
        video_path = st.session_state.video_path
        
        col1, col2 = st.columns(2)
        with col1:
            st.video(video_path)
            st.caption("Original Video")

        # Initialize Pipeline Selector in session state to persist
        if 'selector' not in st.session_state:
            st.session_state.selector = KeyframeSelector(video_path, verbose=True)
            
        selector = st.session_state.selector

        # --- Step 1: Compute Metrics ---
        st.divider()
        st.header("1. Analysis")
        
        if not st.session_state.metrics_computed:
            if st.button("📊 Compute Metrics", type="primary"):
                # Callback factory
                def make_callback(prog_bar, status_text):
                    def callback(p, msg):
                        prog_bar.progress(p)
                        status_text.text(msg)
                    return callback

                prog_bar = st.progress(0)
                status_text = st.empty()
                
                with st.spinner("Computing metrics (LPIPS, SSIM, MSE)..."):
                    metrics = selector.compute_metrics(callback=make_callback(prog_bar, status_text))
                    # Compute reduction options
                    st.session_state.reductions = selector.set_reductions(n=200)
                
                prog_bar.empty()
                status_text.empty()
                st.session_state.metrics_computed = True
                st.rerun()

        if st.session_state.metrics_computed:
            # Visualization
            df_metrics = pd.DataFrame(selector.metrics, columns=["MSE", "Inv SSIM", "LPIPS", "Difference"])
            st.line_chart(df_metrics[["Difference"]], height=200)
            
            # --- Step 2: Select Reduction ---
            st.header("2. Compression Settings")
            
            # Slider for reduction %
            reductions = st.session_state.reductions
            min_red = min(r['reduction_percent'] for r in reductions)
            max_red = max(r['reduction_percent'] for r in reductions)
            
            target_red = st.slider(
                "Target Size Reduction (%)", 
                min_value=min_red, 
                max_value=max_red, 
                value=(min_red + max_red)/2,
                format="%.1f%%"
            )
            
            # Find closest matching reduction setting
            best_match = min(reductions, key=lambda x: abs(x['reduction_percent'] - target_red))
            
            st.info(f"Paramters: Abs={best_match['abs_thres']:.2f}, Delta={best_match['delta_thres']:.2f}, Adapt={best_match['adapt_factor']:.2f}")

            if st.button("🚀 Compress Video", type="primary"):
                 # Callback factory
                def make_callback(prog_bar, status_text):
                    def callback(p, msg):
                        prog_bar.progress(p)
                        status_text.text(msg)
                    return callback
                
                prog_bar = st.progress(0)
                status_text = st.empty()
                
                with st.spinner("Selecting keyframes and compressing..."):
                    # Use selected parameters
                    selector.select_keyframes(
                        abs_thres=best_match['abs_thres'],
                        delta_thres=best_match['delta_thres'],
                        adapt_factor=best_match['adapt_factor']
                    )
                    
                    selector.create_retained_indices_file()
                    selector.create_compressed_video(callback=make_callback(prog_bar, status_text))
                    
                    prog_bar.empty()
                    status_text.empty()
                    
                    # Update paths
                    st.session_state.compressed_path = selector.output_video
                    video_name = os.path.splitext(os.path.basename(video_path))[0]
                    st.session_state.indices_path = os.path.join(selector.metrics_dir, f"{video_name}_retained_indices.csv")
                    
                    # Stats
                    orig_size, comp_size = selector.get_sizes()
                    st.session_state.orig_size = orig_size
                    st.session_state.comp_size = comp_size
                    st.session_state.reduction = (1 - (comp_size / orig_size)) * 100
                    st.session_state.processed = True
                    st.rerun()

        # Display Results if processed
        if st.session_state.processed:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Original Size", f"{st.session_state.orig_size:.2f} MB")
            with c2:
                st.metric("Compressed Size", f"{st.session_state.comp_size:.2f} MB")
            with c3:
                st.metric("Size Reduction", f"{st.session_state.reduction:.1f}%", delta_color="normal")

            with col2:
                if st.session_state.compressed_path and os.path.exists(st.session_state.compressed_path):
                    st.video(st.session_state.compressed_path)
                    st.caption("Compressed Video (Keyframes Only)")
                else:
                    st.error("Output video file not found.")

            # --- Step 2: Create Inputs ---
            st.divider()
            st.header("2. Model Inputs")
            
            if st.button("🛠 Create Model Inputs"):
                temp_dir = "temp_frames_app"
                with st.spinner("Extracting frames and preparing segments..."):
                    inputs = create_inputs(
                        st.session_state.indices_path, 
                        st.session_state.compressed_path, 
                        temp_dir
                    )
                    st.session_state.inputs_created = True
                    st.session_state.num_segments = len(inputs)
                    active_tasks = sum(1 for x in inputs if x['times_to_interpolate'] > 0)
                    st.session_state.active_tasks = active_tasks
                
                st.success(f"Inputs Created! Prepared {len(inputs)} segments.")
                
            if st.session_state.inputs_created:
                st.info(f"Ready to interpolate {st.session_state.active_tasks} gaps in {st.session_state.num_segments} total segments.")

                # --- Step 3: Send to Model ---
                st.divider()
                st.header("3. Run Inference")
                
                if st.button("✨ Send to Model (Dummy)"):
                    with st.spinner("Sending data to model API..."):
                        import time
                        time.sleep(1.5) 
                    st.balloons()
                    st.markdown("""
                        <div class="success-box">
                            <h3>✅ Sent Successfully!</h3>
                            <p>The video segments have been queued for frame interpolation.</p>
                        </div>
                    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()