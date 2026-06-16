"""
邮件发送工具
支持 SMTP 协议发送邮件（Gmail / QQ邮箱 / 163等）
"""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class EmailTool:
    """邮件发送工具"""

    name = 'email'
    description = '使用 SMTP 发送邮件'

    # 常见邮箱 SMTP 配置
    SMTP_CONFIGS = {
        'gmail.com':    ('smtp.gmail.com', 587),
        'qq.com':       ('smtp.qq.com', 587),
        '163.com':      ('smtp.163.com', 25),
        '126.com':      ('smtp.126.com', 25),
        'outlook.com':  ('smtp-mail.outlook.com', 587),
        'hotmail.com':  ('smtp-mail.outlook.com', 587),
        'office365.com':('smtp.office365.com', 587),
    }

    @classmethod
    def _get_smtp_config(cls, from_email: str) -> tuple:
        """根据发件人邮箱获取 SMTP 配置"""
        domain = from_email.split('@')[-1].lower()
        return cls.SMTP_CONFIGS.get(domain, ('smtp.' + domain, 587))

    @classmethod
    def send(
        cls,
        to_email: str,
        subject: str,
        body: str,
        from_email: str = None,
        smtp_password: str = None,
        smtp_host: str = None,
        smtp_port: int = None,
        is_html: bool = False,
    ) -> dict:
        """
        发送邮件

        参数:
            to_email:   收件人邮箱
            subject:    邮件主题
            body:       邮件正文
            from_email: 发件人邮箱（默认取环境变量 EMAIL_FROM）
            smtp_password: SMTP 密码/授权码（默认取环境变量 EMAIL_PASSWORD）
            smtp_host:  SMTP 服务器（自动推断）
            smtp_port:  SMTP 端口（自动推断）
            is_html:    正文是否为 HTML

        返回:
            {'success': True/False, 'message': '...'}
        """
        from_email = from_email or os.getenv('EMAIL_FROM', '')
        smtp_password = smtp_password or os.getenv('EMAIL_PASSWORD', '')

        if not from_email or not smtp_password:
            return {
                'success': False,
                'error': '请配置 EMAIL_FROM 和 EMAIL_PASSWORD 环境变量。'
                         'QQ邮箱请使用授权码（设置→账户→POP3/SMTP服务→生成授权码）',
            }

        if not to_email:
            return {'success': False, 'error': '收件人邮箱不能为空'}

        # 自动获取 SMTP 配置
        if not smtp_host:
            smtp_host, default_port = cls._get_smtp_config(from_email)
            smtp_port = smtp_port or default_port

        try:
            # 构建邮件
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject

            content_type = 'html' if is_html else 'plain'
            msg.attach(MIMEText(body, content_type, 'utf-8'))

            # 发送
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                server.starttls()
                server.login(from_email, smtp_password)
                server.sendmail(from_email, to_email, msg.as_string())

            return {
                'success': True,
                'message': f'邮件已发送至 {to_email}',
            }

        except smtplib.SMTPAuthenticationError:
            return {'success': False, 'error': 'SMTP 认证失败，请检查邮箱地址和授权码'}
        except smtplib.SMTPConnectError:
            return {'success': False, 'error': f'无法连接到 SMTP 服务器 {smtp_host}:{smtp_port}'}
        except smtplib.SMTPException as e:
            return {'success': False, 'error': f'SMTP 错误: {str(e)}'}
        except Exception as e:
            logger.error(f'邮件发送异常: {e}')
            return {'success': False, 'error': f'发送失败: {str(e)}'}
