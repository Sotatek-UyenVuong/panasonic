import base64
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
import urllib.parse
import asyncio


SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_credentials():
    """Xác thực và lấy credentials cho Gmail API"""
    creds = None
    if os.path.exists('commons/oauth2/token.json'):
        creds = Credentials.from_authorized_user_file('commons/oauth2/token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'commons/oauth2/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('commons/oauth2/token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

EMAIL_TEMPLATES = {
    "welcome": {
        "subject": "Your AI Note-Taking Journey Begins! 🚀",
        "body": """
<div style="font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;box-sizing:border-box;font-size:14px;max-width:600px;display:block;margin:0 auto;padding:24px">
Hi {name},<br><br>

Welcome to <strong>NoteX AI</strong>! 🎉 We're excited to have you join our community of productive note-takers.<br><br>

<span style="font-weight:600">Getting Started Guide:</span><br>
━━━━━━━━━━━━━━━━━━━━<br>
📱 <strong>Mobile Access</strong><br>
   • iOS: NoteX AI Note Taker<br>
   • Android: AI Note Taking, Voice To Notes<br><br>

🌐 <strong>Web Platform</strong><br>
   • Access your notes at: <span style="color:#0066CC">notexapp.com</span><br>
   • Sync across all your devices<br><br>

🎯 <strong>Key Features</strong><br>
   • Voice recording up to 6 hours<br>
   • AI transcription (99.2% accuracy)<br>
   • Topic-based AI summaries<br>
   • Document, audio & YouTube imports<br>
   • 100+ languages<br>
   • AI mind maps, flashcards & quizzes<br>
   • AI Chat with Notes<br>
   • Easy Share & Sync<br>
   • Weekly updates<br><br>

<span style="font-weight:600">💫 Upgrade to NoteX Pro Today</span><br>
━━━━━━━━━━━━━━━━━━━━<br>
Start your <strong>7-day free trial</strong> and unlock:<br>
   • Unlimited everything<br>
   • Cross-device Sync<br>
   • Advanced AI models<br>
   • Priority Support<br><br>

<strong>Need Help?</strong><br>
• Email: <span style="color:#0066CC">hello@notexapp.com</span><br><br>

Start taking smarter notes today! Achieve More, Stress Less with NoteX AI!<br><br>

Best regards,<br>
The NoteX AI Team
</div>""",
        "footer_reason": "You are receiving this email because you signed up for NoteX AI.",
    },
    
    "pro_confirmation": {
        "subject": "You've Unlocked NoteX AI Pro - Here's Everything! ⚡",
        "body": """
<div style="font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;box-sizing:border-box;font-size:14px;max-width:600px;display:block;margin:0 auto;padding:24px">
Hi {name},<br><br>

<strong>Welcome to NoteX Pro!</strong> 🎉.<br><br>

<span style="font-weight:600">Your Pro Features:</span><br>
━━━━━━━━━━━━━━<br>
   ✨ Unlimited access<br>
   🔄 Seamless sync<br>
   🤖 Advanced AI<br>
   💫 Premium support<br><br>

Questions? Email <span style="color:#0066CC">hello@notexapp.com</span><br><br>

Best regards,<br>
The NoteX AI Team
</div>""",
        "footer_reason": "You are receiving this email because you subscribed to NoteX Pro.",
    },
    
    "cancellation": {
        "subject": "Quick Question + Special 50% Off Deal Inside 🎁",
        "body": """
<div style="font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;box-sizing:border-box;font-size:14px;max-width:600px;display:block;margin:0 auto;padding:24px">
Hi {name},<br><br>

Your NoteX Pro access continues until the end of your billing period.<br><br>

<span style="font-weight:600">Help Us Improve:</span><br>
━━━━━━━━━━━━━<br>
Share your thoughts on:<br>
   1. Reason for cancellation<br>
   2. Most/least useful features<br>
   3. Desired improvements<br><br>

<span style="font-weight:600">💫 Special Offer:</span><br>
━━━━━━━━━━━━<br>
   • 20% off with code: <strong>WELCOMEBACK</strong><br>
   • Additional 30% savings on web subscriptions<br><br>

Questions? Email <span style="color:#0066CC">hello@notexapp.com</span><br><br>

Thank you for being part of NoteX.<br><br>

Best regards,<br>
The NoteX AI Team
</div>""",
        "footer_reason": "You are receiving this email because you recently cancelled your NoteX Pro subscription.",
    },
    
    "expiration": {
        "subject": "[Time Sensitive] 50% Off NoteX AI Pro - Today Only! 🔥",
        "body": """
<div style="font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;box-sizing:border-box;font-size:14px;max-width:600px;display:block;margin:0 auto;padding:24px">
Hi {name},<br><br>

Missing NoteX Pro? Here's what's new:<br><br>

<span style="font-weight:600">Latest Updates:</span><br>
━━━━━━━━━━━━<br>
🚀 <strong>New Features</strong><br>
   • Redesigned web interface<br>
   • Enhanced mobile apps<br>
   • Faster sync<br>
   • AI chat with notes<br>
   • Document uploads<br>
   • Advanced search<br><br>

<span style="font-weight:600">Special Offer:</span><br>
━━━━━━━━━━━<br>
   • 20% off: Use code <strong>WELCOMEBACK</strong><br>
   • 30% extra savings on web subscriptions<br><br>

<span style="font-weight:600">Reactivate Pro:</span><br>
━━━━━━━━━━━<br>
   • Visit <a href="https://notexapp.com/iap" style="color:#0066CC">Welcome Back Link</a><br>
   • Enter: <strong>WELCOMEBACK</strong> on DISCOUNT CODE<br>
   • Resume Unlimited AI Note features<br><br>

Questions? Email <span style="color:#0066CC">hello@notexapp.com</span><br><br>

We look forward to welcoming you back!<br><br>

Best regards,<br>
The NoteX AI Team
</div>""",
        "footer_reason": "You are receiving this email because you were previously a NoteX Pro subscriber.",
    },
    
    "invitation": {
        "subject": "🎯 Join {enterprise_name} on NoteX AI",
        "body": """
<div style="font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;box-sizing:border-box;max-width:600px;margin:0 auto;padding:40px 20px;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1)">
    <h1 style="margin:0 0 30px;font-size:32px;font-weight:500;color:#202124">Hey there!</h1>
    
    <p style="margin:0 0 30px;font-size:16px;line-height:1.6;color:#202124">
        You have been invited to join the <strong>{enterprise_name}</strong> workspace owned by <strong>{owner_name}</strong> on NoteX AI. To get started, accept the invite below:
    </p>

    <a href="{invitation_link}" style="display:inline-block;background:linear-gradient(135deg, #202124, #1a90ff);color:#ffffff;text-decoration:none;padding:12px 32px;border-radius:6px;font-size:16px">Accept Invite</a>
</div>""",
        "footer_reason": "You are receiving this email because you were invited to join an organization on NoteX AI.",
    }
}

def get_user_name(email):
    """Lấy tên người dùng từ địa chỉ email"""
    return email.split('@')[0].replace('.', ' ').title()

async def send_email(email_type, receiver_email, **kwargs):
    """
    Gửi email qua Gmail API
    """
    try:
        template = EMAIL_TEMPLATES.get(email_type)
        if not template:
            raise ValueError(f"Email template '{email_type}' không tồn tại")

        # Nếu không có name trong kwargs, lấy từ email
        if 'name' not in kwargs:
            kwargs['name'] = get_user_name(receiver_email)
            
        # Format cả subject và body với kwargs
        subject = template["subject"].format(**kwargs)  # Thêm format subject
        body = template["body"].format(**kwargs)
        
        encoded_email = urllib.parse.quote(receiver_email)
        unsubscribe_url = f"https://notexapp.com/unsubscribe?email={encoded_email}"
        
        footer_reason = template.get("footer_reason", "You are receiving this email because you signed up for NoteX AI.")
        unsubscribe_footer = f"""
        <div style="font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;box-sizing:border-box;font-size:14px;max-width:600px;display:block;margin:0 auto;padding:24px">
        <br><br>
        ━━━━━━━━━━━━━━━━━━━━<br>
        {footer_reason}<br>
        <a href="{unsubscribe_url}">Unsubscribe</a>
        </div>
        """
        
        full_body = body + unsubscribe_footer
        
        # Tạo message với Gmail API
        message = MIMEText(full_body, 'html')
        message['to'] = receiver_email
        message['from'] = "NoteX AI <hello@notexapp.com>"
        message['subject'] = subject  # Sử dụng subject đã format
        
        message.add_header('List-Unsubscribe', 
            f'<mailto:unsubscribe@notexapp.com?subject=Unsubscribe&body={encoded_email}>, <{unsubscribe_url}>')
        message.add_header('List-Unsubscribe-Post', 'List-Unsubscribe=One-Click')
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # Gửi email qua Gmail API
        creds = get_credentials()
        service = build('gmail', 'v1', credentials=creds)
        email_message = {'raw': raw_message}
        service.users().messages().send(userId="me", body=email_message).execute()
        
        print(f'✅ Email {email_type} đã được gửi thành công tới {receiver_email}!')
        
    except Exception as e:
        print(f"❌ Lỗi khi gửi email: {str(e)}")
        
        
async def send_invitation_email(email: str, enterprise_name: str, invitation_link: str, owner_name: str):
    """
    Gửi email mời tham gia tổ chức
    
    Args:
        email: Email người nhận
        enterprise_name: Tên tổ chức
        invitation_link: Link mời tham gia
    """
    await send_email(
        "invitation", 
        email,
        enterprise_name=enterprise_name,
        invitation_link=invitation_link,
        owner_name=owner_name
    )
        
        
# Test gửi email
async def test_send_email():
    await send_invitation_email(
        email="hung.dang@sotatek.com",
        enterprise_name="Sotatek Corporation",
        invitation_link="https://dev.notexapp.com/enterprise/join?token=R5DUh43VzLurKAADR8ly6tUHpIZSh4P6IFLd5QQ21nQ",
        owner_name="Hung Dang"
    )
# Chạy test
if __name__ == "__main__":
    asyncio.run(test_send_email())
        



