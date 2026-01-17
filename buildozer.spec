[app]
title = PDF Viewer
package.name = pdfviewer
package.domain = org.viewer

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas

version = 1.0.0

# --- Python requirements ---
requirements = python3,kivy,android,pyjnius==1.5.0,requests

# --- Android permissions ---
android.permissions = INTERNET, READ_EXTERNAL_STORAGE

# WRITE_EXTERNAL_STORAGE not required for scoped storage (API 29+)
# Files are stored in app-specific external directory

# --- Android SDK configuration ---
android.api = 34
android.minapi = 21
android.build_tools_version = 34.0.0
android.ndk = 25b

android.accept_sdk_license = True
android.enable_androidx = True

# Required for FileProvider + AndroidX
android.use_androidx = True

# --- Python-for-Android ---
p4a.branch = master

# --- App behavior ---
android.allow_backup = True
android.fullscreen = False
android.orientation = portrait

# Optional: speeds up cold start
android.manifest_placeholders = applicationName=org.kivy.android.PythonApplication


[buildozer]
log_level = 2
warn_on_root = 1

