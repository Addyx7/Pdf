[app]
# App Info
title = PDFGuard
package.name = pdfguard
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

# Requirements
requirements = python3,kivy,jnius,requests

# Android
android.api = 33
android.minapi = 21
android.ndk = 25b
android.build_tools_version = 33.0.0
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.archs = arm64-v8a,armeabi-v7a
android.release_artifact = apk
p4a.branch = stable

# Buildozer
log_level = 2
warn_on_root = 1
