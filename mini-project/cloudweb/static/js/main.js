document.addEventListener('DOMContentLoaded', () => {
    // State
    let awsCredentials = null;

    // Elements
    const credsForm = document.getElementById('creds-form');
    const authStatus = document.getElementById('auth-status');
    const dashboard = document.getElementById('dashboard');
    const verifyBtn = document.getElementById('verify-btn');
    const toast = document.getElementById('toast');

    // Tabs
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    // S3 Elements
    const s3Form = document.getElementById('s3-form');
    const refreshS3Btn = document.getElementById('refresh-s3');
    const s3List = document.getElementById('s3-list');

    // EC2 Elements
    const ec2Form = document.getElementById('ec2-form');
    const refreshEc2Btn = document.getElementById('refresh-ec2');
    const ec2List = document.getElementById('ec2-list');

    // User Type Logic
    const userTypeRadios = document.querySelectorAll('input[name="userType"]');
    const rootWarning = document.getElementById('root-warning');
    const credTitle = document.getElementById('cred-title');

    userTypeRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (e.target.value === 'root') {
                rootWarning.classList.remove('hidden');
                if (credTitle) credTitle.innerHTML = 'Root Credentials';
            } else {
                rootWarning.classList.add('hidden');
                if (credTitle) credTitle.innerHTML = 'IAM Credentials';
            }
        });
    });

    // Custom Cursor Logic
    const customCursor = document.getElementById('custom-cursor');
    document.addEventListener('mousemove', (e) => {
        if (dashboard.classList.contains('hidden')) {
            document.body.classList.add('use-custom-cursor');
            customCursor.style.display = 'block';
            customCursor.style.transform = `translate(${e.clientX}px, ${e.clientY}px)`;
        } else {
            document.body.classList.remove('use-custom-cursor');
            customCursor.style.display = 'none';
        }
    });

    // Helpers
    const showToast = (message, type = 'success') => {
        toast.textContent = message;
        toast.className = `toast show ${type}`;
        setTimeout(() => {
            toast.className = 'toast';
        }, 3000);
    };

    const apiCall = async (endpoint, payload = {}) => {
        if (!awsCredentials) {
            showToast("Missing AWS Credentials", "error");
            return null;
        }

        const data = { ...awsCredentials, ...payload };
        
        try {
            const response = await fetch(`/api${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.message || 'API Request Failed');
            }
            return result;
        } catch (error) {
            showToast(error.message, 'error');
            console.error(error);
            return null;
        }
    };

    // Tab Switching
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(btn.dataset.target).classList.add('active');
        });
    });

    // Credential Verification
    credsForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const accessKey = document.getElementById('accessKey').value;
        const secretKey = document.getElementById('secretKey').value;
        const region = document.getElementById('region').value;

        // Temporarily store
        awsCredentials = { access_key: accessKey, secret_key: secretKey, region: region };
        
        verifyBtn.textContent = 'Verifying...';
        verifyBtn.disabled = true;

        const result = await apiCall('/verify');
        
        verifyBtn.textContent = 'Verify Credentials';
        verifyBtn.disabled = false;

        if (result && result.status === 'success') {
            showToast('Credentials Verified Successfully!');
            authStatus.innerHTML = `<span style="color: var(--success)">Authenticated as: ${result.identity}</span>`;
            dashboard.classList.remove('hidden');
            
            // Load initial data
            loadS3Buckets();
            loadEC2Options();
            loadEC2Instances();
        } else {
            awsCredentials = null; // Clear if failed
            authStatus.innerHTML = `<span style="color: var(--error)">Authentication failed. Check credentials.</span>`;
            dashboard.classList.add('hidden');
        }
    });

    // S3 Operations
    const loadS3Buckets = async () => {
        s3List.innerHTML = '<div class="loading">Loading buckets...</div>';
        const result = await apiCall('/s3/list');
        
        if (result && result.buckets) {
            if (result.buckets.length === 0) {
                s3List.innerHTML = '<div class="loading">No buckets found in this region.</div>';
                return;
            }
            s3List.innerHTML = result.buckets.map(bucket => `
                <div class="resource-item" style="cursor: pointer;" onclick="openS3Modal('${bucket}')">
                    <span>🪣 ${bucket}</span>
                    <div onclick="event.stopPropagation()">
                        <button class="action-btn btn-warn" onclick="emptyS3('${bucket}')">Empty</button>
                        <button class="action-btn btn-danger" onclick="deleteS3('${bucket}')">Delete</button>
                    </div>
                </div>
            `).join('');
        } else {
            s3List.innerHTML = '<div class="loading" style="color: var(--error)">Failed to load buckets.</div>';
        }
    };

    s3Form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const bucketName = document.getElementById('bucketName').value;
        const submitBtn = s3Form.querySelector('button');
        
        submitBtn.disabled = true;
        submitBtn.textContent = 'Creating...';
        
        const result = await apiCall('/s3/create', { bucket_name: bucketName });
        
        submitBtn.disabled = false;
        submitBtn.textContent = 'Create Bucket';
        
        if (result && result.status === 'success') {
            showToast(result.message);
            document.getElementById('bucketName').value = '';
            loadS3Buckets();
        }
    });

    refreshS3Btn.addEventListener('click', loadS3Buckets);

    window.emptyS3 = async (bucket) => {
        if (!confirm(`WARNING: Are you sure you want to permanently empty all files in bucket '${bucket}'?`)) return;
        const result = await apiCall('/s3/empty', { bucket_name: bucket });
        if (result && result.status === 'success') { showToast(result.message); }
    };

    window.deleteS3 = async (bucket) => {
        if (!confirm(`Are you sure you want to delete bucket '${bucket}'? It must be empty first.`)) return;
        const result = await apiCall('/s3/delete', { bucket_name: bucket });
        if (result && result.status === 'success') { showToast(result.message); loadS3Buckets(); }
    };

    // S3 Modal & Objects
    let currentBucket = null;
    const s3Modal = document.getElementById('s3-modal');
    const s3ObjectsList = document.getElementById('s3-objects-list');
    const modalBucketName = document.getElementById('modal-bucket-name');
    const s3UploadForm = document.getElementById('s3-upload-form');
    
    document.getElementById('close-s3-modal').onclick = () => s3Modal.classList.add('hidden');

    window.openS3Modal = (bucket) => {
        currentBucket = bucket;
        modalBucketName.textContent = `Bucket: ${bucket}`;
        s3Modal.classList.remove('hidden');
        loadS3Objects();
    };

    const loadS3Objects = async () => {
        s3ObjectsList.innerHTML = '<div class="loading">Loading files...</div>';
        const result = await apiCall('/s3/objects', { bucket_name: currentBucket });
        if (result && result.objects) {
            if (result.objects.length === 0) {
                s3ObjectsList.innerHTML = '<div class="loading">Bucket is empty.</div>';
                return;
            }
            s3ObjectsList.innerHTML = result.objects.map(obj => `
                <div class="resource-item">
                    <div>
                        <strong>📄 ${obj.Key}</strong>
                        <div style="font-size: 0.8rem; color: var(--text-muted);">${(obj.Size / 1024).toFixed(2)} KB • ${obj.LastModified}</div>
                    </div>
                    <div>
                        <button class="action-btn btn-primary" onclick="downloadS3Object('${obj.Key}')">Download</button>
                        <button class="action-btn btn-danger" onclick="deleteS3Object('${obj.Key}')">Delete</button>
                    </div>
                </div>
            `).join('');
        }
    };

    s3UploadForm.onsubmit = async (e) => {
        e.preventDefault();
        const fileInput = document.getElementById('s3-file-input');
        const file = fileInput.files[0];
        if (!file) return;

        const submitBtn = s3UploadForm.querySelector('button');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Uploading...';

        const formData = new FormData();
        formData.append('file', file);
        formData.append('bucket_name', currentBucket);
        if (awsCredentials) {
            Object.keys(awsCredentials).forEach(key => formData.append(key, awsCredentials[key]));
        }

        try {
            const uploadRes = await fetch('/api/s3/upload', {
                method: 'POST',
                body: formData
            });
            const result = await uploadRes.json();
            
            if (uploadRes.ok && result.status === 'success') {
                showToast('File uploaded successfully!');
                fileInput.value = '';
                loadS3Objects();
            } else {
                console.error('S3 Upload Error:', result.message);
                showToast('Error: ' + (result.message || 'Upload failed'), 'error');
            }
        } catch (err) {
            console.error('Upload error:', err);
            showToast('Network error: ' + err.message, 'error');
        }
        
        submitBtn.disabled = false;
        submitBtn.textContent = 'Upload';
    };

    window.downloadS3Object = async (key) => {
        const result = await apiCall('/s3/download_url', { bucket_name: currentBucket, file_name: key });
        if (result && result.status === 'success') {
            window.open(result.url, '_blank');
        }
    };

    window.deleteS3Object = async (key) => {
        if (!confirm(`Delete file '${key}'?`)) return;
        const result = await apiCall('/s3/delete_object', { bucket_name: currentBucket, file_name: key });
        if (result && result.status === 'success') {
            showToast(result.message);
            loadS3Objects();
        }
    };

    // EC2 Operations
    const loadEC2Options = async () => {
        const kpRes = await apiCall('/ec2/keypairs');
        if (kpRes && kpRes.keypairs) {
            const kpSelect = document.getElementById('keyName');
            kpSelect.innerHTML = '<option value="None">None (No SSH Access)</option>';
            kpRes.keypairs.forEach(kp => {
                const opt = document.createElement('option');
                opt.value = kp; opt.textContent = kp;
                kpSelect.appendChild(opt);
            });
        }
        const sgRes = await apiCall('/ec2/securitygroups');
        if (sgRes && sgRes.security_groups) {
            const sgSelect = document.getElementById('securityGroup');
            sgSelect.innerHTML = '<option value="None">Default</option>';
            sgRes.security_groups.forEach(sg => {
                const opt = document.createElement('option');
                opt.value = sg.GroupId; opt.textContent = `${sg.GroupName} (${sg.GroupId})`;
                sgSelect.appendChild(opt);
            });
        }
    };

    const sgForm = document.getElementById('sg-form');
    if (sgForm) {
        sgForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const sgName = document.getElementById('sgName').value;
            const submitBtn = sgForm.querySelector('button');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Creating...';
            
            const result = await apiCall('/ec2/create_sg', { sg_name: sgName });
            if (result && result.status === 'success') {
                showToast(result.message);
                document.getElementById('sgName').value = '';
                loadEC2Options(); // Refresh the dropdown
            }
            submitBtn.disabled = false;
            submitBtn.textContent = 'Create SG';
        });
    }

    const loadEC2Instances = async () => {
        ec2List.innerHTML = '<div class="loading">Loading instances...</div>';
        const result = await apiCall('/ec2/list');
        
        if (result && result.instances) {
            if (result.instances.length === 0) {
                ec2List.innerHTML = '<div class="loading">No instances found in this region.</div>';
                return;
            }
            ec2List.innerHTML = result.instances.map(inst => `
                <div class="resource-item">
                    <div>
                        <strong>🖥️ ${inst.Name}</strong>
                        <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 4px;">
                            ${inst.InstanceId} • ${inst.InstanceType}
                        </div>
                    </div>
                    <span class="badge ${inst.State === 'running' ? 'running' : inst.State === 'stopped' ? 'stopped' : 'pending'}">
                        ${inst.State}
                    </span>
                    <div style="margin-top: 10px;">
                        ${inst.State === 'running' ? `<button class="action-btn btn-primary" onclick="openEC2Modal('${inst.InstanceId}', '${inst.Name}')">Manage Files</button>` : ''}
                        <button class="action-btn btn-success" onclick="startEC2('${inst.InstanceId}')">Start</button>
                        <button class="action-btn btn-warn" onclick="stopEC2('${inst.InstanceId}')">Stop</button>
                        <button class="action-btn btn-danger" onclick="terminateEC2('${inst.InstanceId}')">Terminate</button>
                    </div>
                </div>
            `).join('');
        } else {
            ec2List.innerHTML = '<div class="loading" style="color: var(--error)">Failed to load instances.</div>';
        }
    };

    ec2Form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const instanceName = document.getElementById('instanceName').value;
        const amiId = document.getElementById('amiId').value;
        const instanceType = document.getElementById('instanceType').value;
        const keyName = document.getElementById('keyName').value;
        const sgId = document.getElementById('securityGroup').value;
        const count = document.getElementById('instanceCount').value;
        
        const submitBtn = ec2Form.querySelector('button');
        
        submitBtn.disabled = true;
        submitBtn.textContent = 'Launching...';
        
        const result = await apiCall('/ec2/launch', { 
            instance_name: instanceName,
            ami_id: amiId,
            instance_type: instanceType,
            key_name: keyName,
            security_group_id: sgId,
            count: count
        });
        
        submitBtn.disabled = false;
        submitBtn.textContent = 'Launch Instance';
        
        if (result && result.status === 'success') {
            showToast(result.message);
            ec2Form.reset();
            loadEC2Instances();
        }
    });

    refreshEc2Btn.addEventListener('click', loadEC2Instances);

    window.startEC2 = async (instanceId) => {
        const result = await apiCall('/ec2/start', { instance_id: instanceId });
        if (result && result.status === 'success') { showToast(result.message); loadEC2Instances(); }
    };

    window.stopEC2 = async (instanceId) => {
        if (!confirm(`Are you sure you want to stop instance '${instanceId}'?`)) return;
        const result = await apiCall('/ec2/stop', { instance_id: instanceId });
        if (result && result.status === 'success') { showToast(result.message); loadEC2Instances(); }
    };

    window.terminateEC2 = async (instanceId) => {
        if (!confirm(`WARNING: Are you sure you want to TERMINATE instance '${instanceId}'? This is irreversible.`)) return;
        const result = await apiCall('/ec2/terminate', { instance_id: instanceId });
        if (result && result.status === 'success') { showToast(result.message); loadEC2Instances(); }
    };

    // EC2 Modal & Objects
    let currentInstanceId = null;
    const ec2Modal = document.getElementById('ec2-modal');
    const modalEc2Name = document.getElementById('modal-ec2-name');
    const ec2UploadForm = document.getElementById('ec2-upload-form');
    const ec2ListForm = document.getElementById('ec2-list-form');
    const ec2TerminalOutput = document.getElementById('ec2-terminal-output');
    
    if (document.getElementById('close-ec2-modal')) {
        document.getElementById('close-ec2-modal').onclick = () => {
            ec2Modal.classList.add('hidden');
            ec2TerminalOutput.textContent = '';
        };
    }

    window.openEC2Modal = (instanceId, name) => {
        currentInstanceId = instanceId;
        modalEc2Name.textContent = `EC2: ${name} (${instanceId})`;
        ec2Modal.classList.remove('hidden');
        ec2TerminalOutput.textContent = 'Ready. Run a command or upload a file. (Ensure SSM Agent is running on instance)\n';
    };

    if (ec2ListForm) {
        ec2ListForm.onsubmit = async (e) => {
            e.preventDefault();
            const dirPath = document.getElementById('ec2-dir-path').value;
            const submitBtn = ec2ListForm.querySelector('button');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Listing...';
            
            ec2TerminalOutput.textContent = `Running: ls -la ${dirPath} ...\n`;
            const result = await apiCall('/ec2/ssm_command', { instance_id: currentInstanceId, command: `ls -la ${dirPath}` });
            
            submitBtn.disabled = false;
            submitBtn.textContent = 'List Files';
            
            if (result) {
                if (result.status === 'success') {
                    ec2TerminalOutput.textContent += result.output + '\n';
                } else {
                    ec2TerminalOutput.textContent += `Error: ${result.message}\n`;
                }
            }
        };
    }

    if (ec2UploadForm) {
        ec2UploadForm.onsubmit = async (e) => {
            e.preventDefault();
            const targetPath = document.getElementById('ec2-target-path').value;
            const fileInput = document.getElementById('ec2-file-input');
            const file = fileInput.files[0];
            if (!file) return;

            const submitBtn = ec2UploadForm.querySelector('button');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Uploading...';
            
            ec2TerminalOutput.textContent = `Reading local file: ${file.name}...\n`;

            const reader = new FileReader();
            reader.onload = async (e) => {
                const base64Data = e.target.result.split(',')[1];
                const command = `echo '${base64Data}' | base64 -d > ${targetPath}`;
                
                ec2TerminalOutput.textContent += `Writing via SSM to: ${targetPath}...\n`;
                const result = await apiCall('/ec2/ssm_command', { instance_id: currentInstanceId, command: command });
                
                if (result) {
                    if (result.status === 'success') {
                        ec2TerminalOutput.textContent += `\nSuccess! File written to ${targetPath}\n${result.output}\n`;
                        showToast('File uploaded to EC2 successfully!');
                        fileInput.value = '';
                    } else {
                        ec2TerminalOutput.textContent += `\nError: ${result.message}\n`;
                        showToast('Failed to upload file to EC2', 'error');
                    }
                }
                
                submitBtn.disabled = false;
                submitBtn.textContent = 'Upload via SSM';
            };
            reader.onerror = () => {
                ec2TerminalOutput.textContent += `\nError reading file!`;
                submitBtn.disabled = false;
                submitBtn.textContent = 'Upload via SSM';
            };
            // Read as DataURL to get base64
            reader.readAsDataURL(file);
        };
    }
});
