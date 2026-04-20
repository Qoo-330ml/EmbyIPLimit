import logging
import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


class EmailNotifier:
    def __init__(self, config):
        email_config = config.get('email', {})
        self.enabled = email_config.get('enabled', False)
        self.smtp_server = email_config.get('smtp_server', 'smtp.qq.com')
        self.smtp_port = email_config.get('smtp_port', 465)
        self.sender_email = email_config.get('sender_email', '')
        self.sender_password = email_config.get('sender_password', '')
        self.use_ssl = email_config.get('use_ssl', True)

    def send_email(self, to_email, subject, html_body):
        if not self.enabled:
            logger.debug('邮件通知未启用，跳过发送')
            return False

        if not to_email:
            logger.debug('收件人邮箱为空，跳过发送')
            return False

        if not self.sender_email or not self.sender_password:
            logger.error('发件人邮箱或密码未配置')
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = Header(subject, 'utf-8')

            html_part = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(html_part)

            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()

            server.login(self.sender_email, self.sender_password)
            server.sendmail(self.sender_email, [to_email], msg.as_string())
            server.quit()

            logger.info('邮件发送成功: %s -> %s', self.sender_email, to_email)
            return True
        except Exception as exc:
            logger.exception('邮件发送失败: %s', exc)
            return False

    def send_wish_status_notification(self, to_email, title, media_type, new_status, admin_name='管理员'):
        status_labels = {
            'pending': '待处理',
            'approved': '已采纳',
            'rejected': '已拒绝',
        }
        status_text = status_labels.get(new_status, new_status)
        media_label = '电影' if media_type == 'movie' else '剧集'

        subject = f'【求片反馈】{title}'
        html_body = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                <h2 style="color: #333; margin-top: 0;">求片状态更新通知</h2>
                <p>您求片的 <strong>{media_label}</strong> 状态已更新：</p>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f5f5f5;">片名</td>
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>{title}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f5f5f5;">类型</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{media_label}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f5f5f5;">新状态</td>
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong style="color: {'#28a745' if new_status == 'approved' else '#dc3545' if new_status == 'rejected' else '#ffc107'};">{status_text}</strong></td>
                    </tr>
                </table>
                <p style="color: #666; font-size: 14px;">处理人：{admin_name}</p>
                <p style="color: #999; font-size: 12px; margin-top: 30px;">此邮件为系统自动发送，请勿直接回复。</p>
            </div>
        </div>
        '''

        return self.send_email(to_email, subject, html_body)

    def send_comment_notification(self, to_email, title, media_type, comment_content, commenter_name='管理员'):
        media_label = '电影' if media_type == 'movie' else '剧集'

        subject = f'【求片回复】{title}'
        html_body = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                <h2 style="color: #333; margin-top: 0;">收到新的评论回复</h2>
                <p>您求片的 <strong>{media_label}</strong> 收到了新评论：</p>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f5f5f5;">片名</td>
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>{title}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f5f5f5;">评论人</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{commenter_name}</td>
                    </tr>
                </table>
                <div style="background: #fff; border-left: 4px solid #007bff; padding: 12px; margin: 15px 0;">
                    <p style="margin: 0; color: #333;">{comment_content}</p>
                </div>
                <p style="color: #999; font-size: 12px; margin-top: 30px;">此邮件为系统自动发送，请勿直接回复。</p>
            </div>
        </div>
        '''

        return self.send_email(to_email, subject, html_body)

    def test_connection(self):
        if not self.enabled:
            return False, '邮件通知未启用'
        if not self.sender_email or not self.sender_password:
            return False, '发件人邮箱或密码未配置'
        try:
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.quit()
            return True, '连接成功'
        except Exception as exc:
            return False, f'连接失败: {str(exc)}'

    def send_invite_notification(self, to_email, invite_url, valid_hours, max_uses):
        subject = '【邀请注册】你收到了注册邀请'
        html_body = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                <h2 style="color: #333; margin-top: 0;">注册邀请通知</h2>
                <p>你收到了一个注册邀请，请点击下方链接完成注册：</p>
                <div style="background: #fff; border-left: 4px solid #007bff; padding: 12px; margin: 15px 0;">
                    <p style="margin: 0; word-break: break-all;"><a href="{invite_url}" style="color: #007bff;">{invite_url}</a></p>
                </div>
                <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f5f5f5;">有效时间</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{valid_hours}小时</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f5f5f5;">可用名额</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{max_uses}人</td>
                    </tr>
                </table>
                <p style="color: #999; font-size: 12px; margin-top: 30px;">此邮件为系统自动发送，请勿直接回复。</p>
            </div>
        </div>
        '''
        return self.send_email(to_email, subject, html_body)
