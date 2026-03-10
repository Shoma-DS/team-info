<?php

/**
 * Dify API クライアント（curl版）
 * 外部ライブラリ不要 - PHP標準のcurl拡張のみを使用
 */

class DifyClient
{
    protected string $api_key;
    protected string $base_url;

    public function __construct(string $api_key, string $base_url = 'https://api.dify.ai/v1/')
    {
        $this->api_key = $api_key;
        $this->base_url = rtrim($base_url, '/') . '/';
    }

    /**
     * HTTP リクエストを送信する（JSON形式）
     *
     * @param string      $method   HTTPメソッド（GET, POST, PATCH, DELETE）
     * @param string      $endpoint APIエンドポイント（例: 'chat-messages'）
     * @param array|null  $data     リクエストボディ（JSON）
     * @param array|null  $params   クエリパラメータ
     * @param bool        $stream   レスポンスをストリーミングするか
     * @return array      ['status' => int, 'body' => string]
     */
    protected function send_request(string $method, string $endpoint, ?array $data = null, ?array $params = null, bool $stream = false): array
    {
        $url = $this->base_url . $endpoint;

        // クエリパラメータを付与（nullの値は除外）
        if (!empty($params)) {
            $filteredParams = array_filter($params, fn($v) => $v !== null);
            if (!empty($filteredParams)) {
                $url .= '?' . http_build_query($filteredParams);
            }
        }

        $headers = [
            'Authorization: Bearer ' . $this->api_key,
            'Content-Type: application/json',
        ];

        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => !$stream,
            CURLOPT_CUSTOMREQUEST => strtoupper($method),
            CURLOPT_HTTPHEADER => $headers,
            CURLOPT_TIMEOUT => 60,
        ]);

        // ボディがある場合はJSONでセットする
        if ($data !== null) {
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        }

        $body = curl_exec($ch);
        $statusCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error = curl_error($ch);
        curl_close($ch);

        if ($error) {
            throw new RuntimeException('cURLエラー: ' . $error);
        }

        return [
            'status' => $statusCode,
            'body' => $body,
        ];
    }

    /**
     * マルチパート（ファイルアップロード）リクエストを送信する
     *
     * @param string     $endpoint  APIエンドポイント
     * @param array      $fields    テキストフィールド
     * @param array|null $files     ファイル情報の配列（'tmp_name', 'name' キーを持つ）
     * @return array     ['status' => int, 'body' => string]
     */
    protected function send_multipart_request(string $endpoint, array $fields, ?array $files = null): array
    {
        $url = $this->base_url . $endpoint;

        // CURLFILEを使ってファイルを付与する
        $postFields = $fields;
        if (!empty($files)) {
            foreach ($files as $i => $file) {
                $postFields['file' . ($i > 0 ? $i : '')] = new CURLFile($file['tmp_name'], '', $file['name']);
            }
        }

        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_POST => true,
            CURLOPT_POSTFIELDS => $postFields,
            CURLOPT_HTTPHEADER => [
                'Authorization: Bearer ' . $this->api_key,
                // Content-Type はcurlが自動でmultipart/form-dataにする
            ],
            CURLOPT_TIMEOUT => 60,
        ]);

        $body = curl_exec($ch);
        $statusCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error = curl_error($ch);
        curl_close($ch);

        if ($error) {
            throw new RuntimeException('cURLエラー: ' . $error);
        }

        return [
            'status' => $statusCode,
            'body' => $body,
        ];
    }

    /**
     * メッセージへのフィードバックを送信する
     */
    public function message_feedback(string $message_id, string $rating, string $user): array
    {
        $data = [
            'rating' => $rating,
            'user' => $user,
        ];
        return $this->send_request('POST', "messages/{$message_id}/feedbacks", $data);
    }

    /**
     * アプリケーションのパラメータを取得する
     */
    public function get_application_parameters(string $user): array
    {
        return $this->send_request('GET', 'parameters', null, ['user' => $user]);
    }

    /**
     * ファイルをアップロードする
     *
     * @param string $user  ユーザーID
     * @param array  $files ファイル情報の配列（$_FILES形式）
     */
    public function file_upload(string $user, array $files): array
    {
        return $this->send_multipart_request('files/upload', ['user' => $user], $files);
    }

    /**
     * テキストを音声に変換する
     */
    public function text_to_audio(string $text, string $user, bool $streaming = false): array
    {
        $data = [
            'text' => $text,
            'user' => $user,
            'streaming' => $streaming,
        ];
        return $this->send_request('POST', 'text-to-audio', $data);
    }

    /**
     * アプリのメタ情報を取得する
     */
    public function get_meta(string $user): array
    {
        return $this->send_request('GET', 'meta', null, ['user' => $user]);
    }
}

/**
 * テキスト補完APIクライアント
 */
class CompletionClient extends DifyClient
{
    /**
     * テキスト補完メッセージを作成する
     */
    public function create_completion_message(array $inputs, string $response_mode, string $user, ?array $files = null): array
    {
        $data = [
            'inputs' => $inputs,
            'response_mode' => $response_mode,
            'user' => $user,
            'files' => $files,
        ];
        return $this->send_request('POST', 'completion-messages', $data, null, $response_mode === 'streaming');
    }
}

/**
 * チャットAPIクライアント
 */
class ChatClient extends DifyClient
{
    /**
     * チャットメッセージを送信する
     */
    public function create_chat_message(array $inputs, string $query, string $user, string $response_mode = 'blocking', ?string $conversation_id = null, ?array $files = null): array
    {
        $data = [
            'inputs' => $inputs,
            'query' => $query,
            'user' => $user,
            'response_mode' => $response_mode,
            'files' => $files,
        ];
        if ($conversation_id !== null) {
            $data['conversation_id'] = $conversation_id;
        }
        return $this->send_request('POST', 'chat-messages', $data, null, $response_mode === 'streaming');
    }

    /**
     * メッセージへの返信候補を取得する
     */
    public function get_suggestions(string $message_id, string $user): array
    {
        return $this->send_request('GET', "messages/{$message_id}/suggested", null, ['user' => $user]);
    }

    /**
     * ストリーミングメッセージを停止する
     */
    public function stop_message(string $task_id, string $user): array
    {
        return $this->send_request('POST', "chat-messages/{$task_id}/stop", ['user' => $user]);
    }

    /**
     * 会話一覧を取得する
     */
    public function get_conversations(string $user, ?string $first_id = null, ?int $limit = null, ?bool $pinned = null): array
    {
        $params = [
            'user' => $user,
            'first_id' => $first_id,
            'limit' => $limit,
            'pinned' => $pinned,
        ];
        return $this->send_request('GET', 'conversations', null, $params);
    }

    /**
     * 会話のメッセージ履歴を取得する
     */
    public function get_conversation_messages(string $user, ?string $conversation_id = null, ?string $first_id = null, ?int $limit = null): array
    {
        $params = ['user' => $user];
        if ($conversation_id !== null)
            $params['conversation_id'] = $conversation_id;
        if ($first_id !== null)
            $params['first_id'] = $first_id;
        if ($limit !== null)
            $params['limit'] = $limit;

        return $this->send_request('GET', 'messages', null, $params);
    }

    /**
     * 会話名を変更する
     */
    public function rename_conversation(string $conversation_id, string $name, bool $auto_generate, string $user): array
    {
        $data = [
            'name' => $name,
            'user' => $user,
            'auto_generate' => $auto_generate,
        ];
        return $this->send_request('PATCH', "conversations/{$conversation_id}", $data);
    }

    /**
     * 会話を削除する
     */
    public function delete_conversation(string $conversation_id, string $user): array
    {
        return $this->send_request('DELETE', "conversations/{$conversation_id}", ['user' => $user]);
    }

    /**
     * 音声をテキストに変換する
     */
    public function audio_to_text(array $audio_file, string $user): array
    {
        return $this->send_multipart_request('audio-to-text', ['user' => $user], [$audio_file]);
    }
}

/**
 * ワークフローAPIクライアント
 */
class WorkflowClient extends DifyClient
{
    /**
     * ワークフローを実行する
     */
    public function run(array $inputs, string $response_mode, string $user): array
    {
        $data = [
            'inputs' => $inputs,
            'response_mode' => $response_mode,
            'user' => $user,
        ];
        return $this->send_request('POST', 'workflows/run', $data);
    }

    /**
     * ワークフローを停止する
     */
    public function stop(string $task_id, string $user): array
    {
        return $this->send_request('POST', "workflows/tasks/{$task_id}/stop", ['user' => $user]);
    }
}
