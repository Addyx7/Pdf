[app]
title = PDFGuard
package.name = pdfguard
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

requirements = python3,kivy,android,jnius,requests

android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_path = /usr/local/lib/android/sdk/ndk/25.2.9519653

android.build_type = apk
p4a.branch = stable

android.accept_sdk_license = True
android.enable_androidx = True

[buildozer]
log_level = 2
warn_on_root = 1

