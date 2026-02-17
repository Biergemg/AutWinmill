const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

const TOKEN = 'TrAPVETlPnXUeaFkGpgj9L0yoq81F2h7';
const BASE_URL = 'http://localhost:8000/api';
const WORKSPACE = 'admins';

async function deployScript(filePath, metadataPath) {
    try {
        const code = fs.readFileSync(filePath, 'utf8');
        const metadataRaw = fs.readFileSync(metadataPath, 'utf8');
        const metadata = yaml.load(metadataRaw);

        const relativePath = filePath.replace(/\\/g, '/').split('f/')[1].replace('.py', '');
        const scriptPath = `u/admin/${relativePath}`;

        console.log(`Deploying ${scriptPath}...`);

        const payload = {
            path: scriptPath,
            content: code,
            language: 'python3',
            summary: metadata.summary || path.basename(filePath),
            description: metadata.description || '',
            schema: metadata.schema || {},
            kind: 'script'
        };

        const response = await fetch(`${BASE_URL}/w/${WORKSPACE}/scripts/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${TOKEN}`
            },
            body: JSON.stringify(payload)
        });

        if (response.ok || response.status === 201) {
            console.log(`✅ Success: ${scriptPath}`);
        } else if (response.status === 400) {
            // Already exists? Let's try update if it's the right error
            const text = await response.text();
            if (text.includes('already exists')) {
                console.log(`ℹ️ ${scriptPath} already exists, attempting update... (needs different endpoint)`);
                // For now just skip or provide update logic if needed
            } else {
                console.log(`❌ Error: ${scriptPath} - ${response.status} ${text}`);
            }
        } else {
            const text = await response.text();
            console.log(`❌ Error: ${scriptPath} - ${response.status} ${text}`);
        }
    } catch (err) {
        console.error(`Error processing ${filePath}: ${err.message}`);
    }
}

async function main() {
    const root = path.join(__dirname, 'f', 'einstein_kids');
    const folders = ['shared', 'moms', 'therapists'];

    for (const folder of folders) {
        const dir = path.join(root, folder);
        if (!fs.existsSync(dir)) continue;

        const files = fs.readdirSync(dir);
        for (const file of files) {
            if (file.endsWith('.py')) {
                const filePath = path.join(dir, file);
                const metadataPath = filePath.replace('.py', '.script.yaml');
                if (fs.existsSync(metadataPath)) {
                    await deployScript(filePath, metadataPath);
                }
            }
        }
    }
}

main().catch(console.error);
