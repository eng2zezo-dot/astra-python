# Astra Python - نظام Headend البرمجي

## نظرة عامة

**Astra Python** هو نظام Headend Software متقدم يعمل على Linux لتحويل واستقبال ومعالجة وتوزيع قنوات التلفزيون عبر الأقمار الصناعية أو الشبكات أو IPTV.

## الميزات الرئيسية

### 1. مصادر الإدخال (Input Sources)
- ✅ DVB-S/S2 (الأقمار الصناعية)
- ✅ DVB-C (الكابل)
- ✅ DVB-T/T2 (الأرضي)
- ✅ IPTV (UDP, RTP, HTTP, HLS, SRT, RTSP)

### 2. معالجة Transport Stream
- ✅ فلترة القنوات (Filtering)
- ✅ إعادة الترتيب والتعديل (Remapping)
- ✅ معالجة SPTS و MPTS
- ✅ دعم DVB-CI / CAM للتشفير

### 3. المخرجات (Delivery)
- ✅ UDP Multicast
- ✅ HTTP Streaming
- ✅ HLS
- ✅ SRT
- ✅ RTSP

### 4. الميزات المتقدمة
- ✅ Multiplexing (تجميع المصادر)
- ✅ EPG و SI Tables
- ✅ Backup/Failover (النسخ الاحتياطي)
- ✅ Monitoring والمراقبة
- ✅ API للتحكم
- ✅ Lua Scripts
- ✅ SAT>IP

## التثبيت

```bash
git clone https://github.com/eng2zezo-dot/astra-python.git
cd astra-python
pip install -r requirements.txt
```

## الاستخدام

```python
from astra import AstraHeadend

# إنشاء Headend
headend = AstraHeadend()

# إضافة مصدر DVB-S
headend.add_dvb_source('dvb_s', adapter=0, frequency=11554, symbol_rate=27500)

# إنشاء قناة
headend.create_channel('BBC HD', input_source='dvb_s', service_id=4101)

# إرسال البث
headend.start_output('udp://239.1.1.1:5000')
```

## البنية

```
astra-python/
├── astra/
│   ├── __init__.py
│   ├── core/
│   │   ├── headend.py           # النواة الرئيسية
│   │   ├── transport_stream.py   # معالجة TS
│   │   └── packet.py            # TS Packet
│   ├── inputs/
│   │   ├── dvb_receiver.py       # استقبال DVB
│   │   ├── iptv_receiver.py      # استقبال IPTV
│   │   ├── rtsp_receiver.py      # استقبال RTSP
│   │   └── sat_ip.py            # SAT>IP
│   ├── processing/
│   │   ├── filter.py            # الفلترة
│   │   ├── remapper.py          # إعادة الترتيب
│   │   ├── multiplexer.py       # التجميع
│   │   └── scrambler.py         # التشفير
│   ├── outputs/
│   │   ├── udp_output.py        # UDP Multicast
│   │   ├── http_output.py       # HTTP Streaming
│   │   ├── hls_output.py        # HLS
│   │   ├── srt_output.py        # SRT
│   │   └── rtsp_output.py       # RTSP
│   ├── monitoring/
│   │   ├── monitor.py           # المراقبة
│   │   ├── metrics.py           # المقاييس
│   │   └── alarm.py             # التنبيهات
│   ├── failover/
│   │   └── backup_manager.py    # النسخ الاحتياطي
│   ├── epg/
│   │   ├── epg_parser.py        # تحليل EPG
│   │   └── si_tables.py         # SI Tables
│   ├── api/
│   │   └── rest_api.py          # REST API
│   ├── scripting/
│   │   └── lua_engine.py        # محرك Lua
│   ├── config/
│   │   ├── config_manager.py    # إدارة الإعدادات
│   │   └── schemas.py           # مخطط البيانات
│   └── utils/
│       ├── logger.py            # السجلات
│       └── helpers.py           # الدوال المساعدة
├── tests/
│   └── test_*.py
├── docs/
│   ├── guides/
│   └── api/
├── requirements.txt
├── setup.py
└── main.py                       # نقطة الدخول الرئيسية
```

## الترخيص

MIT License
