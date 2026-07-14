# Install dependencies
Write-Host "Installing dependencies..."
pip install -r requirements.txt

# Run the Flask app
Write-Host "Starting the AWS Automation Webapp..."
python app.py
