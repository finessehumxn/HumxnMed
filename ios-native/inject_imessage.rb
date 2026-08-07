#!/usr/bin/env ruby
# Injects the HumxnMed iMessage extension target into the Capacitor-generated Xcode
# project. Capacitor regenerates ios/ on every Codemagic build, so this runs each build
# (after `npx cap add ios`) to re-add the native target. Idempotent: if the target is
# already present it exits cleanly.
#
# Usage (from repo root, on the Codemagic Mac):
#   ruby ios-native/inject_imessage.rb
#
# Requires the `xcodeproj` gem (ships with CocoaPods, which Codemagic has).

require 'xcodeproj'
require 'fileutils'

REPO          = Dir.pwd
PROJECT_PATH  = File.join(REPO, 'ios/App/App.xcodeproj')
SRCROOT       = File.join(REPO, 'ios/App')             # the project's SRCROOT
EXT_NAME      = 'MessagesExtension'
EXT_SRC       = File.join(REPO, 'ios-native/MessagesExtension')  # our committed sources
EXT_DEST      = File.join(SRCROOT, 'MessagesExtension')          # where they live in the project
APP_BUNDLE    = ENV['BUNDLE_ID'] || 'com.medcompanionai.app'
EXT_BUNDLE    = "#{APP_BUNDLE}.MessagesExtension"
TEAM          = ENV['DEV_TEAM'] || '357ABX659P'
DEPLOY_TARGET = '14.0'

abort "❌ project not found at #{PROJECT_PATH}" unless File.exist?(PROJECT_PATH)

# 1) Copy our committed extension sources into the generated project tree.
FileUtils.rm_rf(EXT_DEST)
FileUtils.cp_r(EXT_SRC, EXT_DEST)
puts "✓ copied extension sources -> #{EXT_DEST}"

project   = Xcodeproj::Project.open(PROJECT_PATH)
app_target = project.targets.find { |t| t.name == 'App' }
abort "❌ 'App' target not found" unless app_target

if project.targets.any? { |t| t.name == EXT_NAME }
  puts "✓ #{EXT_NAME} target already present — nothing to do"
  exit 0
end

# 2) Create the extension target, then force the messages-extension product type.
ext = project.new_target(:app_extension, EXT_NAME, :ios, DEPLOY_TARGET)
ext.product_type = 'com.apple.product-type.app-extension.messages'

# 3) Build settings on every configuration.
ext.build_configurations.each do |c|
  bs = c.build_settings
  bs['PRODUCT_BUNDLE_IDENTIFIER']        = EXT_BUNDLE
  bs['PRODUCT_NAME']                     = '$(TARGET_NAME)'
  bs['INFOPLIST_FILE']                   = 'MessagesExtension/Info.plist'
  bs['GENERATE_INFOPLIST_FILE']          = 'NO'
  bs['SWIFT_VERSION']                    = '5.0'
  bs['IPHONEOS_DEPLOYMENT_TARGET']       = DEPLOY_TARGET
  bs['TARGETED_DEVICE_FAMILY']           = '1,2'
  bs['DEVELOPMENT_TEAM']                 = TEAM
  bs['CODE_SIGN_STYLE']                  = 'Manual'   # use-profiles fills in the specifier
  bs['ASSETCATALOG_COMPILER_APPICON_NAME'] = 'iMessage App Icon'
  bs['ENABLE_BITCODE']                   = 'NO'
  bs['SKIP_INSTALL']                     = 'YES'
  # Explicitly link the frameworks the extension uses. Swift autolinking normally adds
  # these, but naming them is harmless and rules out a missing-symbol link failure.
  bs['OTHER_LDFLAGS']                    = ['$(inherited)', '-framework', 'Foundation', '-framework', 'UIKit', '-framework', 'Messages']
  bs['LD_RUNPATH_SEARCH_PATHS']          = ['$(inherited)', '@executable_path/Frameworks', '@executable_path/../../Frameworks']
  bs['CLANG_ENABLE_MODULES']             = 'YES'
  bs['SWIFT_EMIT_LOC_STRINGS']           = 'YES'
end

# 4) Attach the source + asset catalog (Info.plist is referenced via INFOPLIST_FILE only).
group      = project.main_group.new_group(EXT_NAME)
swift_ref  = group.new_reference('MessagesExtension/MessagesViewController.swift')
group.new_reference('MessagesExtension/Info.plist')
assets_ref = group.new_reference('MessagesExtension/Assets.xcassets')
ext.add_file_references([swift_ref])
ext.add_resources([assets_ref])
puts "✓ added source + assets to #{EXT_NAME}"

# 5) Embed the extension into the App target (dependency + Embed App Extensions phase).
app_target.add_dependency(ext)
embed = app_target.new_copy_files_build_phase('Embed App Extensions')
embed.symbol_dst_subfolder_spec = :plug_ins
build_file = embed.add_file_reference(ext.product_reference, true)
build_file.settings = { 'ATTRIBUTES' => ['RemoveHeadersOnCopy'] }
puts "✓ embedded #{EXT_NAME}.appex into App"

project.save
puts "✅ injected #{EXT_NAME} (#{EXT_BUNDLE}) — project saved"
