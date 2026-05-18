"""Aseprite integration service."""

import os
import subprocess
import tempfile
from pathlib import Path


class AsepriteService:
    """Handles Aseprite executable path and CLI operations."""

    def __init__(self, database_service):
        self.db = database_service
        self._cache_path: str | None = None

    def set_aseprite_path(self, path: str) -> None:
        """Save Aseprite executable path."""
        self._cache_path = path
        self.db.set_setting("aseprite_path", path)

    def get_aseprite_path(self) -> str:
        """Get Aseprite executable path."""
        if self._cache_path is None:
            self._cache_path = self.db.get_setting("aseprite_path", "")
        return self._cache_path

    def is_available(self) -> bool:
        """Check if Aseprite path is configured and exists."""
        path = self.get_aseprite_path()
        return bool(path) and os.path.isfile(path)

    def open_file(self, file_path: str) -> None:
        """Open file with Aseprite, or fallback to system default."""
        aseprite = self.get_aseprite_path()
        if aseprite and os.path.isfile(aseprite):
            subprocess.Popen([aseprite, file_path])
        else:
            os.startfile(file_path)

    def export_preview_png(self, aseprite_file: str, output_png: str) -> bool:
        """Export a preview PNG for an Aseprite file."""
        if self._export_preview_with_aseprite_cli(aseprite_file, output_png):
            return True
        return self._export_preview_with_windows_shell(aseprite_file, output_png)

    def _export_preview_with_aseprite_cli(self, aseprite_file: str, output_png: str) -> bool:
        """Export first frame of aseprite file to PNG using Aseprite CLI."""
        aseprite = self.get_aseprite_path()
        if not aseprite or not os.path.isfile(aseprite):
            return False
        if not os.path.exists(aseprite_file):
            return False

        try:
            Path(output_png).parent.mkdir(parents=True, exist_ok=True)
            commands = [
                [aseprite, "-b", aseprite_file, "--frame", "0", "--save-as", output_png],
                [aseprite, "-b", aseprite_file, "--save-as", output_png],
            ]
            for command in commands:
                if os.path.exists(output_png):
                    os.remove(output_png)
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.returncode == 0 and os.path.exists(output_png):
                    return True
        except Exception:
            return False
        return False

    def _export_preview_with_windows_shell(self, aseprite_file: str, output_png: str) -> bool:
        """Use Windows Explorer's thumbnail provider as a fallback preview source."""
        if os.name != "nt" or not os.path.exists(aseprite_file):
            return False

        script = r'''
param(
    [string]$InputPath,
    [string]$OutputPath,
    [int]$Size
)
$ErrorActionPreference = 'Stop'
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @"
using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;

[StructLayout(LayoutKind.Sequential)]
public struct SIZE {
    public int cx;
    public int cy;
    public SIZE(int x, int y) { cx = x; cy = y; }
}

[Flags]
public enum SIIGBF {
    ResizeToFit = 0x00,
    BiggerSizeOk = 0x01,
    ThumbnailOnly = 0x08
}

[ComImport]
[Guid("bcc18b79-ba16-442f-80c4-8a59c30c463b")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IShellItemImageFactory {
    void GetImage(SIZE size, SIIGBF flags, out IntPtr phbm);
}

public static class ShellThumbnail {
    [DllImport("shell32.dll", CharSet = CharSet.Unicode, PreserveSig = false)]
    static extern void SHCreateItemFromParsingName(
        string pszPath,
        IntPtr pbc,
        [MarshalAs(UnmanagedType.LPStruct)] Guid riid,
        out IShellItemImageFactory ppv
    );

    [DllImport("gdi32.dll")]
    static extern bool DeleteObject(IntPtr hObject);

    public static void Save(string input, string output, int size) {
        Guid iid = typeof(IShellItemImageFactory).GUID;
        IShellItemImageFactory factory;
        SHCreateItemFromParsingName(input, IntPtr.Zero, iid, out factory);
        IntPtr hbitmap;
        factory.GetImage(new SIZE(size, size), SIIGBF.BiggerSizeOk, out hbitmap);
        try {
            using (Bitmap bitmap = Bitmap.FromHbitmap(hbitmap)) {
                bitmap.Save(output, ImageFormat.Png);
            }
        } finally {
            DeleteObject(hbitmap);
        }
    }
}
"@
[System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($OutputPath)) | Out-Null
[ShellThumbnail]::Save($InputPath, $OutputPath, $Size)
'''
        script_path = ""
        try:
            Path(output_png).parent.mkdir(parents=True, exist_ok=True)
            if os.path.exists(output_png):
                os.remove(output_png)
            with tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False, encoding="utf-8") as script_file:
                script_file.write(script)
                script_path = script_file.name
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    script_path,
                    aseprite_file,
                    output_png,
                    "256",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
            return result.returncode == 0 and os.path.exists(output_png)
        except Exception:
            return False
        finally:
            if script_path and os.path.exists(script_path):
                try:
                    os.remove(script_path)
                except OSError:
                    pass
