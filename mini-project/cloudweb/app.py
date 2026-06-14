import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config

app = Flask(__name__)
CORS(app)

def get_aws_client(service, credentials):
    config = Config(signature_version='s3v4') if service == 's3' else None
    return boto3.client(
        service,
        aws_access_key_id=credentials.get('access_key'),
        aws_secret_access_key=credentials.get('secret_key'),
        region_name=credentials.get('region'),
        config=config
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/verify', methods=['POST'])
def verify_credentials():
    data = request.json
    try:
        sts = get_aws_client('sts', data)
        identity = sts.get_caller_identity()
        return jsonify({"status": "success", "message": "Credentials verified", "identity": identity['Arn']})
    except ClientError as e:
        return jsonify({"status": "error", "message": str(e)}), 401

# S3 Operations
@app.route('/api/s3/list', methods=['POST'])
def list_buckets():
    data = request.json
    try:
        s3 = get_aws_client('s3', data)
        response = s3.list_buckets()
        buckets = [bucket['Name'] for bucket in response.get('Buckets', [])]
        return jsonify({"status": "success", "buckets": buckets})
    except ClientError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/s3/create', methods=['POST'])
def create_bucket():
    data = request.json
    bucket_name = data.get('bucket_name')
    region = data.get('region')
    if not bucket_name:
        return jsonify({"status": "error", "message": "Bucket name is required"}), 400
    
    try:
        s3 = get_aws_client('s3', data)
        # S3 create_bucket in us-east-1 does not accept LocationConstraint
        if region == 'us-east-1':
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region}
            )
            
        # Add CORS configuration to allow direct browser uploads (kept for backwards compatibility if needed, but not required for backend upload)
        cors_configuration = {
            'CORSRules': [{
                'AllowedHeaders': ['*'],
                'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE', 'HEAD'],
                'AllowedOrigins': ['*'], # In production, restrict this to your domain
                'ExposeHeaders': ['ETag']
            }]
        }
        s3.put_bucket_cors(Bucket=bucket_name, CORSConfiguration=cors_configuration)
        
        return jsonify({"status": "success", "message": f"Bucket {bucket_name} created successfully"})
    except ClientError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/s3/objects', methods=['POST'])
def list_objects():
    data = request.json
    bucket_name = data.get('bucket_name')
    if not bucket_name:
        return jsonify({"status": "error", "message": "Bucket name is required"}), 400
    try:
        s3 = get_aws_client('s3', data)
        response = s3.list_objects_v2(Bucket=bucket_name)
        objects = []
        for obj in response.get('Contents', []):
            objects.append({
                "Key": obj['Key'],
                "Size": obj['Size'],
                "LastModified": obj['LastModified'].strftime("%Y-%m-%d %H:%M:%S") if 'LastModified' in obj else ''
            })
        return jsonify({"status": "success", "objects": objects})
    except ClientError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/s3/upload', methods=['POST'])
def upload_object():
    # Use request.form for fields and request.files for the file
    data = request.form.to_dict()
    file = request.files.get('file')
    
    bucket_name = data.get('bucket_name')
    if not bucket_name or not file:
        return jsonify({"status": "error", "message": "Bucket name and file are required"}), 400
        
    try:
        s3 = get_aws_client('s3', data)
        # Upload the file directly from memory using boto3
        s3.upload_fileobj(file, bucket_name, file.filename)
        return jsonify({"status": "success", "message": f"File {file.filename} uploaded successfully"})
    except ClientError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/s3/download_url', methods=['POST'])
def get_download_url():
    data = request.json
    bucket_name = data.get('bucket_name')
    file_name = data.get('file_name')
    if not bucket_name or not file_name:
        return jsonify({"status": "error", "message": "Bucket name and file name are required"}), 400
    try:
        s3 = get_aws_client('s3', data)
        url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': file_name}, ExpiresIn=3600)
        return jsonify({"status": "success", "url": url})
    except ClientError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/s3/delete_object', methods=['POST'])
def delete_object():
    data = request.json
    bucket_name = data.get('bucket_name')
    file_name = data.get('file_name')
    if not bucket_name or not file_name:
        return jsonify({"status": "error", "message": "Bucket name and file name are required"}), 400
    try:
        s3 = get_aws_client('s3', data)
        s3.delete_object(Bucket=bucket_name, Key=file_name)
        return jsonify({"status": "success", "message": f"File {file_name} deleted successfully"})
    except ClientError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/s3/delete', methods=['POST'])
def delete_bucket():
    data = request.json
    bucket_name = data.get('bucket_name')
    if not bucket_name:
        return jsonify({"status": "error", "message": "Bucket name is required"}), 400
    try:
        s3 = get_aws_client('s3', data)
        s3.delete_bucket(Bucket=bucket_name)
        return jsonify({"status": "success", "message": f"Bucket {bucket_name} deleted successfully"})
    except ClientError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/s3/empty', methods=['POST'])
def empty_bucket():
    data = request.json
    bucket_name = data.get('bucket_name')
    if not bucket_name:
        return jsonify({"status": "error", "message": "Bucket name is required"}), 400
    try:
        s3 = get_aws_client('s3', data)
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name)
        delete_us = dict(Objects=[])
        for item in pages.search('Contents'):
            if item:
                delete_us['Objects'].append(dict(Key=item['Key']))
                if len(delete_us['Objects']) >= 1000:
                    s3.delete_objects(Bucket=bucket_name, Delete=delete_us)
                    delete_us = dict(Objects=[])
        if len(delete_us['Objects']):
            s3.delete_objects(Bucket=bucket_name, Delete=delete_us)
            
        return jsonify({"status": "success", "message": f"Bucket {bucket_name} emptied successfully"})
    except ClientError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# EC2 Operations
@app.route('/api/ec2/list', methods=['POST'])
def list_instances():
    data = request.json
    try:
        ec2 = get_aws_client('ec2', data)
        response = ec2.describe_instances()
        instances = []
        for reservation in response.get('Reservations', []):
            for inst in reservation.get('Instances', []):
                name = "Unknown"
                for tag in inst.get('Tags', []):
                    if tag['Key'] == 'Name':
                        name = tag['Value']
                        break
                instances.append({
                    "InstanceId": inst['InstanceId'],
                    "InstanceType": inst['InstanceType'],
                    "State": inst['State']['Name'],
                    "Name": name
                })
        return jsonify({"status": "success", "instances": instances})
    except ClientError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/ec2/keypairs', methods=['POST'])
def list_keypairs():
    data = request.json
    try:
        ec2 = get_aws_client('ec2', data)
        response = ec2.describe_key_pairs()
        keypairs = [kp['KeyName'] for kp in response.get('KeyPairs', [])]
        return jsonify({"status": "success", "keypairs": keypairs})
    except ClientError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/ec2/securitygroups', methods=['POST'])
def list_securitygroups():
    data = request.json
    try:
        ec2 = get_aws_client('ec2', data)
        response = ec2.describe_security_groups()
        groups = [{"GroupId": sg['GroupId'], "GroupName": sg['GroupName']} for sg in response.get('SecurityGroups', [])]
        return jsonify({"status": "success", "security_groups": groups})
    except ClientError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/ec2/create_sg', methods=['POST'])
def create_security_group():
    data = request.json
    sg_name = data.get('sg_name')
    if not sg_name:
        return jsonify({"status": "error", "message": "Security Group name is required"}), 400
    try:
        ec2 = get_aws_client('ec2', data)
        # Create Security Group
        response = ec2.create_security_group(GroupName=sg_name, Description='Created via AWS Automation Dashboard')
        group_id = response['GroupId']
        
        # Authorize Ingress for SSH and HTTP
        ec2.authorize_security_group_ingress(
            GroupId=group_id,
            IpPermissions=[
                {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
            ]
        )
        return jsonify({"status": "success", "message": f"Security Group {sg_name} created successfully"})
    except ClientError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/ec2/launch', methods=['POST'])
def launch_instance():
    data = request.json
    ami_id = data.get('ami_id')
    instance_type = data.get('instance_type', 't2.micro')
    instance_name = data.get('instance_name', 'MyInstance')
    key_name = data.get('key_name')
    sg_id = data.get('security_group_id')
    count = int(data.get('count', 1))
    
    if not ami_id:
        return jsonify({"status": "error", "message": "AMI ID is required"}), 400
        
    try:
        ec2 = get_aws_client('ec2', data)
        
        launch_params = {
            'ImageId': ami_id,
            'InstanceType': instance_type,
            'MinCount': count,
            'MaxCount': count,
            'TagSpecifications': [
                {
                    'ResourceType': 'instance',
                    'Tags': [{'Key': 'Name', 'Value': instance_name}]
                }
            ]
        }
        
        if key_name and key_name != 'None':
            launch_params['KeyName'] = key_name
        if sg_id and sg_id != 'None':
            launch_params['SecurityGroupIds'] = [sg_id]

        response = ec2.run_instances(**launch_params)
        
        instance_ids = [inst['InstanceId'] for inst in response['Instances']]
        return jsonify({"status": "success", "message": f"{len(instance_ids)} instance(s) launched successfully", "instance_ids": instance_ids})
    except ClientError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/ec2/start', methods=['POST'])
def start_instance():
    data = request.json
    instance_id = data.get('instance_id')
    try:
        ec2 = get_aws_client('ec2', data)
        ec2.start_instances(InstanceIds=[instance_id])
        return jsonify({"status": "success", "message": f"Instance {instance_id} starting"})
    except ClientError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/ec2/stop', methods=['POST'])
def stop_instance():
    data = request.json
    instance_id = data.get('instance_id')
    try:
        ec2 = get_aws_client('ec2', data)
        ec2.stop_instances(InstanceIds=[instance_id])
        return jsonify({"status": "success", "message": f"Instance {instance_id} stopping"})
    except ClientError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/ec2/terminate', methods=['POST'])
def terminate_instance():
    data = request.json
    instance_id = data.get('instance_id')
    try:
        ec2 = get_aws_client('ec2', data)
        ec2.terminate_instances(InstanceIds=[instance_id])
        return jsonify({"status": "success", "message": f"Instance {instance_id} terminating"})
    except ClientError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/ec2/ssm_command', methods=['POST'])
def ssm_command():
    data = request.json
    instance_id = data.get('instance_id')
    command = data.get('command')
    if not instance_id or not command:
        return jsonify({"status": "error", "message": "Instance ID and command are required"}), 400
        
    try:
        ssm = get_aws_client('ssm', data)
        import time
        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={'commands': [command]}
        )
        command_id = response['Command']['CommandId']
        
        # Wait a bit for execution
        time.sleep(2)
        
        try:
            output = ssm.get_command_invocation(
                CommandId=command_id,
                InstanceId=instance_id
            )
            status = output.get('Status')
            
            if status in ['Pending', 'InProgress']:
                time.sleep(3)
                output = ssm.get_command_invocation(
                    CommandId=command_id,
                    InstanceId=instance_id
                )
                
            stdout = output.get('StandardOutputContent', '')
            stderr = output.get('StandardErrorContent', '')
            
            if stderr and not stdout:
                return jsonify({"status": "error", "message": stderr.strip()}), 400
            return jsonify({"status": "success", "output": stdout.strip()})
        except ssm.exceptions.InvocationDoesNotExist:
            return jsonify({"status": "error", "message": "Command sent, but output not available. Ensure SSM agent is running on the instance."}), 400
            
    except ClientError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/log_error', methods=['POST'])
def log_error():
    data = request.json
    print("\n" + "="*50)
    print("FRONTEND S3 UPLOAD ERROR:")
    for k, v in data.items():
        print(f"{k}: {v}")
    print("="*50 + "\n", flush=True)
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
