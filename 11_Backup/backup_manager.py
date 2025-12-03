# ========================================
# Backup และ Recovery System
# ========================================

import os
import shutil
import zipfile
import json
import sqlite3
import threading
import time
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
import schedule
import boto3
from google.cloud import storage as gcs
import dropbox
import paramiko
import ftplib
from cryptography.fernet import Fernet
import psutil

# Import configuration
import sys
sys.path.append(str(Path(__file__).parent.parent / "08_Config"))
from security_config import SecureConfig

@dataclass
class BackupConfig:
    """คลาสสำหรับ configuration ของ backup"""
    name: str
    source_paths: List[str]
    destination: str
    backup_type: str  # 'full', 'incremental', 'differential'
    schedule: str  # cron-like schedule
    retention_days: int
    compression: bool
    encryption: bool
    exclude_patterns: List[str]
    include_databases: bool
    cloud_storage: Optional[str]  # 'aws', 'gcp', 'dropbox', 'ftp'
    enabled: bool

@dataclass
class BackupRecord:
    """คลาสสำหรับเก็บข้อมูล backup record"""
    id: str
    config_name: str
    backup_type: str
    start_time: datetime
    end_time: Optional[datetime]
    status: str  # 'running', 'completed', 'failed'
    file_path: str
    file_size_mb: float
    files_count: int
    checksum: str
    error_message: Optional[str]

class BackupManager:
    """คลาสหลักสำหรับจัดการ backup"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = SecureConfig(config_path)
        self.logger = self._setup_logging()
        
        # Paths
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        self.config_file = Path("backup_configs.json")
        self.db_path = Path("backup_records.db")
        
        # State
        self.backup_configs: Dict[str, BackupConfig] = {}
        self.running_backups: Dict[str, threading.Thread] = {}
        self.scheduler_active = False
        self.scheduler_thread = None
        
        # Encryption
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Initialize
        self._init_database()
        self._load_configs()
        
        # Cloud storage clients
        self.cloud_clients = {}
        self._init_cloud_clients()
    
    def _setup_logging(self) -> logging.Logger:
        """ตั้งค่า logging"""
        logger = logging.getLogger("BackupManager")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler("backup_manager.log")
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _get_or_create_encryption_key(self) -> bytes:
        """สร้างหรือดึง encryption key"""
        key_file = Path("backup_encryption.key")
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            
            # ตั้งค่า permission
            os.chmod(key_file, 0o600)
            return key
    
    def _init_database(self):
        """สร้าง database สำหรับเก็บ backup records"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS backup_records (
                    id TEXT PRIMARY KEY,
                    config_name TEXT NOT NULL,
                    backup_type TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    status TEXT NOT NULL,
                    file_path TEXT,
                    file_size_mb REAL,
                    files_count INTEGER,
                    checksum TEXT,
                    error_message TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_backup_records_config_time 
                ON backup_records(config_name, start_time)
            """)
    
    def _load_configs(self):
        """โหลด backup configurations"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    configs_data = json.load(f)
                
                for name, config_dict in configs_data.items():
                    self.backup_configs[name] = BackupConfig(**config_dict)
                
                self.logger.info(f"Loaded {len(self.backup_configs)} backup configurations")
                
            except Exception as e:
                self.logger.error(f"Error loading backup configs: {e}")
    
    def _save_configs(self):
        """บันทึก backup configurations"""
        try:
            configs_data = {}
            for name, config in self.backup_configs.items():
                configs_data[name] = asdict(config)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(configs_data, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            self.logger.error(f"Error saving backup configs: {e}")
    
    def _init_cloud_clients(self):
        """เริ่มต้น cloud storage clients"""
        try:
            # AWS S3
            if self.config.get('aws_access_key'):
                self.cloud_clients['aws'] = boto3.client(
                    's3',
                    aws_access_key_id=self.config.get('aws_access_key'),
                    aws_secret_access_key=self.config.get('aws_secret_key'),
                    region_name=self.config.get('aws_region', 'us-east-1')
                )
            
            # Google Cloud Storage
            if self.config.get('gcp_credentials_path'):
                self.cloud_clients['gcp'] = gcs.Client.from_service_account_json(
                    self.config.get('gcp_credentials_path')
                )
            
            # Dropbox
            if self.config.get('dropbox_access_token'):
                self.cloud_clients['dropbox'] = dropbox.Dropbox(
                    self.config.get('dropbox_access_token')
                )
            
        except Exception as e:
            self.logger.error(f"Error initializing cloud clients: {e}")
    
    def add_backup_config(self, config: BackupConfig):
        """เพิ่ม backup configuration"""
        self.backup_configs[config.name] = config
        self._save_configs()
        self.logger.info(f"Added backup configuration: {config.name}")
    
    def remove_backup_config(self, name: str):
        """ลบ backup configuration"""
        if name in self.backup_configs:
            del self.backup_configs[name]
            self._save_configs()
            self.logger.info(f"Removed backup configuration: {name}")
    
    def update_backup_config(self, name: str, config: BackupConfig):
        """อัปเดต backup configuration"""
        if name in self.backup_configs:
            self.backup_configs[name] = config
            self._save_configs()
            self.logger.info(f"Updated backup configuration: {name}")
    
    def create_backup(self, config_name: str, backup_type: Optional[str] = None) -> str:
        """สร้าง backup"""
        if config_name not in self.backup_configs:
            raise ValueError(f"Backup configuration '{config_name}' not found")
        
        config = self.backup_configs[config_name]
        
        if not config.enabled:
            raise ValueError(f"Backup configuration '{config_name}' is disabled")
        
        # ใช้ backup_type จาก parameter หรือจาก config
        backup_type = backup_type or config.backup_type
        
        # สร้าง backup record
        backup_id = f"{config_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        record = BackupRecord(
            id=backup_id,
            config_name=config_name,
            backup_type=backup_type,
            start_time=datetime.now(),
            end_time=None,
            status='running',
            file_path='',
            file_size_mb=0,
            files_count=0,
            checksum='',
            error_message=None
        )
        
        # บันทึก record
        self._save_backup_record(record)
        
        # รัน backup ใน thread แยก
        backup_thread = threading.Thread(
            target=self._run_backup,
            args=(config, record),
            daemon=True
        )
        
        self.running_backups[backup_id] = backup_thread
        backup_thread.start()
        
        self.logger.info(f"Started backup: {backup_id}")
        return backup_id
    
    def _run_backup(self, config: BackupConfig, record: BackupRecord):
        """รัน backup process"""
        try:
            # สร้าง backup file path
            timestamp = record.start_time.strftime('%Y%m%d_%H%M%S')
            backup_filename = f"{config.name}_{record.backup_type}_{timestamp}"
            
            if config.compression:
                backup_filename += ".zip"
            else:
                backup_filename += ".tar"
            
            backup_path = self.backup_dir / backup_filename
            
            # สร้าง backup
            if config.compression:
                files_count = self._create_zip_backup(config, backup_path, record.backup_type)
            else:
                files_count = self._create_tar_backup(config, backup_path, record.backup_type)
            
            # Encrypt ถ้าต้องการ
            if config.encryption:
                encrypted_path = backup_path.with_suffix(backup_path.suffix + '.enc')
                self._encrypt_file(backup_path, encrypted_path)
                backup_path.unlink()  # ลบไฟล์ต้นฉบับ
                backup_path = encrypted_path
            
            # คำนวณ checksum
            checksum = self._calculate_checksum(backup_path)
            
            # อัปเดต record
            record.end_time = datetime.now()
            record.status = 'completed'
            record.file_path = str(backup_path)
            record.file_size_mb = backup_path.stat().st_size / (1024 * 1024)
            record.files_count = files_count
            record.checksum = checksum
            
            # Upload to cloud storage
            if config.cloud_storage:
                self._upload_to_cloud(backup_path, config.cloud_storage, config.name)
            
            # Backup databases
            if config.include_databases:
                self._backup_databases(config, record)
            
            self.logger.info(f"Backup completed: {record.id}")
            
        except Exception as e:
            record.end_time = datetime.now()
            record.status = 'failed'
            record.error_message = str(e)
            self.logger.error(f"Backup failed: {record.id} - {e}")
        
        finally:
            # อัปเดต record ใน database
            self._save_backup_record(record)
            
            # ลบจาก running backups
            if record.id in self.running_backups:
                del self.running_backups[record.id]
    
    def _create_zip_backup(self, config: BackupConfig, backup_path: Path, backup_type: str) -> int:
        """สร้าง ZIP backup"""
        files_count = 0
        
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for source_path in config.source_paths:
                source = Path(source_path)
                
                if not source.exists():
                    self.logger.warning(f"Source path not found: {source_path}")
                    continue
                
                if source.is_file():
                    if self._should_include_file(source, config):
                        zipf.write(source, source.name)
                        files_count += 1
                else:
                    for file_path in source.rglob('*'):
                        if file_path.is_file() and self._should_include_file(file_path, config):
                            # ตรวจสอบ backup type
                            if self._should_backup_file(file_path, backup_type, config):
                                relative_path = file_path.relative_to(source.parent)
                                zipf.write(file_path, relative_path)
                                files_count += 1
        
        return files_count
    
    def _create_tar_backup(self, config: BackupConfig, backup_path: Path, backup_type: str) -> int:
        """สร้าง TAR backup"""
        import tarfile
        
        files_count = 0
        
        with tarfile.open(backup_path, 'w') as tar:
            for source_path in config.source_paths:
                source = Path(source_path)
                
                if not source.exists():
                    self.logger.warning(f"Source path not found: {source_path}")
                    continue
                
                if source.is_file():
                    if self._should_include_file(source, config):
                        tar.add(source, source.name)
                        files_count += 1
                else:
                    for file_path in source.rglob('*'):
                        if file_path.is_file() and self._should_include_file(file_path, config):
                            if self._should_backup_file(file_path, backup_type, config):
                                relative_path = file_path.relative_to(source.parent)
                                tar.add(file_path, relative_path)
                                files_count += 1
        
        return files_count
    
    def _should_include_file(self, file_path: Path, config: BackupConfig) -> bool:
        """ตรวจสอบว่าควร include ไฟล์หรือไม่"""
        file_str = str(file_path)
        
        # ตรวจสอบ exclude patterns
        for pattern in config.exclude_patterns:
            if pattern in file_str or file_path.match(pattern):
                return False
        
        return True
    
    def _should_backup_file(self, file_path: Path, backup_type: str, config: BackupConfig) -> bool:
        """ตรวจสอบว่าควร backup ไฟล์ตาม backup type หรือไม่"""
        if backup_type == 'full':
            return True
        
        # สำหรับ incremental และ differential
        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        
        if backup_type == 'incremental':
            # หาไฟล์ backup ล่าสุด
            last_backup = self._get_last_backup(config.name)
            if last_backup and last_backup.start_time:
                return file_mtime > last_backup.start_time
        
        elif backup_type == 'differential':
            # หาไฟล์ full backup ล่าสุด
            last_full_backup = self._get_last_full_backup(config.name)
            if last_full_backup and last_full_backup.start_time:
                return file_mtime > last_full_backup.start_time
        
        return True
    
    def _encrypt_file(self, source_path: Path, dest_path: Path):
        """เข้ารหัสไฟล์"""
        with open(source_path, 'rb') as source_file:
            data = source_file.read()
        
        encrypted_data = self.cipher.encrypt(data)
        
        with open(dest_path, 'wb') as dest_file:
            dest_file.write(encrypted_data)
    
    def _decrypt_file(self, source_path: Path, dest_path: Path):
        """ถอดรหัสไฟล์"""
        with open(source_path, 'rb') as source_file:
            encrypted_data = source_file.read()
        
        data = self.cipher.decrypt(encrypted_data)
        
        with open(dest_path, 'wb') as dest_file:
            dest_file.write(data)
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """คำนวณ checksum ของไฟล์"""
        hash_sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        
        return hash_sha256.hexdigest()
    
    def _upload_to_cloud(self, file_path: Path, cloud_provider: str, config_name: str):
        """อัปโหลดไฟล์ไป cloud storage"""
        try:
            cloud_key = f"backups/{config_name}/{file_path.name}"
            
            if cloud_provider == 'aws' and 'aws' in self.cloud_clients:
                bucket_name = self.config.get('aws_backup_bucket')
                if bucket_name:
                    self.cloud_clients['aws'].upload_file(
                        str(file_path), bucket_name, cloud_key
                    )
                    self.logger.info(f"Uploaded to AWS S3: {cloud_key}")
            
            elif cloud_provider == 'gcp' and 'gcp' in self.cloud_clients:
                bucket_name = self.config.get('gcp_backup_bucket')
                if bucket_name:
                    bucket = self.cloud_clients['gcp'].bucket(bucket_name)
                    blob = bucket.blob(cloud_key)
                    blob.upload_from_filename(str(file_path))
                    self.logger.info(f"Uploaded to GCP Storage: {cloud_key}")
            
            elif cloud_provider == 'dropbox' and 'dropbox' in self.cloud_clients:
                with open(file_path, 'rb') as f:
                    self.cloud_clients['dropbox'].files_upload(
                        f.read(), f"/{cloud_key}"
                    )
                self.logger.info(f"Uploaded to Dropbox: {cloud_key}")
            
            elif cloud_provider == 'ftp':
                self._upload_to_ftp(file_path, cloud_key)
            
        except Exception as e:
            self.logger.error(f"Error uploading to {cloud_provider}: {e}")
    
    def _upload_to_ftp(self, file_path: Path, remote_path: str):
        """อัปโหลดไฟล์ไป FTP server"""
        try:
            ftp_host = self.config.get('ftp_host')
            ftp_user = self.config.get('ftp_user')
            ftp_password = self.config.get('ftp_password')
            
            if not all([ftp_host, ftp_user, ftp_password]):
                raise ValueError("FTP credentials not configured")
            
            with ftplib.FTP(ftp_host) as ftp:
                ftp.login(ftp_user, ftp_password)
                
                # สร้าง directory ถ้าไม่มี
                remote_dir = str(Path(remote_path).parent)
                try:
                    ftp.mkd(remote_dir)
                except ftplib.error_perm:
                    pass  # Directory อาจมีอยู่แล้ว
                
                with open(file_path, 'rb') as f:
                    ftp.storbinary(f'STOR {remote_path}', f)
                
                self.logger.info(f"Uploaded to FTP: {remote_path}")
                
        except Exception as e:
            self.logger.error(f"Error uploading to FTP: {e}")
    
    def _backup_databases(self, config: BackupConfig, record: BackupRecord):
        """สำรองข้อมูล databases"""
        try:
            db_backup_dir = self.backup_dir / "databases" / record.id
            db_backup_dir.mkdir(parents=True, exist_ok=True)
            
            # SQLite databases
            sqlite_files = []
            for source_path in config.source_paths:
                source = Path(source_path)
                if source.exists():
                    sqlite_files.extend(source.rglob('*.db'))
                    sqlite_files.extend(source.rglob('*.sqlite'))
                    sqlite_files.extend(source.rglob('*.sqlite3'))
            
            for db_file in sqlite_files:
                backup_file = db_backup_dir / f"{db_file.stem}_backup.sql"
                self._backup_sqlite_database(db_file, backup_file)
            
            self.logger.info(f"Database backup completed for {record.id}")
            
        except Exception as e:
            self.logger.error(f"Error backing up databases: {e}")
    
    def _backup_sqlite_database(self, db_path: Path, backup_path: Path):
        """สำรองข้อมูล SQLite database"""
        try:
            with sqlite3.connect(db_path) as conn:
                with open(backup_path, 'w') as f:
                    for line in conn.iterdump():
                        f.write(f"{line}\n")
            
        except Exception as e:
            self.logger.error(f"Error backing up SQLite database {db_path}: {e}")
    
    def _save_backup_record(self, record: BackupRecord):
        """บันทึก backup record"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO backup_records (
                        id, config_name, backup_type, start_time, end_time,
                        status, file_path, file_size_mb, files_count,
                        checksum, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.id,
                    record.config_name,
                    record.backup_type,
                    record.start_time.isoformat(),
                    record.end_time.isoformat() if record.end_time else None,
                    record.status,
                    record.file_path,
                    record.file_size_mb,
                    record.files_count,
                    record.checksum,
                    record.error_message
                ))
                
        except Exception as e:
            self.logger.error(f"Error saving backup record: {e}")
    
    def _get_last_backup(self, config_name: str) -> Optional[BackupRecord]:
        """ดึง backup record ล่าสุด"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM backup_records 
                    WHERE config_name = ? AND status = 'completed'
                    ORDER BY start_time DESC LIMIT 1
                """, (config_name,))
                
                row = cursor.fetchone()
                if row:
                    return BackupRecord(
                        id=row[0],
                        config_name=row[1],
                        backup_type=row[2],
                        start_time=datetime.fromisoformat(row[3]),
                        end_time=datetime.fromisoformat(row[4]) if row[4] else None,
                        status=row[5],
                        file_path=row[6],
                        file_size_mb=row[7],
                        files_count=row[8],
                        checksum=row[9],
                        error_message=row[10]
                    )
                
        except Exception as e:
            self.logger.error(f"Error getting last backup: {e}")
        
        return None
    
    def _get_last_full_backup(self, config_name: str) -> Optional[BackupRecord]:
        """ดึง full backup record ล่าสุด"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM backup_records 
                    WHERE config_name = ? AND backup_type = 'full' AND status = 'completed'
                    ORDER BY start_time DESC LIMIT 1
                """, (config_name,))
                
                row = cursor.fetchone()
                if row:
                    return BackupRecord(
                        id=row[0],
                        config_name=row[1],
                        backup_type=row[2],
                        start_time=datetime.fromisoformat(row[3]),
                        end_time=datetime.fromisoformat(row[4]) if row[4] else None,
                        status=row[5],
                        file_path=row[6],
                        file_size_mb=row[7],
                        files_count=row[8],
                        checksum=row[9],
                        error_message=row[10]
                    )
                
        except Exception as e:
            self.logger.error(f"Error getting last full backup: {e}")
        
        return None
    
    def restore_backup(self, backup_id: str, restore_path: str) -> bool:
        """กู้คืนข้อมูลจาก backup"""
        try:
            # ดึง backup record
            record = self.get_backup_record(backup_id)
            if not record:
                raise ValueError(f"Backup record not found: {backup_id}")
            
            backup_file = Path(record.file_path)
            if not backup_file.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_file}")
            
            restore_dir = Path(restore_path)
            restore_dir.mkdir(parents=True, exist_ok=True)
            
            # ถอดรหัสถ้าจำเป็น
            if backup_file.suffix == '.enc':
                decrypted_file = backup_file.with_suffix('')
                self._decrypt_file(backup_file, decrypted_file)
                backup_file = decrypted_file
            
            # แตกไฟล์
            if backup_file.suffix == '.zip':
                with zipfile.ZipFile(backup_file, 'r') as zipf:
                    zipf.extractall(restore_dir)
            else:
                import tarfile
                with tarfile.open(backup_file, 'r') as tar:
                    tar.extractall(restore_dir)
            
            # ลบไฟล์ที่ถอดรหัสชั่วคราว
            if backup_file.name != record.file_path:
                backup_file.unlink()
            
            self.logger.info(f"Backup restored successfully: {backup_id} -> {restore_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring backup {backup_id}: {e}")
            return False
    
    def verify_backup(self, backup_id: str) -> bool:
        """ตรวจสอบความถูกต้องของ backup"""
        try:
            record = self.get_backup_record(backup_id)
            if not record:
                return False
            
            backup_file = Path(record.file_path)
            if not backup_file.exists():
                return False
            
            # ตรวจสอบ checksum
            current_checksum = self._calculate_checksum(backup_file)
            if current_checksum != record.checksum:
                self.logger.error(f"Checksum mismatch for backup {backup_id}")
                return False
            
            # ตรวจสอบว่าไฟล์เปิดได้
            if backup_file.suffix == '.zip':
                with zipfile.ZipFile(backup_file, 'r') as zipf:
                    if zipf.testzip() is not None:
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error verifying backup {backup_id}: {e}")
            return False
    
    def get_backup_record(self, backup_id: str) -> Optional[BackupRecord]:
        """ดึง backup record"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM backup_records WHERE id = ?",
                    (backup_id,)
                )
                
                row = cursor.fetchone()
                if row:
                    return BackupRecord(
                        id=row[0],
                        config_name=row[1],
                        backup_type=row[2],
                        start_time=datetime.fromisoformat(row[3]),
                        end_time=datetime.fromisoformat(row[4]) if row[4] else None,
                        status=row[5],
                        file_path=row[6],
                        file_size_mb=row[7],
                        files_count=row[8],
                        checksum=row[9],
                        error_message=row[10]
                    )
                
        except Exception as e:
            self.logger.error(f"Error getting backup record: {e}")
        
        return None
    
    def list_backups(self, config_name: Optional[str] = None) -> List[BackupRecord]:
        """แสดงรายการ backups"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if config_name:
                    cursor = conn.execute("""
                        SELECT * FROM backup_records 
                        WHERE config_name = ?
                        ORDER BY start_time DESC
                    """, (config_name,))
                else:
                    cursor = conn.execute("""
                        SELECT * FROM backup_records 
                        ORDER BY start_time DESC
                    """)
                
                records = []
                for row in cursor.fetchall():
                    records.append(BackupRecord(
                        id=row[0],
                        config_name=row[1],
                        backup_type=row[2],
                        start_time=datetime.fromisoformat(row[3]),
                        end_time=datetime.fromisoformat(row[4]) if row[4] else None,
                        status=row[5],
                        file_path=row[6],
                        file_size_mb=row[7],
                        files_count=row[8],
                        checksum=row[9],
                        error_message=row[10]
                    ))
                
                return records
                
        except Exception as e:
            self.logger.error(f"Error listing backups: {e}")
            return []
    
    def cleanup_old_backups(self):
        """ลบ backup เก่า"""
        try:
            for config_name, config in self.backup_configs.items():
                if config.retention_days <= 0:
                    continue
                
                cutoff_date = datetime.now() - timedelta(days=config.retention_days)
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT id, file_path FROM backup_records 
                        WHERE config_name = ? AND start_time < ? AND status = 'completed'
                    """, (config_name, cutoff_date.isoformat()))
                    
                    old_backups = cursor.fetchall()
                    
                    for backup_id, file_path in old_backups:
                        # ลบไฟล์
                        backup_file = Path(file_path)
                        if backup_file.exists():
                            backup_file.unlink()
                        
                        # ลบ record
                        conn.execute(
                            "DELETE FROM backup_records WHERE id = ?",
                            (backup_id,)
                        )
                        
                        self.logger.info(f"Deleted old backup: {backup_id}")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old backups: {e}")
    
    def start_scheduler(self):
        """เริ่ม backup scheduler"""
        if self.scheduler_active:
            self.logger.warning("Backup scheduler is already active")
            return
        
        self.scheduler_active = True
        
        # ตั้งค่า schedules
        for config_name, config in self.backup_configs.items():
            if config.enabled and config.schedule:
                self._schedule_backup(config_name, config.schedule)
        
        # เริ่ม scheduler thread
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True
        )
        self.scheduler_thread.start()
        
        self.logger.info("Backup scheduler started")
    
    def _schedule_backup(self, config_name: str, schedule_str: str):
        """ตั้งค่า schedule สำหรับ backup"""
        try:
            # Parse schedule string (simplified cron-like)
            # Format: "daily", "weekly", "hourly", "every 6 hours", etc.
            
            if schedule_str == "daily":
                schedule.every().day.at("02:00").do(self.create_backup, config_name)
            elif schedule_str == "weekly":
                schedule.every().sunday.at("02:00").do(self.create_backup, config_name)
            elif schedule_str == "hourly":
                schedule.every().hour.do(self.create_backup, config_name)
            elif "every" in schedule_str and "hours" in schedule_str:
                hours = int(schedule_str.split()[1])
                schedule.every(hours).hours.do(self.create_backup, config_name)
            elif "every" in schedule_str and "minutes" in schedule_str:
                minutes = int(schedule_str.split()[1])
                schedule.every(minutes).minutes.do(self.create_backup, config_name)
            
        except Exception as e:
            self.logger.error(f"Error scheduling backup {config_name}: {e}")
    
    def _scheduler_loop(self):
        """Scheduler loop"""
        while self.scheduler_active:
            try:
                schedule.run_pending()
                time.sleep(60)  # ตรวจสอบทุกนาที
                
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)
    
    def stop_scheduler(self):
        """หยุด backup scheduler"""
        self.scheduler_active = False
        schedule.clear()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        self.logger.info("Backup scheduler stopped")
    
    def get_backup_status(self) -> Dict[str, Any]:
        """ดึงสถานะ backup system"""
        total_backups = len(self.list_backups())
        running_backups = len(self.running_backups)
        
        # คำนวณขนาดรวม
        total_size_mb = 0
        successful_backups = 0
        failed_backups = 0
        
        for record in self.list_backups():
            if record.status == 'completed':
                successful_backups += 1
                total_size_mb += record.file_size_mb or 0
            elif record.status == 'failed':
                failed_backups += 1
        
        # ตรวจสอบพื้นที่ disk
        backup_disk_usage = psutil.disk_usage(self.backup_dir)
        
        return {
            'total_backups': total_backups,
            'successful_backups': successful_backups,
            'failed_backups': failed_backups,
            'running_backups': running_backups,
            'total_size_mb': round(total_size_mb, 2),
            'scheduler_active': self.scheduler_active,
            'backup_configs': len(self.backup_configs),
            'disk_usage': {
                'total_gb': round(backup_disk_usage.total / (1024**3), 2),
                'used_gb': round(backup_disk_usage.used / (1024**3), 2),
                'free_gb': round(backup_disk_usage.free / (1024**3), 2),
                'percent': round((backup_disk_usage.used / backup_disk_usage.total) * 100, 1)
            }
        }

# ========================================
# Main Function สำหรับทดสอบ
# ========================================

if __name__ == "__main__":
    # สร้าง backup manager
    backup_manager = BackupManager()
    
    # สร้าง sample backup config
    sample_config = BackupConfig(
        name="daily_backup",
        source_paths=["./data", "./logs"],
        destination="./backups",
        backup_type="full",
        schedule="daily",
        retention_days=30,
        compression=True,
        encryption=True,
        exclude_patterns=["*.tmp", "*.log", "__pycache__"],
        include_databases=True,
        cloud_storage=None,
        enabled=True
    )
    
    # เพิ่ม config
    backup_manager.add_backup_config(sample_config)
    
    # เริ่ม scheduler
    backup_manager.start_scheduler()
    
    try:
        print("Backup system started. Press Ctrl+C to stop.")
        
        while True:
            time.sleep(30)
            status = backup_manager.get_backup_status()
            
            print(f"\nBackup Status:")
            print(f"Total Backups: {status['total_backups']}")
            print(f"Successful: {status['successful_backups']}")
            print(f"Failed: {status['failed_backups']}")
            print(f"Running: {status['running_backups']}")
            print(f"Total Size: {status['total_size_mb']:.1f} MB")
            print(f"Scheduler Active: {status['scheduler_active']}")
            
    except KeyboardInterrupt:
        print("\nStopping backup system...")
        backup_manager.stop_scheduler()
        print("Backup system stopped.")