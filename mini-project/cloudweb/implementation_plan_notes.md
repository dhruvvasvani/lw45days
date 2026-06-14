# Goal Description

The goal is to expand the AWS Automation Dashboard into a full-featured AWS Management tool. We will add advanced EC2 launching configurations (AMI selection, Key Pairs, Security Groups, Instance Count) and introduce complete S3 file management (uploading, downloading, and viewing files within buckets).

## User Review Required

> [!IMPORTANT]
> To handle S3 file uploads efficiently through a web UI, the best approach is for the Python backend to generate a **Presigned URL**, allowing the browser to upload the file directly to AWS. This avoids sending large files through the local Python server. Please confirm if this approach is acceptable.

## Open Questions

1. **EC2 AMIs:** AWS AMIs vary by region. Would you prefer a dropdown of common OS options (e.g., Ubuntu, Amazon Linux) where the backend dynamically finds the correct AMI ID for your selected region, or do you still want the ability to manually paste a specific AMI ID?
2. **Key Pair Download:** When creating a new Key Pair via the webapp, the `.pem` file will be downloaded directly to your local machine. Is this the behavior you expect?

## Proposed Changes

### Backend Operations (Python)

#### [MODIFY] app.py
**EC2 Enhancements:**
- `/api/ec2/keypairs`: List existing key pairs.
- `/api/ec2/securitygroups`: List existing security groups.
- Update `/api/ec2/launch`: Add support for `MinCount`, `MaxCount`, `KeyName`, and `SecurityGroupIds`.

**S3 File Handling:**
- `/api/s3/objects`: List files (objects) inside a specific bucket.
- `/api/s3/upload_url`: Generate a presigned POST URL for uploading files directly to S3.
- `/api/s3/download_url`: Generate a presigned GET URL for downloading files securely.
- `/api/s3/delete_object`: Delete a specific file from a bucket.

### Frontend UI/UX (HTML, CSS, JS)

#### [MODIFY] templates/index.html
- **EC2 Launch Form:** Add dropdowns for AMI selection, Key Pairs, and Security Groups. Add a number input for Instance Count.
- **S3 Bucket View:** Add a new modal or expanding section under each bucket to list files.
- **File Upload:** Add a drag-and-drop or file selection area inside the S3 bucket view.

#### [MODIFY] static/js/main.js
- Implement logic to fetch and populate Key Pairs and Security Groups when the dashboard loads.
- Build the logic for S3 file navigation (clicking a bucket shows its files).
- Implement direct-to-S3 file uploading using the presigned URLs from the backend.

#### [MODIFY] static/css/style.css
- Add styles for the new S3 file browser and file upload zones.
- Style the advanced EC2 form to remain clean and visually appealing within the 3D aesthetic.

## Verification Plan

### Manual Verification
1. Verify EC2 Launch form has all new fields (Key Pair, SG, Count, AMI Dropdown).
2. Successfully launch 2 Ubuntu instances with a selected Key Pair and Security Group.
3. Open an S3 bucket in the UI, upload a test image, view it in the list, and download it back to the local machine.
