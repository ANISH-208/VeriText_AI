export type SavedReference = {
  id: string;
  name: string;
  type: string;
  size: number;
  savedAt: number;
  data: Blob;
};

const DB_NAME = 'veritext-local-reference-library';
const STORE = 'references';

function database(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = () => request.result.createObjectStore(STORE, { keyPath: 'id' });
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error || new Error('Could not open the local reference library.'));
  });
}

export async function listSavedReferences(): Promise<SavedReference[]> {
  const db = await database();
  return new Promise((resolve, reject) => {
    const request = db.transaction(STORE, 'readonly').objectStore(STORE).getAll();
    request.onsuccess = () => resolve((request.result as SavedReference[]).sort((a, b) => b.savedAt - a.savedAt));
    request.onerror = () => reject(request.error || new Error('Could not read the local reference library.'));
    request.transaction?.addEventListener('complete', () => db.close());
  });
}

export async function saveReferences(files: File[]): Promise<void> {
  const db = await database();
  await new Promise<void>((resolve, reject) => {
    const transaction = db.transaction(STORE, 'readwrite');
    const store = transaction.objectStore(STORE);
    files.forEach(file => store.put({
      id: `${file.name}-${file.size}-${file.lastModified}`,
      name: file.name,
      type: file.type,
      size: file.size,
      savedAt: Date.now(),
      data: file,
    } satisfies SavedReference));
    transaction.oncomplete = () => { db.close(); resolve(); };
    transaction.onerror = () => { db.close(); reject(transaction.error || new Error('Could not save references in this browser.')); };
  });
}

export async function deleteSavedReference(id: string): Promise<void> {
  const db = await database();
  await new Promise<void>((resolve, reject) => {
    const transaction = db.transaction(STORE, 'readwrite');
    transaction.objectStore(STORE).delete(id);
    transaction.oncomplete = () => { db.close(); resolve(); };
    transaction.onerror = () => { db.close(); reject(transaction.error || new Error('Could not remove this saved reference.')); };
  });
}

export function toFile(reference: SavedReference): File {
  return new File([reference.data], reference.name, { type: reference.type, lastModified: reference.savedAt });
}
