/**
 * Generates a SHA-256 hash for a file
 * @param {File} file - The file to hash
 * @returns {Promise<string>} - Hex string of the hash
 */
export async function calculateFileHash(file) {
  try {
    const arrayBuffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    return hashHex;
  } catch (error) {
    console.error('Error calculating file hash:', error);
    throw error;
  }
}

/**
 * Generates a quick hash for file metadata (for preliminary checks)
 * @param {File} file - The file to hash
 * @returns {string} - Simple hash based on file properties
 */
export function calculateQuickHash(file) {
  return `${file.name}_${file.size}_${file.lastModified}`;
}
