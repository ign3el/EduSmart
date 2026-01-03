/**
 * Story Storage Utility - Uses IndexedDB for large stories, localStorage as fallback
 */

const DB_NAME = 'EduSmartDB';
const DB_VERSION = 1;
const STORE_NAME = 'stories';
const SIZE_LIMIT_MB = 5; // Try localStorage for stories under 5MB

// Initialize IndexedDB
function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'id' });
      }
    };
  });
}

// Save story (auto-selects IndexedDB or localStorage based on size)
export async function saveStory(storyData) {
  const storyJson = JSON.stringify(storyData);
  const sizeInMB = new Blob([storyJson]).size / 1024 / 1024;
  
  // Try localStorage for small stories (faster)
  if (sizeInMB < SIZE_LIMIT_MB) {
    try {
      localStorage.setItem(`edusmart_story_${storyData.id}`, storyJson);
      console.log(`Story saved to localStorage (${sizeInMB.toFixed(2)}MB)`);
      return { storage: 'localStorage', size: sizeInMB };
    } catch (e) {
      console.warn('localStorage failed, falling back to IndexedDB:', e);
    }
  }
  
  // Use IndexedDB for large stories or if localStorage fails
  try {
    const db = await openDB();
    const transaction = db.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    
    await new Promise((resolve, reject) => {
      const request = store.put(storyData);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
    
    db.close();
    console.log(`Story saved to IndexedDB (${sizeInMB.toFixed(2)}MB)`);
    return { storage: 'IndexedDB', size: sizeInMB };
  } catch (error) {
    throw new Error(`Failed to save story: ${error.message}`);
  }
}

// Load story from either storage
export async function loadStory(storyId) {
  // Try localStorage first
  try {
    const localData = localStorage.getItem(`edusmart_story_${storyId}`);
    if (localData) {
      return JSON.parse(localData);
    }
  } catch (e) {
    console.warn('localStorage read failed:', e);
  }
  
  // Try IndexedDB
  try {
    const db = await openDB();
    const transaction = db.transaction([STORE_NAME], 'readonly');
    const store = transaction.objectStore(STORE_NAME);
    
    const story = await new Promise((resolve, reject) => {
      const request = store.get(storyId);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
    
    db.close();
    return story || null;
  } catch (error) {
    console.error('Failed to load from IndexedDB:', error);
    return null;
  }
}

// List all stories from both storages
export async function listStories() {
  const stories = [];
  
  // Get from localStorage
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key && key.startsWith('edusmart_story_')) {
      try {
        const data = JSON.parse(localStorage.getItem(key));
        stories.push({ ...data, storage: 'localStorage' });
      } catch (e) {
        console.warn('Failed to parse localStorage story:', key);
      }
    }
  }
  
  // Get from IndexedDB
  try {
    const db = await openDB();
    const transaction = db.transaction([STORE_NAME], 'readonly');
    const store = transaction.objectStore(STORE_NAME);
    
    const indexedDBStories = await new Promise((resolve, reject) => {
      const request = store.getAll();
      request.onsuccess = () => resolve(request.result || []);
      request.onerror = () => reject(request.error);
    });
    
    db.close();
    stories.push(...indexedDBStories.map(s => ({ ...s, storage: 'IndexedDB' })));
  } catch (error) {
    console.error('Failed to list IndexedDB stories:', error);
  }
  
  return stories.sort((a, b) => b.savedAt - a.savedAt);
}

// Delete story from both storages
export async function deleteStory(storyId) {
  // Delete from localStorage
  localStorage.removeItem(`edusmart_story_${storyId}`);
  
  // Delete from IndexedDB
  try {
    const db = await openDB();
    const transaction = db.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    
    await new Promise((resolve, reject) => {
      const request = store.delete(storyId);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
    
    db.close();
  } catch (error) {
    console.error('Failed to delete from IndexedDB:', error);
  }
}

// Get storage info
export async function getStorageInfo() {
  if (navigator.storage && navigator.storage.estimate) {
    const estimate = await navigator.storage.estimate();
    return {
      usage: (estimate.usage / 1024 / 1024).toFixed(2), // MB
      quota: (estimate.quota / 1024 / 1024).toFixed(2), // MB
      available: ((estimate.quota - estimate.usage) / 1024 / 1024).toFixed(2) // MB
    };
  }
  return null;
}
