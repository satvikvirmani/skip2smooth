from db.init import supabase
import os
import logging

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_file_info(identifier):
    """
    Retrieves file metadata from the database for a given identifier.
    """
    try:
        response = (
            supabase
            .table("peer_files")
            .select("*")
            .eq("identifier", identifier)
            .execute()
        )
        if response.data:
            return response.data[0]
        else:
            logger.warning(f"No entry found for identifier: {identifier}")
            return None
    except Exception as e:
        logger.error(f"Error retrieving file info: {e}")
        return None

def download_file(bucket_path, local_destination):
    """
    Downloads a file from the 'peer_files' bucket to a local destination.
    """
    try:
        with open(local_destination, 'wb') as f:
            response = supabase.storage.from_("peer_files").download(bucket_path)
            f.write(response)
        logger.info(f"Downloaded {bucket_path} to {local_destination}")
        return True
    except Exception as e:
        logger.error(f"Error downloading file {bucket_path}: {e}")
        return False

def retrieve_files(identifier, download_dir):
    """
    Retrieves metadata and downloads the associated compressed video and indices file.
    Returns a dictionary with paths to the downloaded files, or None if failed.
    """
    file_info = get_file_info(identifier)
    if not file_info:
        return None

    os.makedirs(download_dir, exist_ok=True)

    # Extract info (assuming schema matches uploader implementation)
    # The file names in the DB might just be the UUID or the full path. 
    # Based on uploader.py: 
    # video_name = video_filename (e.g. "uuid.mp4")
    # video_path = response.full_path (e.g. "peer_files/uuid.mp4") -- storage path usually doesn't include bucket in 'path' arg for download, but we'll check.
    # The `download` method of supabase-py storage usually expects the path within the bucket.
    
    video_name = file_info.get("video_name")
    indices_name = file_info.get("indices_name")

    # If the names aren't in the DB, we might try to infer them or use columns if they exist.
    # If the upload logic used `path=video_filename`, then that is the path in the bucket.
    
    if not video_name or not indices_name:
         logger.error("Database entry missing filename information.")
         return None

    local_video_path = os.path.join(download_dir, video_name)
    local_indices_path = os.path.join(download_dir, indices_name)

    # Download Video
    if not download_file(video_name, local_video_path):
        return None

    # Download Indices
    if not download_file(indices_name, local_indices_path):
        return None
        
    return {
        "video_path": local_video_path,
        "indices_path": local_indices_path
    }
