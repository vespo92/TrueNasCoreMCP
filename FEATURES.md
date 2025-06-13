# TrueNAS MCP Server - Feature Documentation

## Table of Contents

- [Core Features](#core-features)
- [Phase 2 Advanced Features](#phase-2-advanced-features)
- [Usage Examples](#usage-examples)
- [Best Practices](#best-practices)
- [Compatibility](#compatibility)

## Core Features

### 🗄️ Storage Management

#### List Storage Pools
```
"Show me all storage pools"
"What pools do I have?"
```
Returns pool names, status, capacity, and health information.

#### Dataset Operations
```
"Create a dataset called projects in tank pool"
"List all datasets"
"Show me tank/data status"
```
- Create datasets with customizable compression
- Set quotas and reservations
- View usage statistics

#### Snapshot Management
```
"Take a snapshot of tank/important called before-update"
"Create recursive snapshot of tank/vms"
```
- Manual snapshot creation
- Recursive snapshots for dataset trees
- Custom naming schemes

### 👥 User Management

#### List and View Users
```
"List all users"
"Show me details for user john"
```
- View user accounts, groups, and permissions
- Check sudo privileges and shell access
- Identify system vs regular users

### 🔗 Sharing

#### SMB/CIFS Shares
```
"List all SMB shares"
"Create a share called Public for /mnt/tank/public"
```
- Create Windows-compatible network shares
- Set read-only or read-write access
- Add descriptions and comments

## Phase 2 Advanced Features

### 🔐 Permission Management

#### Unix Permissions (chmod/chown)
```
"Change permissions on tank/data to 755"
"Set owner of tank/shared to john and group to developers"
"Recursively change ownership of tank/projects to mary"
```

**Features:**
- Standard Unix permission modes (755, 644, etc.)
- User and group ownership changes
- Recursive operations for directory trees
- Support for both usernames and UIDs/GIDs

#### Access Control Lists (ACLs)
```
"Give the sales group read access to tank/reports"
"Set up ACLs for tank/shared with full control for admins"
"Remove all ACLs from tank/temp"
```

**Features:**
- Fine-grained permission control
- Windows-compatible ACL support
- Multiple user/group entries
- Inheritance control

### 🎛️ Dataset Properties

#### Compression
```
"Enable lz4 compression on tank/backups"
"Change compression to zstd on tank/archives"
"Disable compression on tank/media"
```

**Supported algorithms:**
- lz4 (default, balanced)
- zstd (better compression)
- gzip (levels 1-9)
- off (disable)

#### Quotas and Reservations
```
"Set a 100GB quota on tank/users/john"
"Reserve 50GB for tank/databases"
"Remove quota from tank/temp"
```

**Features:**
- Human-readable sizes (100G, 2T, 500M)
- User quotas (quota/refquota)
- Space reservations (reservation/refreservation)

#### Performance Tuning
```
"Disable atime on tank/vms for better performance"
"Set recordsize to 1M for tank/media"
"Enable deduplication on tank/backups"
```

**Tunable properties:**
- atime (access time updates)
- recordsize (block size)
- sync (synchronous writes)
- deduplication (storage efficiency)

### ☸️ Kubernetes Storage Integration

#### NFS Exports for Persistent Volumes
```
"Create an NFS export for tank/k8s-volumes accessible from 10.0.0.0/24"
"Export tank/wordpress-data for my Kubernetes cluster"
```

**Features:**
- Network access restrictions
- Root squashing options
- Auto-generated StorageClass YAML
- PersistentVolume examples

**Generated Kubernetes YAML:**
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: truenas-nfs-tank-k8s
provisioner: nfs.csi.k8s.io
parameters:
  server: 192.168.1.100
  share: /mnt/tank/k8s-volumes
```

#### iSCSI Targets for Block Storage
```
"Create a 100GB iSCSI target called postgres-data"
"Set up 50GB block storage for mongodb in tank/iscsi"
```

**Features:**
- Block-level storage for databases
- Automatic extent creation
- iSCSI qualified names (IQN)
- Multiple LUN support

### 🤖 Automation

#### Snapshot Policies
```
"Create daily snapshots of tank/important keeping 30 days"
"Set up hourly snapshots for tank/databases with 24 hour retention"
"Schedule weekly snapshots of tank/homes keeping 4 weeks"
```

**Schedule options:**
- Hourly, daily, weekly, monthly
- Custom cron expressions
- Flexible retention periods
- Recursive snapshots

**Example schedule:**
```python
{
    "minute": "0",
    "hour": "2",      # 2 AM
    "dom": "*",       # Every day
    "month": "*",     # Every month
    "dow": "*"        # Every day of week
}
```

## Usage Examples

### Complete Workflow Examples

#### Setting Up a Development Environment
```
1. "Create dataset tank/development"
2. "Set compression to lz4 on tank/development"
3. "Create dataset tank/development/projects"
4. "Set permissions 775 on tank/development/projects with group developers"
5. "Create SMB share DevProjects for /mnt/tank/development/projects"
6. "Set up daily snapshots keeping 7 days"
```

#### Kubernetes Storage Setup
```
1. "Create dataset tank/kubernetes"
2. "Create dataset tank/kubernetes/nfs-volumes"
3. "Create dataset tank/kubernetes/iscsi-volumes"
4. "Create NFS export for tank/kubernetes/nfs-volumes from 10.42.0.0/16"
5. "Create 50GB iSCSI target postgres-pv in tank/kubernetes/iscsi-volumes"
```

#### User Home Directory with Quotas
```
1. "Create dataset tank/users/alice"
2. "Set owner alice on tank/users/alice"
3. "Set permissions 700 on tank/users/alice"
4. "Set quota 50GB on tank/users/alice"
5. "Create SMB share alice-home for /mnt/tank/users/alice"
```

## Best Practices

### 🏆 Recommended Patterns

1. **Dataset Hierarchy**
   ```
   tank/
   ├── apps/          # Application data
   ├── backups/       # Backup storage
   ├── media/         # Large media files
   ├── users/         # User home directories
   └── vms/           # Virtual machine storage
   ```

2. **Compression Strategy**
   - `lz4` - General purpose (default)
   - `zstd` - Better compression for archives
   - `off` - Media files, encrypted data

3. **Snapshot Retention**
   - Hourly: 24-48 snapshots
   - Daily: 7-30 snapshots
   - Weekly: 4-12 snapshots
   - Monthly: 6-12 snapshots

4. **Permission Models**
   - User homes: 700 or 750
   - Shared data: 770 or 775
   - Public read: 755
   - Sensitive: 700 with ACLs

### ⚠️ Important Considerations

1. **Recursive Operations**
   - Always verify dataset contents before recursive changes
   - Recursive permission changes can't be easily undone
   - Consider creating a snapshot before major changes

2. **Storage Efficiency**
   - Don't enable deduplication without sufficient RAM
   - Compression has minimal performance impact with lz4
   - Monitor pool fragmentation

3. **Kubernetes Storage**
   - Use NFS for ReadWriteMany (RWX) access
   - Use iSCSI for ReadWriteOnce (RWO) with better performance
   - Always specify network restrictions for NFS

## Compatibility

### Tested Versions
- **TrueNAS Core**: 13.0-U6.1 ✅
- **API Version**: v2.0

### Python Support
- Python 3.10 ✅
- Python 3.11 ✅
- Python 3.12 ✅

### MCP Clients
- Claude Desktop ✅
- Any MCP-compatible client ✅

### Known Limitations
- iSCSI configuration may require additional setup on TrueNAS Core
- Snapshot policies use TrueNAS periodic snapshot tasks

## Support

For issues, questions, or feature requests:
- 📝 [GitHub Issues](https://github.com/vespo92/TrueNasCoreMCP/issues)
- 💬 [Discussions](https://github.com/vespo92/TrueNasCoreMCP/discussions)

---

**Note:** This documentation covers version 2.0.0. Check [CHANGELOG.md](CHANGELOG.md) for version-specific features.
