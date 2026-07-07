const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

function getOpPath() {
    try {
        const p = execSync('which op', { encoding: 'utf8' }).trim();
        if (p) return p;
    } catch (e) {}
    
    const commonPaths = ['/opt/homebrew/bin/op', '/usr/local/bin/op', '/usr/bin/op'];
    for (const p of commonPaths) {
        if (fs.existsSync(p)) {
            return p;
        }
    }
    return 'op';
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

function main() {
    const dotenvPath = path.join(__dirname, '..', '..', '..', '..', '.env');
    const opBin = getOpPath();
    
    try {
        execSync(`"${opBin}" --version`, { stdio: 'ignore' });
    } catch (e) {
        console.error("Error: 1Password CLI (op) is not installed or not found.");
        process.exit(1);
    }
    
    console.log("Fetching 'AI Automation Global Setup' from 1Password 'Team' vault...");
    
    let stdout;
    try {
        stdout = execSync(`"${opBin}" item get "AI Automation Global Setup" --vault Team --format json`, { encoding: 'utf8' });
    } catch (e) {
        console.error(`Error fetching from 1Password: ${e.message}`);
        process.exit(1);
    }
    
    let data;
    try {
        data = JSON.parse(stdout);
    } catch (e) {
        console.error("Error: Could not parse JSON output from 1Password.");
        process.exit(1);
    }
    
    const fields = data.fields || [];
    let notesContent = null;
    for (const field of fields) {
        if (field.id === 'notesPlain') {
            notesContent = field.value || '';
            break;
        }
    }
    
    if (notesContent === null) {
        console.error("Error: Could not find 'notesPlain' field in 1Password item.");
        process.exit(1);
    }
    
    if (!fs.existsSync(dotenvPath)) {
        fs.writeFileSync(dotenvPath, '', 'utf8');
        console.log(`Created new .env file at ${dotenvPath}`);
    }
    
    const lines = notesContent.split(/\r?\n/);
    let updates = 0;
    
    for (let line of lines) {
        line = line.trim();
        if (!line || line.startsWith('#')) {
            continue;
        }
        
        if (line.includes('=')) {
            const firstEq = line.indexOf('=');
            let key = line.substring(0, firstEq).trim();
            let val = line.substring(firstEq + 1).trim();
            
            if (val.startsWith('"') && val.endsWith('"')) {
                val = val.substring(1, val.length - 1);
            } else if (val.startsWith("'") && val.endsWith("'")) {
                val = val.substring(1, val.length - 1);
            }
            
            if (key) {
                setKey(dotenvPath, key, val);
                updates++;
                console.log(`Synced ${key} to .env`);
            }
        }
    }
    
    console.log(`Successfully synced ${updates} environment variables from 1Password!`);
}

main();
