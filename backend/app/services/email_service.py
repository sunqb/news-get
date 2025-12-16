import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import get_settings

settings = get_settings()


async def send_email(to_email: str, subject: str, body: str, html_body: str | None = None):
    """发送邮件"""
    message = MIMEMultipart("alternative")
    message["From"] = settings.smtp_from
    message["To"] = to_email
    message["Subject"] = subject

    # 添加纯文本内容
    part1 = MIMEText(body, "plain", "utf-8")
    message.attach(part1)

    # 如果有HTML内容，也添加
    if html_body:
        part2 = MIMEText(html_body, "html", "utf-8")
        message.attach(part2)

    try:
        # 465端口使用SSL，587端口使用STARTTLS
        use_tls = settings.smtp_port == 465
        start_tls = settings.smtp_port == 587 and settings.smtp_tls

        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            use_tls=use_tls,
            start_tls=start_tls,
        )
        print(f"邮件发送成功: {to_email}")
        return True
    except Exception as e:
        print(f"发送邮件失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def send_verification_code(to_email: str, code: str):
    """发送验证码邮件"""
    subject = "您的登录验证码"
    body = f"""
您好！

您的登录验证码是：{code}

验证码有效期为10分钟，请尽快使用。

如果这不是您的操作，请忽略此邮件。

---
News Task Manager
"""
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #333;">登录验证码</h2>
    <p>您好！</p>
    <p>您的登录验证码是：</p>
    <div style="background-color: #f5f5f5; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px;">
        <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #333;">{code}</span>
    </div>
    <p style="color: #666;">验证码有效期为10分钟，请尽快使用。</p>
    <p style="color: #999; font-size: 12px;">如果这不是您的操作，请忽略此邮件。</p>
    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
    <p style="color: #999; font-size: 12px;">News Task Manager</p>
</body>
</html>
"""
    return await send_email(to_email, subject, body, html_body)


async def send_task_result(to_email: str, task_name: str, result: str):
    """发送任务执行结果邮件"""
    subject = f"任务执行结果: {task_name}"
    body = f"""
您好！

您的任务「{task_name}」已执行完成。

执行结果：
{result}

---
News Task Manager
"""
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #333;">任务执行结果</h2>
    <p>您好！</p>
    <p>您的任务「<strong>{task_name}</strong>」已执行完成。</p>
    <div style="background-color: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 8px; white-space: pre-wrap;">
{result}
    </div>
    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
    <p style="color: #999; font-size: 12px;">News Task Manager</p>
</body>
</html>
"""
    return await send_email(to_email, subject, body, html_body)
