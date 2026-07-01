# Astra Headend - MPEG-2 TS Processing System

## 📺 نظام معالجة البث التلفزيوني الاحترافي

**Astra** هو نظام متكامل لمعالجة وبث تدفقات MPEG-2 Transport Stream، مصمم للعمل مع أنظمة البث التلفزيوني الاحترافية.

### ✨ المميزات الرئيسية

#### 📥 **المدخلات المدعومة**
- **DVB-S/S2** - استقبال الأقمار الصناعية
- **DVB-C** - كابل رقمي
- **DVB-T/T2** - بث أرضي رقمي
- **IPTV** - بث عبر IP (UDP, RTP, HTTP, HLS)

#### 🔧 **معالجة متقدمة**
- **فلترة القنوات** - اختيار PIDs محددة
- **إعادة تعيين PIDs** - تغيير معرّفات الحزم
- **التجميع (Multiplexing)** - دمج عدة مصادر
- **التشفير** - دعم التشفير DVB-CSA
- **المراقبة** - تحديث الـ Metrics والإنذارات

#### 📤 **المخرجات المدعومة**
- **UDP Multicast** - بث متعدد الوجهات
- **HTTP Streaming** - بث عبر HTTP
- **HLS** - HTTP Live Streaming
- **SRT** - Secure Reliable Transport
- **RTSP** - Real Time Streaming Protocol

#### 🎛️ **الميزات المتقدمة**
- **Failover/Backup** - التبديل التلقائي للمصادر
- **EPG/SI Tables** - معلومات البرامج والخدمات
- **REST API** - واجهة برمجية متكاملة
- **Config Management** - إدارة الإعدادات (YAML/JSON)
- **Monitoring** - مراقبة النظام والأداء

---

## 🚀 البدء السريع

### التثبيت

```bash
# استنساخ المستودع
git clone https://github.com/eng2zezo-dot/astra-python.git
cd astra-python

# تثبيت المتطلبات
pip install -r requirements.txt

# التثبيت
pip install -e .
```

### الاستخدام الأساسي

```bash
# عرض المساعدة
astra --help

# عرض حالة النظام
astra --status

# تحميل الإعدادات وتشغيل API
astra --config config.yaml --api 0.0.0.0 5000

# تشغيل النظام
astra --start

# إيقاف النظام
astra --stop
```

---

## 📚 أمثلة الاستخدام

### مثال 1: الإعداد الأساسي

```python
from astra.core.headend import AstraHeadend, Channel, InputSource, OutputTarget, SourceType, OutputType

# إنشاء نظام Headend
headend = AstraHeadend()

# إضافة قناة
channel = Channel(
    name="BBC One",
    service_id=4101,
    video_pid=0x0100,
    audio_pids=[0x0101]
)
headend.add_channel(channel)

# إضافة مصدر
source = InputSource(
    name="Satellite",
    source_type=SourceType.DVB_S,
    uri="dvb://adapter0",
    frequency=11462000,
    symbol_rate=22000000
)
headend.add_input_source(source)

# إضافة مخرج
output = OutputTarget(
    name="UDP",
    output_type=OutputType.UDP,
    uri="udp://239.1.1.100:5000",
    channels=["BBC One"]
)
headend.add_output_target(output)

# تشغيل النظام
headend.start()
```

### مثال 2: معالجة متقدمة

```python
from astra.core.transport_stream import TransportStream
from astra.processing.filter import ChannelFilter
from astra.processing.remapper import PIDRemapper
from astra.processing.multiplexer import Multiplexer

# إنشاء transport stream
ts = TransportStream()

# فلترة
filter_obj = ChannelFilter(ts)
filter_obj.add_keep_pid(0x100)
filter_obj.apply()

# إعادة تعيين
remapper = PIDRemapper(ts)
remapper.add_pid_mapping(0x100, 0x200)
remapper.apply_pid_remapping()

# تجميع
multiplexer = Multiplexer()
multiplexer.add_input_stream("ts1", ts)
output = multiplexer.multiplex()
```

### مثال 3: تحميل الإعدادات

```python
from astra.config.config_manager import ConfigManager

# تحميل الإعدادات
config = ConfigManager('config.yaml')
config.apply_to_headend(headend)

# حفظ الإعدادات
config.export_from_headend(headend)
config.save_config('backup.yaml')
```

---

## 🔧 REST API

واجهة برمجية شاملة للتحكم في النظام:

```bash
# الحالة
curl http://localhost:5000/api/v1/status

# قائمة القنوات
curl http://localhost:5000/api/v1/channels

# إضافة قناة
curl -X POST http://localhost:5000/api/v1/channels \
  -H "Content-Type: application/json" \
  -d '{"name": "BBC", "service_id": 4101, "video_pid": 0x100}'

# حذف قناة
curl -X DELETE http://localhost:5000/api/v1/channels/BBC

# تشغيل/إيقاف
curl -X POST http://localhost:5000/api/v1/system/start
curl -X POST http://localhost:5000/api/v1/system/stop
```

---

## 📋 ملف الإعدادات (YAML)

```yaml
channels:
  BBC_ONE:
    service_id: 4101
    video_pid: 0x0100
    audio_pids: [0x0101, 0x0102]
    pmt_pid: 0x0110

inputs:
  SATELLITE_INPUT:
    type: dvb-s
    uri: dvb://adapter0
    frequency: 11462000
    symbol_rate: 22000000

outputs:
  UDP_MULTICAST:
    type: udp
    uri: udp://239.1.1.100:5000
    channels: [BBC_ONE]
```

---

## 📊 البنية المعمارية

```
astra/
├── core/                    # النوى الأساسية
│   ├── packet.py           # MPEG-2 TS Packets
│   ├── transport_stream.py  # معالجة TS
│   └── headend.py          # النظام الرئيسي
├── inputs/                 # المدخلات
│   ├── dvb_receiver.py     # DVB receiver
│   └── iptv_receiver.py    # IPTV receiver
├── processing/             # المعالجة
│   ├── filter.py           # فلترة
│   ├── remapper.py         # إعادة تعيين
│   ├── multiplexer.py      # تجميع
│   └── scrambler.py        # تشفير
├── outputs/                # المخرجات
│   ├── udp_output.py       # UDP
│   ├── http_output.py      # HTTP
│   ├── hls_output.py       # HLS
│   ├── srt_output.py       # SRT
│   └── rtsp_output.py      # RTSP
├── monitoring/             # المراقبة
│   └── monitor.py          # System Monitor
├── failover/               # الـ Failover
│   └── backup_manager.py   # Backup Manager
├── epg/                    # EPG/SI Tables
│   └── si_tables.py        # SI Parser
├── api/                    # REST API
│   └── rest_api.py         # Flask API
├── config/                 # الإعدادات
│   └── config_manager.py   # Config Manager
├── utils/                  # الأدوات
│   ├── logger.py           # Logger
│   └── helpers.py          # Helpers
└── main.py                 # Entry Point
```

---

## 🧪 الاختبارات

```bash
# تشغيل جميع الاختبارات
python -m pytest tests/

# اختبار محدد
python -m pytest tests/test_core.py

# مع تغطية
python -m pytest tests/ --cov=astra
```

---

## 📖 التوثيق

### الفئات الرئيسية

#### `AstraHeadend`
النظام الرئيسي الذي يدير القنوات والمصادر والمخرجات.

```python
headend = AstraHeadend()
headend.add_channel(channel)
headend.add_input_source(source)
headend.add_output_target(output)
headend.start()
```

#### `SystemMonitor`
مراقبة الأداء والإنذارات.

```python
monitor = SystemMonitor(headend)
monitor.start()
metrics = monitor.get_metrics()
```

#### `BackupManager`
إدارة الـ Failover والنسخ الاحتياطية.

```python
backup = BackupManager()
backup.add_backup_source('SAT', 'primary', 'backup')
backup.start_monitoring()
```

#### `ConfigManager`
إدارة الإعدادات.

```python
config = ConfigManager()
config.load_config('config.yaml')
config.apply_to_headend(headend)
```

---

## 🔐 الأمان

- 🔒 **التشفير** - دعم DVB-CSA
- 🛡️ **التحقق** - التحقق من سلامة البيانات
- 🔄 **الـ Failover** - ضمان استمرار الخدمة

---

## 📝 الترخيص

MIT License - انظر [LICENSE](LICENSE) للتفاصيل.

---

## 👨‍💻 المساهمون

- **Eng2zezo** - المطور الرئيسي

---

## 📧 التواصل

- **البريد الإلكتروني**: eng2zezo@gmail.com
- **GitHub**: https://github.com/eng2zezo-dot
- **المشروع**: https://github.com/eng2zezo-dot/astra-python

---

## 🎯 خارطة الطريق

- [ ] دعم DVB-CI (Conditional Access Interface)
- [ ] إضافة واجهة ويب (Web Dashboard)
- [ ] دعم Docker
- [ ] تحسين الأداء (GPU acceleration)
- [ ] دعم المزيد من البروتوكولات

---

## 📚 موارد إضافية

- [MPEG-2 TS Specification](https://en.wikipedia.org/wiki/MPEG_transport_stream)
- [DVB Standards](https://www.dvb.org/)
- [Transport Stream](https://en.wikipedia.org/wiki/MPEG_transport_stream)

---

**Made with ❤️ for broadcast professionals**
