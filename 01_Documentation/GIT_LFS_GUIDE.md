# 🔧 Git Large File Storage (LFS) Setup Guide

## ❌ ปัญหาที่พบ

```
remote: warning: File ssvid.net--Playlist-아무-생각하기-싫을-때-가만히-듣기-좋은-잔잔한-재즈.mp3 is 55.40 MB; this is larger than GitHub's recommended maximum file size of 50.00 MB
remote: error: File ssvid.net--Fallout-TV-Show-All-Songs.mp3 is 101.59 MB; this exceeds GitHub's file size limit of 100.00 MB
remote: error: GH001: Large files detected. You may want to try Git Large File Storage
```

## 🎯 สาเหตุ

- GitHub จำกัดขนาดไฟล์ที่ **50 MB** (แนะนำ) และ **100 MB** (สูงสุด)
- ไฟล์เสียงในโปรเจคมีขนาดใหญ่เกินกำหนด:
  - `ssvid.net--Playlist-아무-생각하기-싫을-때-가만히-듣기-좋은-잔잔한-재즈.mp3` (55.40 MB)
  - `ssvid.net--Fallout-TV-Show-All-Songs.mp3` (101.59 MB)

## ✅ วิธีแก้ไข

### 🚀 วิธีที่ 1: ใช้ Script อัตโนมัติ (แนะนำ)

```bash
# รันสคริปต์แก้ไขปัญหาอัตโนมัติ
setup_git_lfs.bat
```

### 🔧 วิธีที่ 2: แก้ไขด้วยตนเอง

#### ขั้นตอนที่ 1: ติดตั้ง Git LFS

```bash
# ตรวจสอบว่าติดตั้งแล้วหรือยัง
git lfs version

# หากยังไม่ได้ติดตั้ง ให้ไปที่
# https://git-lfs.github.com/
```

#### ขั้นตอนที่ 2: ตั้งค่า Git LFS

```bash
# ตั้งค่า Git LFS สำหรับ user account
git lfs install

# เพิ่มไฟล์ประเภทที่ต้องการให้ LFS จัดการ
git lfs track "*.mp3"
git lfs track "*.wav"
git lfs track "*.mp4"
git lfs track "*.zip"
git lfs track "*.jpg"
git lfs track "*.png"

# เพิ่ม .gitattributes
git add .gitattributes
```

#### ขั้นตอนที่ 3: Migrate ไฟล์ที่มีอยู่

```bash
# Migrate ไฟล์เสียงที่มีอยู่เข้า LFS
git lfs migrate import --include="*.mp3" --everything

# หรือ migrate ไฟล์เฉพาะ
git lfs migrate import --include="ssvid.net--*.mp3" --everything
```

#### ขั้นตอนที่ 4: Commit และ Push

```bash
# Commit การเปลี่ยนแปลง
git add .
git commit -m "Setup Git LFS for large audio files"

# Push ไปยัง GitHub
git push origin main
```

## 🔍 การตรวจสอบ

### ตรวจสอบไฟล์ที่อยู่ใน LFS

```bash
# แสดงไฟล์ทั้งหมดที่ถูกจัดการโดย LFS
git lfs ls-files

# ตรวจสอบสถานะ LFS
git lfs status

# ดูข้อมูลการใช้งาน LFS
git lfs env
```

### ตรวจสอบ .gitattributes

```bash
# ดูเนื้อหาไฟล์ .gitattributes
cat .gitattributes
```

ควรมีเนื้อหาคล้ายนี้:
```
*.mp3 filter=lfs diff=lfs merge=lfs -text
*.wav filter=lfs diff=lfs merge=lfs -text
*.mp4 filter=lfs diff=lfs merge=lfs -text
*.zip filter=lfs diff=lfs merge=lfs -text
*.jpg filter=lfs diff=lfs merge=lfs -text
*.png filter=lfs diff=lfs merge=lfs -text
```

## 🚨 การแก้ไขปัญหาเพิ่มเติม

### ปัญหา: Push ยังล้มเหลว

```bash
# ลอง force push (ระวัง: อาจเขียนทับ history)
git push origin main --force

# หรือสร้าง branch ใหม่
git checkout -b fix-large-files
git push origin fix-large-files
```

### ปัญหา: ไฟล์ยังใหญ่เกินไป

```bash
# ลบไฟล์ออกจาก Git history
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch "ssvid.net--*.mp3"' \
  --prune-empty --tag-name-filter cat -- --all

# หรือใช้ BFG Repo-Cleaner (แนะนำ)
# https://rtyley.github.io/bfg-repo-cleaner/
```

### ปัญหา: Git LFS quota เต็ม

- GitHub ให้ Git LFS ฟรี **1 GB storage** และ **1 GB bandwidth** ต่อเดือน
- หากเกินสามารถซื้อเพิ่มได้ที่ GitHub Settings

## 📋 ไฟล์ประเภทที่ควรใช้ LFS

### 🎵 Audio Files
- `*.mp3`, `*.wav`, `*.flac`, `*.m4a`, `*.aac`

### 🎬 Video Files  
- `*.mp4`, `*.avi`, `*.mov`, `*.mkv`, `*.wmv`

### 🖼️ Image Files
- `*.jpg`, `*.jpeg`, `*.png`, `*.gif`, `*.bmp`, `*.tiff`
- `*.psd`, `*.ai`, `*.sketch`

### 📦 Archive Files
- `*.zip`, `*.rar`, `*.7z`, `*.tar.gz`

### 📊 Data Files
- `*.csv` (ขนาดใหญ่), `*.json` (ขนาดใหญ่)
- `*.db`, `*.sqlite`

## 💡 Best Practices

1. **ตั้งค่า LFS ตั้งแต่เริ่มต้นโปรเจค**
2. **ใช้ .gitignore สำหรับไฟล์ที่ไม่จำเป็น**
3. **แยกไฟล์ขนาดใหญ่ออกจาก repository หากเป็นไปได้**
4. **ใช้ external storage สำหรับไฟล์ media**
5. **ตรวจสอบขนาดไฟล์ก่อน commit**

## 🔗 ลิงก์ที่เป็นประโยชน์

- [Git LFS Official Site](https://git-lfs.github.com/)
- [GitHub LFS Documentation](https://docs.github.com/en/repositories/working-with-files/managing-large-files)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
- [GitHub LFS Pricing](https://docs.github.com/en/billing/managing-billing-for-git-large-file-storage)

## 🎯 สรุป

หลังจากตั้งค่า Git LFS แล้ว:
- ✅ ไฟล์ขนาดใหญ่จะถูกจัดเก็บใน LFS
- ✅ Repository จะมีขนาดเล็กลง
- ✅ Clone และ fetch จะเร็วขึ้น
- ✅ สามารถ push ไฟล์ขนาดใหญ่ได้โดยไม่มีปัญหา

---

**หมายเหตุ:** หากยังมีปัญหา ให้ลองลบไฟล์เสียงออกจากโปรเจคชั่วคราว แล้วเพิ่มกลับเข้าไปหลังจากตั้งค่า LFS เรียบร้อยแล้ว