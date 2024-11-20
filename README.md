## Installation

Install [Python 3.10+](https://www.python.org/getit/) and run the below commands

```bash
pip3 install --upgrade pip
python3 -m venv .venv      # create virtual environment for installing dependencies
source ./.venv/bin/activate  # Activate virtual environment for macOS/linux
pip3 install -r requirements.txt
```

Update .env
- USER_NAME="email-id"
- PWD="password"
- MOBILE="mobile-number"
- INPUT_FILE="file-name-of-resume" //Put the file in the root directory of project
- OUTPUT_FILE="output-file-name-of-resume" //Name shiuld be different than input file

Optional env varaibles - If you running this as a cron job and need to send the logs to your mail.
If you don't need this you can comment out mail_logs()
- AWS_ACCESS_KEY_ID="aws-access-key-id"
- AWS_SECRET_ACCESS_KEY="aws-access-key"
- SNS_TOPIC="aws-sns-topic-arn"
- AWS_REGION="aws-region"

To run the script in a docker container
```bash
docker build -t automation-image .
docker run -d --name automation-container -p 8080:8080 automation-image
```
You can push the image to AWS ECR and then deploy it as a cron job using ECS(Fargate)

To run the application locally
```bash
python3 main.py
```

Extension of https://github.com/navchandar/Naukri
