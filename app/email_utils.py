from smtplib import SMTPException


# Function to mock sending email notification
def send_email_mock(to_email: str, subject: str, body: str):
    # Mock up of sending Email
    try:
        print(f"Sending email to {to_email}")
        print(f"Subject: {subject}")
        print(f"Body {body}")
        return True
    except SMTPException as e:
        print(f"Error sending email: {e}")
        return False
