[app]
title = PDFGuard
package.name = pdfguard
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

requirements = python3,kivy,android,pyjnius==1.5.0,requests

android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE
android.api = 34
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.enable_androidx = True

# IMPORTANT
p4a.branch = stable
android.build_type = apk

[buildozer]
log_level = 2
warn_on_root = 1
