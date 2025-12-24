from video_compressor import KeyframeSelector

VIDEO_FILE = "./data/videoplayback2.mp4"

keyframe_selector = KeyframeSelector(VIDEO_FILE, verbose=True)
keyframe_selector.compute_metrics()
keyframe_selector.select_keyframes(abs_thres=18.0, delta_thres=2.0)
keyframe_selector.create_retained_indices_file()
keyframe_selector.create_compressed_video()
keyframe_selector.get_sizes()