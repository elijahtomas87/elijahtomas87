// Rasterize the source and its isolated layers in one process.
const fs = require('node:fs');
const sharp = require('sharp');
const jobs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
(async () => {
  for (const {input, output, scale = 1} of jobs) await sharp(input, {density:72 * scale}).png().toFile(output);
})().catch(error => { console.error(error); process.exit(1); });
