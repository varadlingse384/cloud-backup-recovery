
import os
from datetime import timezone

import boto3
import streamlit as st
from botocore.exceptions import ClientError, BotoCoreError


# ----------------------------------------
# CONFIGURATION
# ----------------------------------------

def get_setting(name, default=""):
    try:
        return st.secrets.get(name, os.getenv(name, default))
    except Exception:
        return os.getenv(name, default)


BUCKET_NAME = get_setting("S3_BUCKET_NAME").strip()
AWS_REGION = get_setting("AWS_REGION", "ap-southeast-2").strip()

AWS_ACCESS_KEY_ID = get_setting("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = get_setting("AWS_SECRET_ACCESS_KEY")

st.set_page_config(
    page_title="Cloud Backup and Recovery",
    page_icon="☁️",
    layout="wide"
)

st.title("☁️ Cloud-Based Backup and Recovery System")
st.write(
    "Upload, store, download, and recover files "
    "using Amazon S3."
)


# ----------------------------------------
# AWS CONNECTION
# ----------------------------------------

@st.cache_resource
def get_s3_client():
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        return boto3.client(
            "s3",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )

    return boto3.client(
        "s3",
        region_name=AWS_REGION,
    )


if not BUCKET_NAME:
    st.error(
        "S3_BUCKET_NAME is not configured. "
        "Set the environment variable and restart the app."
    )
    st.stop()

s3 = get_s3_client()


# ----------------------------------------
# HELPER FUNCTIONS
# ----------------------------------------

def format_size(size):
    if size < 1024:
        return f"{size} B"

    if size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"

    return f"{size / (1024 * 1024):.2f} MB"


def list_backups():
    paginator = s3.get_paginator("list_objects_v2")
    backups = []

    for page in paginator.paginate(Bucket=BUCKET_NAME):
        backups.extend(page.get("Contents", []))

    return backups


def get_file_versions(file_name):
    paginator = s3.get_paginator("list_object_versions")
    versions = []

    for page in paginator.paginate(
        Bucket=BUCKET_NAME,
        Prefix=file_name
    ):
        for version in page.get("Versions", []):
            if version["Key"] == file_name:
                versions.append(version)

    return sorted(
        versions,
        key=lambda version: version["LastModified"],
        reverse=True
    )


def show_error(error):
    st.error(
        "The operation failed. Check your AWS credentials, "
        "bucket name, Region, network connection, and IAM "
        "permissions."
    )

    if isinstance(error, ClientError):
        code = error.response.get(
            "Error", {}
        ).get("Code", "Unknown")

        st.caption(f"AWS error code: {code}")


# ----------------------------------------
# SIDEBAR
# ----------------------------------------

st.sidebar.header("Project Menu")

page = st.sidebar.radio(
    "Choose an operation",
    [
        "Upload Backup",
        "View Backups",
        "Download Backup",
        "Recover Previous Version",
        "Delete Backup"
    ]
)


# ----------------------------------------
# UPLOAD BACKUP
# ----------------------------------------

if page == "Upload Backup":

    st.header("Upload Files")

    uploaded_files = st.file_uploader(
        "Choose files to back up",
        accept_multiple_files=True
    )

    if st.button("Upload to AWS S3"):

        if not uploaded_files:
            st.warning("Select at least one file.")

        else:
            for uploaded_file in uploaded_files:

                try:
                    s3.upload_fileobj(
                        uploaded_file,
                        BUCKET_NAME,
                        uploaded_file.name
                    )

                    st.success(
                        f"Successfully uploaded: "
                        f"{uploaded_file.name}"
                    )

                except (ClientError, BotoCoreError) as error:
                    show_error(error)


# ----------------------------------------
# VIEW BACKUPS
# ----------------------------------------

elif page == "View Backups":

    st.header("Stored Backups")

    if st.button("Refresh Backup List"):

        try:
            backups = list_backups()

            if not backups:
                st.info("No backups are available.")

            else:
                backups.sort(
                    key=lambda item: item["LastModified"],
                    reverse=True
                )

                for backup in backups:
                    st.write(f"**File:** {backup['Key']}")

                    st.write(
                        f"**Size:** "
                        f"{format_size(backup['Size'])}"
                    )

                    modified = backup[
                        "LastModified"
                    ].astimezone(timezone.utc)

                    st.write(
                        f"**Last modified (UTC):** "
                        f"{modified}"
                    )

                    st.divider()

        except (ClientError, BotoCoreError) as error:
            show_error(error)


# ----------------------------------------
# DOWNLOAD BACKUP
# ----------------------------------------

elif page == "Download Backup":

    st.header("Download a Backup")

    try:
        backups = list_backups()

        file_names = sorted(
            item["Key"] for item in backups
        )

        if not file_names:
            st.info("No backups are available.")

        else:
            selected_file = st.selectbox(
                "Choose a file",
                file_names
            )

            if st.button("Prepare File Download"):

                response = s3.get_object(
                    Bucket=BUCKET_NAME,
                    Key=selected_file
                )

                file_data = response["Body"].read()

                st.download_button(
                    label="Download File",
                    data=file_data,
                    file_name=os.path.basename(
                        selected_file
                    ),
                    key="download_" + selected_file
                )

    except (ClientError, BotoCoreError) as error:
        show_error(error)


# ----------------------------------------
# RECOVER PREVIOUS VERSION
# ----------------------------------------

elif page == "Recover Previous Version":

    st.header("Recover a Previous Version")

    try:
        backups = list_backups()

        file_names = sorted(
            item["Key"] for item in backups
        )

        if not file_names:
            st.info("No backups are available.")

        else:
            selected_file = st.selectbox(
                "Choose a file",
                file_names
            )

            versions = get_file_versions(
                selected_file
            )

            if not versions:
                st.info("No versions were found.")

            else:
                st.write("### Version History")

                version_labels = []

                for version in versions:
                    label = (
                        f"{version['LastModified']} | "
                        f"Version ID: {version['VersionId']}"
                    )

                    version_labels.append(label)

                selected_label = st.selectbox(
                    "Select a version",
                    version_labels
                )

                selected_index = version_labels.index(
                    selected_label
                )

                selected_version = versions[
                    selected_index
                ]

                version_id = selected_version[
                    "VersionId"
                ]

                st.write(
                    "Selected version: "
                    f"{version_id}"
                )

                response = s3.get_object(
                    Bucket=BUCKET_NAME,
                    Key=selected_file,
                    VersionId=version_id
                )

                file_data = response["Body"].read()

                st.download_button(
                    "Download Selected Version",
                    data=file_data,
                    file_name=os.path.basename(
                        selected_file
                    ),
                    key="version_download_" + version_id
                )

                st.warning(
                    "Restoring a previous version creates "
                    "a new current version. Choose carefully."
                )

                confirm_restore = st.checkbox(
                    "I confirm that I want to restore "
                    "this version as the current version."
                )

                if st.button("Restore Selected Version"):

                    if not confirm_restore:
                        st.warning(
                            "Confirm the restore operation first."
                        )

                    else:
                        s3.copy_object(
                            Bucket=BUCKET_NAME,
                            Key=selected_file,
                            CopySource={
                                "Bucket": BUCKET_NAME,
                                "Key": selected_file,
                                "VersionId": version_id
                            }
                        )

                        st.success(
                            "Previous version restored "
                            "as a new current version."
                        )

    except (ClientError, BotoCoreError) as error:
        show_error(error)


# ----------------------------------------
# DELETE BACKUP
# ----------------------------------------

elif page == "Delete Backup":

    st.header("Delete a Backup")

    st.warning(
        "In a versioned bucket, deleting an object "
        "usually creates a delete marker. Previous "
        "versions may remain stored."
    )

    try:
        backups = list_backups()

        file_names = sorted(
            item["Key"] for item in backups
        )

        if not file_names:
            st.info("No backups are available.")

        else:
            selected_file = st.selectbox(
                "Choose a file to delete",
                file_names
            )

            confirm_delete = st.checkbox(
                "I understand that this operation "
                "will delete the current object."
            )

            if st.button("Delete Selected Backup"):

                if not confirm_delete:
                    st.warning(
                        "Confirm the deletion first."
                    )

                else:
                    s3.delete_object(
                        Bucket=BUCKET_NAME,
                        Key=selected_file
                    )

                    st.success(
                        "Delete request completed. "
                        "Previous versions may still exist."
                    )

    except (ClientError, BotoCoreError) as error:
        show_error(error)

