const fs = require('fs');
const path = require('path');

const dataPath = path.join(__dirname, '..', 'src', 'data.json');
const nonMedPath = path.join(__dirname, '..', 'src', 'non_med_data.json');

const data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
const nonMed = JSON.parse(fs.readFileSync(nonMedPath, 'utf8'));

// Create a map of English name to SMILES and Image
const smileMap = {};
data.forEach(item => {
    if (item.en && item.smiles) {
        smileMap[item.en.toLowerCase()] = {
            smiles: item.smiles,
            image: item.image
        };
    }
    if (item.cn && item.smiles) {
        smileMap[item.cn] = {
            smiles: item.smiles,
            image: item.image
        };
    }
});

let patchedCount = 0;
const patchedNonMed = nonMed.map(item => {
    const match = smileMap[item.en.toLowerCase()] || smileMap[item.cn];
    if (match && (!item.smiles || !item.image)) {
        patchedCount++;
        return {
            ...item,
            smiles: item.smiles || match.smiles,
            image: item.image || match.image
        };
    }
    return item;
});

fs.writeFileSync(nonMedPath, JSON.stringify(patchedNonMed, null, 2));
console.log(`Patched ${patchedCount} items in non_med_data.json`);
