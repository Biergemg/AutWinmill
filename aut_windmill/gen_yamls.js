const fs = require('fs');
const path = require('path');

const root = 'f/einstein_kids';
const out = 'scripts_yaml';
if (!fs.existsSync(out)) fs.mkdirSync(out);

const folders = ['shared', 'moms', 'therapists'];

folders.forEach(fld => {
    const dir = path.join(root, fld);
    if (fs.existsSync(dir)) {
        fs.readdirSync(dir).filter(f => f.endsWith('.py')).forEach(scriptFile => {
            const content = fs.readFileSync(path.join(dir, scriptFile), 'utf8');
            const metaPath = path.join(dir, scriptFile.replace('.py', '.script.yaml'));

            let summary = scriptFile;
            let description = '';

            if (fs.existsSync(metaPath)) {
                const metaRaw = fs.readFileSync(metaPath, 'utf8');
                const sMatch = metaRaw.match(/summary:\s*"(.*)"/);
                const dMatch = metaRaw.match(/description:\s*"(.*)"/);
                if (sMatch) summary = sMatch[1];
                if (dMatch) description = dMatch[1];
            }

            const yaml = `summary: "${summary}"
description: "${description}"
language: python3
content: |
${content.split('\n').map(line => '  ' + line).join('\n')}
`;
            fs.writeFileSync(path.join(out, scriptFile.replace('.py', '.yaml')), yaml);
            console.log(`Generated ${scriptFile.replace('.py', '.yaml')}`);
        });
    }
});
