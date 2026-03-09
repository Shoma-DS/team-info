require('dotenv').config();
const express = require('express');
const crypto = require('crypto');
const axios = require('axios');
const fs = require('fs');

const app = express();
const port = 8080;

// Canva OAuth2 endpoints
const AUTHORIZE_URL = 'https://www.canva.com/api/oauth/authorize';
const TOKEN_URL = 'https://api.canva.com/rest/v1/oauth/token';

// Configure these securely or via environment variables (.env)
const CLIENT_ID = process.env.CANVA_CLIENT_ID;
const CLIENT_SECRET = process.env.CANVA_CLIENT_SECRET;
const REDIRECT_URI = `http://localhost:${port}/callback`;

if (!CLIENT_ID || !CLIENT_SECRET) {
    console.error('エラー: 環境変数 CANVA_CLIENT_ID と CANVA_CLIENT_SECRET が設定されていません。');
    console.error('.env ファイルを作成するか、環境変数をエクスポートしてください。');
    process.exit(1);
}

// Scopes required for MCP and design generation
const SCOPES = 'design:content:read design:content:write asset:read asset:write';

// Generate PKCE code verifier and challenge
const codeVerifier = crypto.randomBytes(32).toString('base64url');
const codeChallenge = crypto.createHash('sha256').update(codeVerifier).digest('base64url');

console.log('--- Canva API OAuth 2.0 PKCE 認証サーバー ---');

app.get('/', (req, res) => {
    const params = new URLSearchParams({
        response_type: 'code',
        client_id: CLIENT_ID,
        redirect_uri: REDIRECT_URI,
        scope: SCOPES,
        code_challenge: codeChallenge,
        code_challenge_method: 'S256'
    });

    const authUrl = `${AUTHORIZE_URL}?${params.toString()}`;
    res.send(`
        <html>
            <body style="font-family: sans-serif; padding: 20px;">
                <h2>Canva API 認証</h2>
                <p>以下のリンクをクリックしてCanvaでアプリを承認してください：</p>
                <a href="${authUrl}" style="padding: 10px 20px; background: #8b3dff; color: white; text-decoration: none; border-radius: 5px;">Canvaで認証する</a>
            </body>
        </html>
    `);
});

app.get('/callback', async (req, res) => {
    const { code, error } = req.query;

    if (error) {
        return res.send(`認証エラー: ${error}`);
    }

    if (!code) {
        return res.send('コードが取得できませんでした。');
    }

    try {
        const credentials = Buffer.from(`${CLIENT_ID}:${CLIENT_SECRET}`).toString('base64');

        const response = await axios.post(TOKEN_URL, new URLSearchParams({
            grant_type: 'authorization_code',
            code: code,
            code_verifier: codeVerifier,
            redirect_uri: REDIRECT_URI
        }).toString(), {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': `Basic ${credentials}`
            }
        });

        console.log('\\n✅ 認証成功！アクセストークンを取得しました：\\n');
        console.log(response.data);
        console.log('\\n※ この json オブジェクト内にある "access_token" を使用します。有効期限やリフレッシュトークンも含まれています。');

        res.send('認証が正常に完了しました！このウィンドウを閉じて、ターミナルを確認してください。');

        // Output token to a file to be easily retrieved
        fs.writeFileSync('canva_tokens.json', JSON.stringify(response.data, null, 2));
        console.log('✅ トークンを canva_tokens.json に保存しました。');

        // Stop the server
        setTimeout(() => process.exit(0), 1000);
    } catch (err) {
        console.error('トークン取得エラー:', err.response ? err.response.data : err.message);
        res.send('トークンの取得に失敗しました。ターミナルを確認してください。');
    }
});

app.listen(port, () => {
    console.log(\`サーバーが起動しました: http://localhost:\${port}\`);
    console.log(\`ブラウザで上記のURLを開いて、認証プロセスを開始してください。\`);
});
