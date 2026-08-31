#!/bin/bash
# vendorsetup.sh — AOSP compatibility (kept so lunch still finds the tree)
# SpiderLang reads BoardConfig.spt directly, this only registers the lunch combo.

export SPIDER_DEVICE="X6886"
add_lunch_combo "twrp_X6886-eng"
add_lunch_combo "twrp_X6886-userdebug"
echo "SpiderLang: registered lunch combos for X6886"
