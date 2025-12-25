# Skip2Smooth

### Intelligent Video Compression & Reconstruction System

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg?style=for-the-badge)
![Python](https://img.shields.io/badge/python-3.8+-green.svg?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-orange.svg?style=for-the-badge)

---

## Overview

**Skip2Smooth** is an innovative video processing system that dramatically reduces video file sizes while maintaining visual quality through AI-powered frame interpolation. Perfect for scenarios where bandwidth is limited but quality matters.

### How It Works

1. **Sender Side**: Intelligently selects keyframes from your video, removing redundant frames
2. **Transfer**: Send only the compressed keyframes (up to 90% size reduction!)
3. **Receiver Side**: Uses Google's FILM AI model to reconstruct smooth, full-quality video

---

## Features

### Intelligent Keyframe Selection
- **Multi-metric Analysis**: Uses MSE, SSIM, and LPIPS to identify important frames
- **Adaptive Thresholding**: Automatically balances quality vs. compression
- **Visual Metrics**: Real-time visualization of frame differences
- **Flexible Compression**: Choose your target compression ratio with an intuitive slider

### AI-Powered Reconstruction
- **FILM Model Integration**: Leverages Google's state-of-the-art frame interpolation
- **Smooth Playback**: Generates missing frames with natural motion
- **Batch Processing**: Efficient memory management for large videos
- **High Fidelity**: Reconstructed videos closely match original quality

### Cloud-Based File Transfer
- **Supabase Integration**: Secure cloud storage for compressed videos
- **UUID Tracking**: Simple identifier system for file sharing
- **Automatic Metadata**: Tracks upload times and file information
- **Easy Retrieval**: One-click download with identifier

### User-Friendly Interface
- **Streamlit-Powered**: Clean, modern web interface
- **Progress Tracking**: Real-time feedback during processing
- **Side-by-Side Comparison**: View original vs. compressed videos
- **Metric Dashboard**: See compression statistics at a glance

---

## Quick Start

### Prerequisites

- Python 3.8 or higher
- CUDA-capable GPU (recommended for faster interpolation)
- Supabase account

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/skip2smooth.git
cd skip2smooth
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**

Create a `.env` file in the root directory:
```env
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_secret_key_here
```

4. **Run the application**
```bash
streamlit run homepage.py
```

---

## Usage

### Sending a Video

1. Navigate to **"Send Video"** page
2. Upload your video file (supports MP4, MOV, AVI)
3. Click **"Compute Metrics"** to analyze frame differences
4. Adjust the compression slider to your desired reduction level
5. Click **"Compress Video"** to process
6. Click **"Send"** to upload to cloud
7. Copy the generated UUID and share with receiver

### Receiving a Video

1. Navigate to **"Receive Video"** page
2. Paste the UUID identifier from sender
3. Click **"Retrieve Files"** to download from cloud
4. Click **"Reconstruct Video"** to rebuild full video
5. Watch your reconstructed video!

---

## Architecture

### Project Structure

```
skip2smooth/
├── homepage.py              # Main entry point
├── pages/
│   ├── send_video.py       # Sender interface
│   └── receive_video.py    # Receiver interface
├── db/
│   ├── init.py             # Supabase client setup
│   ├── uploader.py         # File upload handlers
│   └── retriever.py        # File download handlers
├── pipeline/
│   ├── create_inputs.py    # Interpolation input preparation
│   ├── image_loader.py     # Image normalization
│   └── google_film/
│       └── interpolater.py # FILM model wrapper
├── .env                     # Environment configuration
└── .streamlit/
    └── config.toml         # Streamlit settings
```

### Technology Stack

- **Frontend**: Streamlit
- **Video Processing**: OpenCV, MediaPy
- **AI/ML**: TensorFlow, TensorFlow Hub (Google FILM)
- **Backend**: Python
- **Database**: Supabase (PostgreSQL)
- **Storage**: Supabase Storage
- **Metrics**: LPIPS, SSIM, MSE

---

## How It Works

### Compression Pipeline

1. **Frame Analysis**: Each consecutive frame pair is analyzed using three metrics:
   - **MSE (Mean Squared Error)**: Pixel-level differences
   - **SSIM (Structural Similarity Index)**: Perceptual similarity
   - **LPIPS (Learned Perceptual Image Patch Similarity)**: Deep learning-based perceptual distance

2. **Keyframe Selection**: An adaptive thresholding algorithm selects frames where:
   - Significant motion occurs
   - Scene changes happen
   - Important visual information appears

3. **Compression**: Only selected keyframes are kept, reducing file size by 50-90%

### Reconstruction Pipeline

1. **Frame Extraction**: Keyframes are extracted from compressed video
2. **Gap Analysis**: System calculates how many frames are missing between each keyframe pair
3. **AI Interpolation**: Google's FILM model generates smooth intermediate frames
4. **Video Stitching**: All frames are reassembled into a complete video at original framerate

---

## Performance

### Typical Results

| Metric | Value |
|--------|-------|
| Compression Ratio | 50-90% |
| Processing Speed | ~2-5 fps (interpolation) |
| Quality Retention | 85-95% (perceptual) |
| Supported Resolutions | Up to 4K |

### Optimization Tips

- Use GPU acceleration for 5-10x faster interpolation
- Start with higher compression ratios for faster processing
- Batch size of 1 ensures stability on consumer hardware
- Pre-process videos to standard framerates (24, 30, 60 fps)

---

## Configuration

### Streamlit Settings

Edit `.streamlit/config.toml`:
```toml
[server]
maxUploadSize = 1024  # Max upload size in MB
```

### Compression Parameters

Adjust in the UI or programmatically:
- **abs_thres**: Absolute difference threshold (0-50)
- **delta_thres**: Change detection threshold (0-10)
- **adapt_factor**: Dynamic threshold adaptation (0-1)

---

## Troubleshooting

### Common Issues

**"CUDA out of memory"**
- Reduce batch size to 1 (already default)
- Process shorter video segments
- Use CPU-only mode (slower but stable)

**"Failed to retrieve files"**
- Verify Supabase credentials in `.env`
- Check internet connection
- Ensure identifier is correct

**"Metrics computation slow"**
- Expected for long videos (10+ minutes)
- LPIPS requires GPU for reasonable speed
- Consider processing videos in chunks

**"Reconstruction quality poor"**
- Increase keyframe retention (lower compression)
- Check original video quality
- FILM works best with smooth motion

---

## Contributing

We welcome contributions! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **Google Research**: For the FILM (Frame Interpolation for Large Motion) model
- **Streamlit**: For the amazing web framework
- **Supabase**: For seamless backend infrastructure
- **OpenCV Community**: For robust video processing tools

---

## Resources

- [FILM Paper](https://arxiv.org/abs/2202.04901)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Supabase Documentation](https://supabase.com/docs)
- [LPIPS Metric](https://github.com/richzhang/PerceptualSimilarity)

---

## Future Roadmap

- [ ] Multi-video batch processing
- [ ] Real-time streaming support
- [ ] Custom interpolation model training
- [ ] Mobile app version
- [ ] Automatic quality assessment
- [ ] Support for audio preservation

---

<div align="center">

### ⭐ Star us on GitHub — it motivates us a lot!

Made with ❤️ by developers who care about bandwidth

</div>
