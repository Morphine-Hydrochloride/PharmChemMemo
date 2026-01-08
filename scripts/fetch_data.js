import fs from 'fs';
import path from 'path';
import https from 'https';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DATA_FILE = path.join(__dirname, '../src/data.json');

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Simplified fetch helper mimicking debug_fetch.js
function fetch(url) {
    return new Promise((resolve, reject) => {
        const req = https.get(url, (res) => {
            let data = Buffer.alloc(0);
            res.on('data', chunk => data = Buffer.concat([data, chunk]));
            res.on('end', () => {
                if (res.statusCode >= 200 && res.statusCode < 300) {
                    resolve(data.toString());
                } else {
                    reject(new Error(`Status: ${res.statusCode}`));
                }
            });
        });
        req.on('error', reject);
    });
}

// Retry wrapper
async function fetchWithBackoff(url, retries = 3) {
    for (let i = 0; i < retries; i++) {
        try {
            return await fetch(url);
        } catch (e) {
            if (i === retries - 1) throw e;
            await delay(1000 * (i + 1));
        }
    }
}

async function getSmilesForName(name) {
    try {
        // 1. Get CID
        const cidUrl = `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/${encodeURIComponent(name)}/cids/JSON`;
        const cidJson = await fetchWithBackoff(cidUrl);
        const cidData = JSON.parse(cidJson);
        const cid = cidData.IdentifierList?.CID?.[0];

        if (!cid) return null;

        // 2. Get SMILES
        const smileUrl = `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/${cid}/property/CanonicalSMILES/JSON`;
        const smileJson = await fetchWithBackoff(smileUrl);
        const smileData = JSON.parse(smileJson);
        return smileData.PropertyTable?.Properties?.[0]?.CanonicalSMILES || null;
    } catch (e) {
        if (e.message.includes('Status: 404')) return null;
        console.error(`Error fetching ${name}: ${e.message}`);
        return null;
    }
}

async function main() {
    if (!fs.existsSync(DATA_FILE)) {
        console.error("No data file!");
        return;
    }

    const data = JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
    let count = 0;

    for (let i = 0; i < data.length; i++) {
        const item = data[i];
        if (item.smiles) continue;

        console.log(`[${i + 1}/${data.length}] Processing ${item.en}...`);

        // Strategy 1: Exact name
        let smiles = await getSmilesForName(item.en);

        // Strategy 2: Remove salts
        if (!smiles) {
            const salts = [" hydrochloride", " sodium", " tartrate", " besilate", " maleate", " citrate", " sulfate", " phosphate", " acetate", " nitrate", " bromide", " mesylate", " hydrobromide", " fumarate", " succinate"];
            let base = item.en;
            for (const salt of salts) {
                if (base.includes(salt)) {
                    base = base.replace(salt, "");
                    break;
                }
            }
            if (base !== item.en) {
                console.log(`  > Trying base: ${base}`);
                smiles = await getSmilesForName(base);
            }
        }

        if (smiles) {
            console.log(`  > Found: ${smiles}`);
            item.smiles = smiles;
            count++;

            // Save every 5 updates
            if (count % 5 === 0) {
                fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));
                console.log('  (Saved)');
            }
        } else {
            console.log('  > Not found');
        }

        await delay(300); // polite delay
    }

    fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));
    console.log(`\nDone. Updated ${count} items.`);
}

main();
