[app]
title = Simon
p4a.branch=2024.1.20
package.name = simon
package.domain = org.simon.assistant
source.dir = .
source.include_exts = py,json,wav
version = 0.4
requirements = python3,kivy==2.3.1,requests
orientation = portrait
fullscreen = 0
android.permissions = RECORD_AUDIO,INTERNET,POST_NOTIFICATIONS,WAKE_LOCK
android.api = 33
android.minapi = 24
android.archs = arm64-v8a
android.accept_sdk_license=True

[buildozer]
log_level = 2
warn_on_root = 1
