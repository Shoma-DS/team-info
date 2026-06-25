#!/usr/bin/env python3
# Zoom会議自動作成、LINE/Discord通知、カレンダー更新を統合処理

import json
import sys
import re
import os
import subprocess
from datetime import datetime
from typing import Optional, Dict, List, Any
import urllib.request
import urllib.error

def load_json_file(path: str) -> dict:
    """JSONファイルを読み込む"""
    expanded_path = os.path.expandvars(path)
    with open(expanded_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_uid_from_description(description: str) -> Optional[str]:
    """説明欄からuid または ユーザーID を抽出"""
    if not description:
        return None
    uid_match = re.search(r'uid[：:]\s*(\S+)', description)
    if uid_match:
        return uid_match.group(1)
    user_id_match = re.search(r'ユーザーID[：:]\s*(\S+)', description)
    if user_id_match:
        return user_id_match.group(1)
    return None

def extract_zoom_url_from_description(description: str) -> Optional[str]:
    """説明欄から既存の Zoom URL を抽出"""
    if not description:
        return None
    zoom_match = re.search(r'https://[\w\.]*zoom\.us/j/[\w?=&]+', description)
    if zoom_match:
        return zoom_match.group(0)
    return None

def extract_zoom_meeting_id(description: str) -> Optional[str]:
    """説明欄から Zoom Meeting ID を抽出"""
    if not description:
        return None
    meeting_id_match = re.search(r'Meeting ID[：:]\s*([\d\s]+)', description)
    if meeting_id_match:
        return meeting_id_match.group(1).replace(' ', '')
    return None

def send_discord_message(webhook_url: str, content: str = None, embeds: List[Dict] = None) -> bool:
    """Discord に メッセージを送信"""
    payload = {}
    if content:
        payload['content'] = content
    if embeds:
        payload['embeds'] = embeds
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            return response.status == 204
    except urllib.error.URLError as e:
        print(f"Discord送信エラー: {e}", file=sys.stderr)
        return False

def send_line_message(line_url: str, token: str, uid: str, message: str) -> bool:
    """LINE / ProLine へメッセージを送信"""
    if not line_url or not uid:
        return False
    try:
        payload = {
            'user_id': uid,
            'message': message
        }
        if token:
            payload['token'] = token
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            line_url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            return response.status == 200
    except urllib.error.URLError as e:
        print(f"LINE送信エラー: {e}", file=sys.stderr)
        return False

def process_events(events: List[Dict], settings: Dict, discord_webhook: str, line_url: str = None, line_token: str = None) -> Dict:
    """カレンダーイベントを処理"""
    results = {
        'success': True,
        'events_processed': 0,
        'discord_messages_sent': 0,
        'line_messages_sent': 0,
        'events': []
    }

    if not events:
        embed = {
            'title': '📅 本日のスケジュール',
            'description': '予定がありません',
            'color': 9807270
        }
        if send_discord_message(discord_webhook, embeds=[embed]):
            results['discord_messages_sent'] += 1
        return results

    all_day_events = []
    timed_events = []

    for event in events:
        event_info = {
            'title': event.get('title', ''),
            'start_time': event.get('start', ''),
            'end_time': event.get('end', ''),
            'description': event.get('description', ''),
            'all_day': event.get('allDay', False)
        }
        if event_info['all_day']:
            all_day_events.append(event_info)
        else:
            timed_events.append(event_info)

    overview_embed = {
        'title': '📅 本日のスケジュール',
        'description': f'**{len(all_day_events)} 件の終日予定 + {len(timed_events)} 件の時刻付き予定**',
        'color': 3447003,
        'fields': []
    }

    if all_day_events:
        all_day_text = '\n'.join([f"• {e['title']}" for e in all_day_events])
        overview_embed['fields'].append({
            'name': '終日予定',
            'value': all_day_text,
            'inline': False
        })

    if timed_events:
        timed_text = '\n'.join([
            f"{'🔗' if extract_zoom_url_from_description(e['description']) else '📅'} {e['start_time']} {e['title']}"
            for e in timed_events
        ])
        overview_embed['fields'].append({
            'name': '時刻付き予定',
            'value': timed_text,
            'inline': False
        })

    if send_discord_message(discord_webhook, embeds=[overview_embed]):
        results['discord_messages_sent'] += 1

    for event in events:
        title = event.get('title', '')
        start_time = event.get('start', '')
        end_time = event.get('end', '')
        description = event.get('description', '')

        zoom_url = extract_zoom_url_from_description(description)
        uid = extract_uid_from_description(description)
        meeting_id = extract_zoom_meeting_id(description)

        detail_embed = {
            'title': title,
            'description': f'{start_time} - {end_time}',
            'color': 3447003,
            'fields': []
        }

        if description:
            desc_preview = description[:300]
            if len(description) > 300:
                desc_preview += '...'
            detail_embed['fields'].append({
                'name': '説明',
                'value': desc_preview,
                'inline': False
            })

        if zoom_url:
            detail_embed['fields'].append({
                'name': 'Zoom リンク',
                'value': f'```\n{zoom_url}\n```',
                'inline': False
            })

        if meeting_id:
            detail_embed['fields'].append({
                'name': 'ミーティング ID',
                'value': meeting_id,
                'inline': False
            })

        line_sent = False
        if uid and zoom_url and line_url:
            message = f'本日 {start_time} の「{title}」の会議リンクをお送りします。\n\n{zoom_url}\n\nよろしくお願いいたします。'
            if send_line_message(line_url, line_token, uid, message):
                line_sent = True
                results['line_messages_sent'] += 1

        if line_sent:
            detail_embed['fields'].append({
                'name': 'LINE送信',
                'value': '済み',
                'inline': True
            })

        if send_discord_message(discord_webhook, embeds=[detail_embed]):
            results['discord_messages_sent'] += 1

        results['events_processed'] += 1
        results['events'].append({
            'title': title,
            'uid': uid,
            'zoom_url': zoom_url,
            'line_sent': line_sent
        })

    return results

def main():
    settings_path = os.environ.get('SETTINGS_PATH', '')
    if settings_path:
        settings = load_json_file(settings_path)
    else:
        settings = {'discord_webhook_file': '', 'calendar_id': 'syouma1674@gmail.com', 'timezone': 'Asia/Tokyo'}

    discord_webhook = os.environ.get('DISCORD_DAILY_WEBHOOK', '')
    if not discord_webhook and settings.get('discord_webhook_file'):
        try:
            webhook_data = load_json_file(settings['discord_webhook_file'])
            discord_webhook = webhook_data.get('webhook_url', '')
        except:
            pass

    line_url = os.environ.get('PROLINE_MESSAGE_SENDER_URL', '')
    line_token = os.environ.get('PROLINE_MESSAGE_SENDER_TOKEN', '')
    if not line_url:
        line_url = os.environ.get('LINE_MESSAGE_SENDER_URL', '')
        line_token = os.environ.get('LINE_MESSAGE_SENDER_TOKEN', '')

    try:
        calendar_data = json.load(sys.stdin)
        events = calendar_data.get('events', [])
    except json.JSONDecodeError:
        print("エラー: カレンダーデータのJSON形式が不正です", file=sys.stderr)
        sys.exit(1)

    results = process_events(events, settings, discord_webhook, line_url, line_token)
    print(json.dumps(results, ensure_ascii=False, indent=2))

    if not results['success']:
        sys.exit(1)

if __name__ == '__main__':
    main()
