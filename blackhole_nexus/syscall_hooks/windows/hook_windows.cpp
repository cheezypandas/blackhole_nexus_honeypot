#include <windows.h>
#include <detours.h>
#include <fstream>
#include <string>

#define LOG_FILE "C:\\honeypot\\win_hooks.log"

static BOOL (WINAPI *True_CreateFileW)(
    LPCWSTR lpFileName,
    DWORD dwDesiredAccess,
    DWORD dwShareMode,
    LPSECURITY_ATTRIBUTES lpSecurityAttributes,
    DWORD dwCreationDisposition,
    DWORD dwFlagsAndAttributes,
    HANDLE hTemplateFile
) = CreateFileW;

BOOL WINAPI Hooked_CreateFileW(
    LPCWSTR lpFileName,
    DWORD dwDesiredAccess,
    DWORD dwShareMode,
    LPSECURITY_ATTRIBUTES lpSecurityAttributes,
    DWORD dwCreationDisposition,
    DWORD dwFlagsAndAttributes,
    HANDLE hTemplateFile
) {
    std::ofstream log(LOG_FILE, std::ios::app);
    if (log) {
        log << "[CreateFileW] Attempt: " << lpFileName << "\n";
        log.close();
    }
    
    // Block writes to sensitive locations
    if (wcsstr(lpFileName, L"System32") && (dwDesiredAccess & GENERIC_WRITE)) {
        SetLastError(ERROR_ACCESS_DENIED);
        return INVALID_HANDLE_VALUE;
    }
    
    return True_CreateFileW(
        lpFileName,
        dwDesiredAccess,
        dwShareMode,
        lpSecurityAttributes,
        dwCreationDisposition,
        dwFlagsAndAttributes,
        hTemplateFile
    );
}

BOOL APIENTRY DllMain(HMODULE hModule, DWORD ul_reason_for_call, LPVOID lpReserved) {
    if (ul_reason_for_call == DLL_PROCESS_ATTACH) {
        DetourTransactionBegin();
        DetourUpdateThread(GetCurrentThread());
        DetourAttach(&(PVOID&)True_CreateFileW, Hooked_CreateFileW);
        DetourTransactionCommit();
    }
    return TRUE;
}