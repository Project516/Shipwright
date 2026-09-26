#pragma once
#ifdef __EMSCRIPTEN__

#ifdef __cplusplus
extern "C" {
#endif

// Mounts IndexedDB-backed storage at the app directory and loads its contents.
// Call before anything reads or writes the app directory.
void WebStorage_Mount(void);
// Writes the app directory back to IndexedDB and waits for it to finish.
void WebStorage_Sync(void);
// Same write without waiting, for the quit path where the runtime is going away.
void WebStorage_SyncNoWait(void);
// Called once per frame; syncs every few seconds so saves and settings survive a closed tab.
void WebStorage_PeriodicSync(void);

// Yes/no question for code that would use SDL_ShowMessageBox, which SDL does not
// implement in the browser. Blocks like SDL's alert() fallback for simple boxes.
// Returns 1 for yes.
int WebConfirm(const char* title, const char* text);

// Shows an in-page file prompt and copies the chosen file to destPath.
// Files over maxBytes are refused before they are read, and the prompt stays open.
// Returns 0 when the user cancels or the file cannot be written.
int WebFilePicker_PickInto(const char* title, const char* accept, int maxBytes, const char* destPath);

#ifdef __cplusplus
}
#endif

#endif // __EMSCRIPTEN__
