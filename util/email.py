import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sender = "sanjayait16@gmail.com"
password = "oehpqvciofnywejj"

def get_otp_template(otp: int) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                font-family: Arial, sans-serif;
            }}
            .header {{
                background-color: #4CAF50;
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 5px 5px 0 0;
            }}
            .content {{
                background-color: #f9f9f9;
                padding: 20px;
                border-radius: 0 0 5px 5px;
            }}
            .otp-container {{
                background-color: #ffffff;
                padding: 15px;
                margin: 20px 0;
                border-radius: 5px;
                text-align: center;
            }}
            .otp-code {{
                font-size: 32px;
                font-weight: bold;
                color: #4CAF50;
                letter-spacing: 5px;
                cursor: pointer;
            }}
            .copy-text {{
                color: #666;
                font-size: 14px;
                margin-top: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Password Reset OTP</h2>
            </div>
            <div class="content">
                <p>Hello,</p>
                <p>You have requested to reset your password. Please use the following OTP to verify your identity:</p>
                <div class="otp-container">
                    <div class="otp-code" onclick="navigator.clipboard.writeText('{otp}')" title="Click to copy">
                        {otp}
                    </div>
                    <p class="copy-text">(Click the OTP to copy to clipboard)</p>
                </div>
                <p>This OTP will expire in 10 minutes. If you didn't request this password reset, please ignore this email.</p>
                <p>Best regards,<br>Your App Team</p>
            </div>
        </div>
    </body>
    </html>
    """

def send_email(subject: str, recipient: str, html_content: str):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient
    
    html_part = MIMEText(html_content, 'html')
    msg.attach(html_part)
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp_server:
            smtp_server.ehlo()
            smtp_server.starttls()
            smtp_server.ehlo()
            smtp_server.login(sender, password)
            smtp_server.sendmail(sender, recipient, msg.as_string())
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False