from __future__ import annotations

import logging
from datetime import datetime

from .ip_utils import extract_ip_address, is_ipv4, is_ipv6

logger = logging.getLogger(__name__)


class SessionTracker:
    def __init__(self, db_manager, emby_client, location_lookup, login_abnormality_checker, whitelist_resolver):
        self.db = db_manager
        self.emby = emby_client
        self.location_lookup = location_lookup
        self.login_abnormality_checker = login_abnormality_checker
        self.whitelist_resolver = whitelist_resolver

    def detect_new_sessions(self, active_sessions, current_sessions):
        for session_id, session in current_sessions.items():
            if session_id not in active_sessions:
                self.record_session_start(active_sessions, session)

    def detect_ended_sessions(self, active_sessions, current_sessions):
        if not current_sessions and active_sessions:
            logger.debug('Emby返回空会话但存在活跃会话(%d个)，跳过结束检测避免误判', len(active_sessions))
            return
        ended = set(active_sessions.keys()) - set(current_sessions.keys())
        for session_id in ended:
            self.record_session_end(active_sessions, session_id)

    def update_session_positions(self, active_sessions, current_sessions):
        for session_id, session in current_sessions.items():
            if session_id in active_sessions:
                play_state = session.get('PlayState', {})
                position_ticks = play_state.get('PositionTicks')
                is_paused = play_state.get('IsPaused', False)
                last_position_ticks = active_sessions[session_id].get('last_position_ticks', None)

                if position_ticks is not None and last_position_ticks is not None:
                    if position_ticks > last_position_ticks:
                        delta_ticks = position_ticks - last_position_ticks
                        delta_seconds = round(delta_ticks / 10000000)
                        current_duration = active_sessions[session_id].get('playback_duration', 0)
                        active_sessions[session_id]['playback_duration'] = current_duration + delta_seconds

                if position_ticks is not None:
                    active_sessions[session_id]['last_position_ticks'] = position_ticks

                was_paused = active_sessions[session_id].get('is_paused', False)
                active_sessions[session_id]['is_paused'] = is_paused
                if is_paused and not was_paused:
                    active_sessions[session_id]['pause_started_at'] = datetime.now()
                elif not is_paused and was_paused:
                    pause_started_at = active_sessions[session_id].get('pause_started_at')
                    if pause_started_at:
                        paused_seconds = int((datetime.now() - pause_started_at).total_seconds())
                        total_paused = active_sessions[session_id].get('total_paused_seconds', 0)
                        active_sessions[session_id]['total_paused_seconds'] = total_paused + paused_seconds
                    active_sessions[session_id]['pause_started_at'] = None

    def record_session_start(self, active_sessions, session):
        try:
            user_id = session['UserId']
            user_info = self.emby.get_user_info(user_id)
            ip_address = extract_ip_address(session.get('RemoteEndPoint', ''))
            username = user_info.get('Name', '未知用户').strip()
            is_whitelist = self.whitelist_resolver(username)
            media_item = session.get('NowPlayingItem', {})
            media_name = self.emby.parse_media_info(media_item)
            location = self.location_lookup(ip_address)

            play_state = session.get('PlayState', {})
            initial_position_ticks = play_state.get('PositionTicks')
            is_paused = play_state.get('IsPaused', False)

            playback_start_ticks = play_state.get('PlaybackStartTimeTicks')
            if playback_start_ticks and playback_start_ticks > 0:
                start_time = datetime.fromtimestamp(playback_start_ticks / 10000000)
            else:
                start_time = datetime.now()

            session_data = {
                'session_id': session['Id'],
                'user_id': user_id,
                'username': username,
                'ip': ip_address,
                'device': session.get('DeviceName', '未知设备'),
                'client': session.get('Client', '未知客户端'),
                'media': media_name,
                'start_time': start_time,
                'location': location,
                'playback_duration': 0,
                'last_position_ticks': initial_position_ticks,
                'is_paused': is_paused,
                'pause_started_at': datetime.now() if is_paused else None,
                'total_paused_seconds': 0,
            }

            self.db.record_session_start(session_data)
            active_sessions[session['Id']] = session_data

            ip_type = 'IPv6' if is_ipv6(ip_address) else 'IPv4' if is_ipv4(ip_address) else '未知'
            if is_whitelist:
                logger.info(
                    '[▶] %s (白名单) | 设备: %s | IP: %s (%s) | 位置: %s | 内容: %s',
                    username,
                    session_data['device'],
                    ip_address,
                    ip_type,
                    location,
                    session_data['media'],
                )
            else:
                logger.info(
                    '[▶] %s | 设备: %s | IP: %s (%s) | 位置: %s | 内容: %s',
                    username,
                    session_data['device'],
                    ip_address,
                    ip_type,
                    location,
                    session_data['media'],
                )

            self.login_abnormality_checker(user_id, ip_address)
        except KeyError as e:
            logger.error('❌ 会话数据缺失关键字段: %s', e)
        except Exception as e:
            logger.error('❌ 会话记录失败: %s', e)

    def record_session_end(self, active_sessions, session_id):
        try:
            session_data = active_sessions[session_id]
            end_time = datetime.now()
            duration = session_data.get('playback_duration', 0)
            if duration == 0:
                wall_duration = int((end_time - session_data['start_time']).total_seconds())
                total_paused = session_data.get('total_paused_seconds', 0)
                pause_started_at = session_data.get('pause_started_at')
                if pause_started_at:
                    total_paused += int((end_time - pause_started_at).total_seconds())
                duration = max(wall_duration - total_paused, 0)

            self.db.record_session_end(session_id, end_time, duration)
            logger.info('[■] %s | 时长: %s分%s秒', session_data['username'], duration // 60, duration % 60)
            del active_sessions[session_id]
        except KeyError:
            logger.warning('⚠️ 会话 %s 已不存在', session_id)
        except Exception as e:
            logger.error('❌ 结束记录失败: %s', e)
