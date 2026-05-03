# X APIで自分のアカウントの投稿メトリクスを取得しNeon PostgreSQLに保存するスクリプト。
# accounts_config.jsonからアカウント一覧を読み込み、投稿後168時間以内の投稿を対象に
# impression/like/retweet/bookmark/replyをスナップショットとして記録する。
# 実行後に今日のAPI使用コスト概算を表示する。

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import psycopg2
import tweepy

SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "accounts_config.json"
SNAPSHOT_WINDOW_HOURS = 168  # 1週間
COST_PER_READ = 0.001  # $0.001/件（自分の投稿読み取り）
TWEET_FIELDS = ["created_at", "public_metrics", "text"]


def load_config():
    if not CONFIG_FILE.exists():
        print(f"❌ 設定ファイルが見つかりません: {CONFIG_FILE}", file=sys.stderr)
        sys.exit(1)

    try:
        text = CONFIG_FILE.read_text(encoding="utf-8")
        json_text = "\n".join(
            line for line in text.splitlines() if not line.lstrip().startswith("//")
        )
        config = json.loads(json_text)
    except json.JSONDecodeError as exc:
        print(f"❌ accounts_config.json の書き方が正しくありません: {exc}", file=sys.stderr)
        sys.exit(1)

    accounts = config.get("accounts")
    if not isinstance(accounts, list):
        print("❌ accounts_config.json に accounts 配列がありません", file=sys.stderr)
        sys.exit(1)
    return config


def get_db_conn():
    url = os.environ.get("NEON_DATABASE_URL")
    if not url:
        print("❌ NEON_DATABASE_URL が設定されていません", file=sys.stderr)
        sys.exit(1)
    try:
        return psycopg2.connect(url)
    except psycopg2.Error as exc:
        print(f"❌ Neon PostgreSQL に接続できません: {exc}", file=sys.stderr)
        sys.exit(1)


def upsert_account(cur, x_username, display_name):
    cur.execute(
        """
        INSERT INTO accounts (x_username, display_name)
        VALUES (%s, %s)
        ON CONFLICT (x_username) DO UPDATE SET display_name = EXCLUDED.display_name
        RETURNING account_id
        """,
        (x_username, display_name),
    )
    return cur.fetchone()[0]


def upsert_tweet(cur, tweet_id, account_id, content, posted_at, post_type):
    cur.execute(
        """
        INSERT INTO tweets (tweet_id, account_id, content, posted_at, post_type)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (tweet_id) DO UPDATE
        SET account_id = EXCLUDED.account_id,
            content = EXCLUDED.content,
            posted_at = EXCLUDED.posted_at,
            post_type = EXCLUDED.post_type
        """,
        (tweet_id, account_id, content, posted_at, post_type),
    )


def insert_snapshot(cur, tweet_id, hours_after, metrics):
    cur.execute(
        """
        INSERT INTO tweet_metrics_snapshots
          (tweet_id, snapshot_at, hours_after_post,
           impression_count, like_count, retweet_count, bookmark_count, reply_count)
        VALUES (%s, NOW(), %s, %s, %s, %s, %s, %s)
        """,
        (
            tweet_id,
            round(hours_after, 2),
            metrics.get("impression_count"),
            metrics.get("like_count"),
            metrics.get("retweet_count"),
            metrics.get("bookmark_count"),
            metrics.get("reply_count"),
        ),
    )


def build_client(api_key, api_secret, access_token, access_token_secret):
    return tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
        wait_on_rate_limit=True,
    )


def fetch_recent_tweets(client, user_id, since):
    tweets = []
    pagination_token = None

    while True:
        response = client.get_users_tweets(
            id=user_id,
            start_time=since,
            max_results=100,
            tweet_fields=TWEET_FIELDS,
            user_auth=True,
            pagination_token=pagination_token,
        )

        page_tweets = response.data or []
        tweets.extend(page_tweets)

        meta = response.meta or {}
        pagination_token = meta.get("next_token")
        if not pagination_token:
            return tweets


def collect_account(account_cfg, conn):
    env_token = account_cfg["token_env"]
    env_secret = account_cfg["token_secret_env"]
    access_token = os.environ.get(env_token)
    access_token_secret = os.environ.get(env_secret)

    if not access_token or not access_token_secret:
        print(
            f"⚠️  {account_cfg['x_username']}: 環境変数 {env_token} / {env_secret} が未設定のためスキップ",
            file=sys.stderr,
        )
        return 0

    api_key = os.environ.get("X_API_KEY")
    api_secret = os.environ.get("X_API_SECRET")
    if not api_key or not api_secret:
        print("❌ X_API_KEY / X_API_SECRET が設定されていません", file=sys.stderr)
        sys.exit(1)

    client = build_client(api_key, api_secret, access_token, access_token_secret)

    try:
        # OAuth 1.0a のユーザー文脈で自分のユーザーIDを取得する。
        me = client.get_me(user_fields=["name", "username"], user_auth=True)
        if not me.data:
            print(f"❌ {account_cfg['x_username']}: ユーザー情報取得失敗", file=sys.stderr)
            return 0

        user_id = me.data.id
        actual_username = me.data.username or account_cfg["x_username"]
        display_name = me.data.name or actual_username
        if actual_username.lower() != account_cfg["x_username"].lower():
            print(
                f"⚠️  設定の x_username と認証アカウントが違います: "
                f"{account_cfg['x_username']} -> {actual_username}",
                file=sys.stderr,
            )

        now = datetime.now(timezone.utc)
        since = now - timedelta(hours=SNAPSHOT_WINDOW_HOURS)
        tweets = fetch_recent_tweets(client, user_id, since)
        read_count = len(tweets)

        with conn.cursor() as cur:
            account_id = upsert_account(cur, actual_username, display_name)

            for tweet in tweets:
                posted_at = tweet.created_at
                if posted_at is None:
                    continue

                hours_after = (now - posted_at).total_seconds() / 3600
                if hours_after > SNAPSHOT_WINDOW_HOURS:
                    continue

                # スレッド判定（簡易）
                post_type = "single"
                if tweet.text.startswith("@"):
                    post_type = "thread"
                elif len(tweet.text) > 200:
                    post_type = "long"

                upsert_tweet(cur, tweet.id, account_id, tweet.text, posted_at, post_type)

                metrics = {}
                if tweet.public_metrics:
                    metrics.update(tweet.public_metrics)

                insert_snapshot(cur, tweet.id, hours_after, metrics)

            conn.commit()
    except tweepy.TooManyRequests as exc:
        conn.rollback()
        print(f"❌ {account_cfg['x_username']}: API制限に達しました: {exc}", file=sys.stderr)
        return 0
    except (
        tweepy.BadRequest,
        tweepy.Forbidden,
        tweepy.NotFound,
        tweepy.TwitterServerError,
        tweepy.Unauthorized,
        tweepy.TweepyException,
    ) as exc:
        conn.rollback()
        print(f"❌ {account_cfg['x_username']}: X API エラー: {exc}", file=sys.stderr)
        return 0
    except psycopg2.Error as exc:
        conn.rollback()
        print(f"❌ {account_cfg['x_username']}: DB書き込みエラー: {exc}", file=sys.stderr)
        return 0

    print(f"✅ {actual_username}: {read_count} 件処理完了")
    return read_count


def main():
    config = load_config()
    conn = get_db_conn()

    total_reads = 0
    try:
        for account in config["accounts"]:
            print(f"\n▶ {account['x_username']} を処理中...")
            total_reads += collect_account(account, conn)
    finally:
        conn.close()

    cost_usd = total_reads * COST_PER_READ
    cost_jpy = cost_usd * 150
    print(f"\n💰 今回のAPI使用コスト概算: ${cost_usd:.4f}（約{cost_jpy:.1f}円）/ 取得件数: {total_reads}件")


if __name__ == "__main__":
    main()
