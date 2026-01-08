import fs from 'fs';
import https from 'https';

const cid = 5073;
const url = `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/${cid}/property/CanonicalSMILES/JSON`;

console.log(`Fetching ${url}...`);

https.get(url, (res) => {
    let data = Buffer.alloc(0);
    res.on('data', chunk => data = Buffer.concat([data, chunk]));
    res.on('end', () => {
        const body = data.toString();
        console.log(`Status: ${res.statusCode}`);
        console.log(`Body: ${body.substring(0, 200)}...`);
        try {
            const json = JSON.parse(body);
            console.log('CID:', json.IdentifierList?.CID?.[0]);
        } catch (e) {
            console.error('Parse error:', e);
        }
    });
}).on('error', e => console.error(e));
