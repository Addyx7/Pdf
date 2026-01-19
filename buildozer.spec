[app]
title = PDF Viewer
package.name = pdfviewer
package.domain = com.example
source.dir = .
source.include_exts = py
version = 1.0.0

requirements = python3,kivy,requests,pyjnius
orientation = portrait
fullscreen = 0

android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 24
android.gradle_dependencies = androidx.core:core:1.12.0

android.manifest_placeholders = applicationId=com.example.pdfviewer
android.add_src = android
