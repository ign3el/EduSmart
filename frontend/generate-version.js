const fs = require('fs');
const path = require('path');

// Read package.json for version
const packageJson = JSON.parse(
  fs.readFileSync(path.join(__dirname, 'package.json'), 'utf8')
);

// Create version.json with current timestamp
const versionInfo = {
  version: packageJson.version,
  buildTime: new Date().toISOString()
};

// Write to public directory
const publicDir = path.join(__dirname, 'public');
if (!fs.existsSync(publicDir)) {
  fs.mkdirSync(publicDir, { recursive: true });
}

fs.writeFileSync(
  path.join(publicDir, 'version.json'),
  JSON.stringify(versionInfo, null, 2)
);

console.log('✅ Version file generated:', versionInfo);
