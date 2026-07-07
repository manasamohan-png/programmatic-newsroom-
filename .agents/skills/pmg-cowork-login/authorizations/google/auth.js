const fs = require('fs');
const path = require('path');
const http = require('http');
const { execSync } = require('child_process');

// Load environment variables
const dotenvPath = path.join(__dirname, '..', '..', '..', '..', '..', '.env');
let envContent = '';
if (fs.existsSync(dotenvPath)) {
    envContent = fs.readFileSync(dotenvPath, 'utf8');
}

function getEnvVar(key) {
    const lines = envContent.split(/\r?\n/);
    for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed && !trimmed.startsWith('#') && trimmed.includes('=')) {
            const firstEq = trimmed.indexOf('=');
            const k = trimmed.substring(0, firstEq).trim();
            let v = trimmed.substring(firstEq + 1).trim();
            if (v.startsWith('"') && v.endsWith('"')) {
                v = v.substring(1, v.length - 1);
            } else if (v.startsWith("'") && v.endsWith("'")) {
                v = v.substring(1, v.length - 1);
            }
            if (k === key) return v;
        }
    }
    return null;
}

function setKey(envPath, key, val) {
    let content = '';
    if (fs.existsSync(envPath)) {
        content = fs.readFileSync(envPath, 'utf8');
    }
    
    const lines = content.split(/\r?\n/);
    let found = false;
    const newLines = lines.map(line => {
        const trimmed = line.trim();
        if (trimmed && !trimmed.startsWith('#') && trimmed.includes('=')) {
            const firstEq = trimmed.indexOf('=');
            const k = trimmed.substring(0, firstEq).trim();
            if (k === key) {
                found = true;
                return `${key}="${val}"`;
            }
        }
        return line;
    });
    
    if (!found) {
        if (newLines.length > 0 && newLines[newLines.length - 1] !== '') {
            newLines.push('');
        }
        newLines.push(`${key}="${val}"`);
    }
    
    fs.writeFileSync(envPath, newLines.join('\n'), 'utf8');
}

const CLIENT_ID = getEnvVar('GOOGLE_CLIENT_ID');
const CLIENT_SECRET = getEnvVar('GOOGLE_CLIENT_SECRET');
const REDIRECT_URI = 'http://127.0.0.1:8088/googlecallback';

const SCOPES = [
    'https://mail.google.com/',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/userinfo.email',
];
const SCOPE = SCOPES.join(' ');

if (!CLIENT_ID || !CLIENT_SECRET) {
    console.error("Error: GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not found in .env file.");
    process.exit(1);
}

const server = http.createServer(async (req, res) => {
    const reqUrl = new URL(req.url, `http://${req.headers.host}`);
    if (reqUrl.pathname === '/googlecallback') {
        const code = reqUrl.searchParams.get('code');
        if (code) {
            res.writeHead(200, { 'Content-Type': 'text/html' });
            
            // Exchange code for token
            const tokenUrl = "https://oauth2.googleapis.com/token";
            const params = new URLSearchParams();
            params.append('grant_type', 'authorization_code');
            params.append('client_id', CLIENT_ID);
            params.append('client_secret', CLIENT_SECRET);
            params.append('redirect_uri', REDIRECT_URI);
            params.append('code', code);
            
            try {
                const response = await fetch(tokenUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded'
                    },
                    body: params.toString()
                });
                
                if (!response.ok) {
                    const errText = await response.text();
                    throw new Error(`HTTP error! status: ${response.status}, body: ${errText}`);
                }
                
                const tokenData = await response.json();
                const accessToken = tokenData.access_token;
                const refreshToken = tokenData.refresh_token;
                
                if (refreshToken) {
                    setKey(dotenvPath, 'GOOGLE_REFRESH_TOKEN', refreshToken);
                    console.log("Successfully retrieved and saved GOOGLE_REFRESH_TOKEN to .env");
                    res.end("<html><body><h1>Authorization Successful!</h1><p>You can close this window now.</p><script>window.close();</script></body></html>");
                } else {
                    if (accessToken) {
                        console.log("Got access token but no refresh token. Make sure you haven't authorized this app previously without revoking, or assure access_type=offline and prompt=consent.");
                    }
                    console.log("Failed to get refresh token from response.");
                    console.log(tokenData);
                    res.end("<html><body><h1>Authorization Completed without Refresh Token</h1><p>See terminal for details.</p></body></html>");
                }
            } catch (e) {
                console.error(`Error fetching token: ${e.message}`);
                res.end("<html><body><h1>Authorization Failed</h1><p>Check terminal for details.</p></body></html>");
            }
            
            setTimeout(() => {
                server.close(() => {
                    console.log("Server shut down.");
                    process.exit(0);
                });
            }, 1000);
        } else {
            res.writeHead(400, { 'Content-Type': 'text/html' });
            res.end("<html><body><h1>Authorization Failed</h1><p>No code provided.</p></body></html>");
            setTimeout(() => {
                server.close(() => {
                    console.log("Server shut down.");
                    process.exit(1);
                });
            }, 1000);
        }
    } else {
        res.writeHead(404);
        res.end();
    }
});

server.listen(8088, () => {
    const authParams = new URLSearchParams({
        client_id: CLIENT_ID,
        redirect_uri: REDIRECT_URI,
        response_type: 'code',
        scope: SCOPE,
        access_type: 'offline',
        prompt: 'consent'
    });
    const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?${authParams.toString()}`;
    
    console.log(`Starting local server to handle callback on ${REDIRECT_URI}...`);
    console.log("Opening browser for authorization...");
    
    // Open browser
    try {
        const openCmd = process.platform === 'darwin' ? 'open' : process.platform === 'win32' ? 'start' : 'xdg-open';
        require('child_process').exec(`${openCmd} "${authUrl}"`);
    } catch (e) {
        console.log(`Please open this URL in your browser:\n${authUrl}`);
    }
});
