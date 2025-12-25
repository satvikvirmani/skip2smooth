from db.init import supabase
import uuid
from datetime import datetime, UTC
import logging

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upload_files(identifier, video_file, video_filename, indices_file, indices_filename):
    """
    Uploads compressed video and indices file to storage and creates a database entry.
    """
    try:
        # Upload Video
        video_response = (
            supabase.storage
            .from_("peer_files")
            .upload(
                file=video_file,
                path=video_filename,
                file_options={"cache-control": "3600", "upsert": "false"}
            )
        )
        logger.info(f"Video uploaded successfully: {video_filename}")

        # Upload Indices
        indices_response = (
            supabase.storage
            .from_("peer_files")
            .upload(
                file=indices_file,
                path=indices_filename,
                file_options={"cache-control": "3600", "upsert": "false"}
            )
        )
        logger.info(f"Indices file uploaded successfully: {indices_filename}")

        return insert_file_info(
            identifier=identifier,
            video_filename=video_filename,
            video_path=video_response.full_path,
            indices_filename=indices_filename,
            indices_path=indices_response.full_path,
            uploaded_at=datetime.now(UTC).isoformat()
        )
    except Exception as e:
        logger.error(f"Error during file upload: {e}")
        raise e

def insert_file_info(identifier, video_filename, video_path, indices_filename, indices_path, uploaded_at):
    """
    Inserts metadata for both uploaded files into the database.
    """
    try:
        response = (
            supabase
            .table("peer_files")
            .insert({
                "identifier": identifier,
                "video_name": video_filename,
                "video_path": video_path,
                "indices_name": indices_filename,
                "indices_path": indices_path,
                "uploaded_at": uploaded_at,
            })
            .execute()
        )
        logger.info(f"Database entry created for identifier: {identifier}")
        return response.data[0]["identifier"]
    except Exception as e:
        logger.error(f"Error inserting file info into database: {e}")
        raise e