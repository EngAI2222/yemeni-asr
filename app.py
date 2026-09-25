import streamlit as st
import re
import time
import tempfile
import os
from faster_whisper import WhisperModel

@st.cache_resource
def load_model():
    return WhisperModel("small", device="cpu", compute_type="int8")

model = load_model()

FINAL_RULES_REGEX = {
    r'\bفعص\b': 'فحص',
    r'\bعطوا فيه\b': 'عطل في',
    r'\bعطو فيه\b': 'عطل في',
    r'\bعطل فيلو تكلاف\b': 'عطل في الأوتوكلاف',
    r'\bفيلو تكلاف\b': 'في الأوتوكلاف',
    r'\bلو تكلاف\b': 'الأوتوكلاف',
    r'\bلوتوكلاف\b': 'الأوتوكلاف',
    r'\bوتهكب\b': 'وتوقف',
    r'\bوذهبوا في\b': 'وتوقف',
    r'\bحط الطعبة\b': 'خط التعبئة',
    r'\bحط الطعبية\b': 'خط التعبئة',
    r'\bالطعبة\b': 'التعبئة',
    r'\bالطعبية\b': 'التعبئة',
    r'\bآل التقليب\b': 'آلة تغليف',
    r'\bآل التقليفة\b': 'آلة تغليف',
    r'\bآلة تقليب\b': 'آلة تغليف',
    r'\bآلة تقريب\b': 'آلة تغليف',
    r'\bالشرائد\b': 'الشرائط',
    r'\bالشرايد\b': 'الشرائط',
    r'\bشرايط\b': 'شرائط',
    r'\bربع تجير\b': 'رفع تقرير',
    r'\bربع تجريج\b': 'رفع تقرير',
    r'\bربع تقليص\b': 'رفع تقرير',
    r'\bربع تقريب\b': 'رفع تقرير',
    r'\bربع تقرير\b': 'رفع تقرير',
    r'\bيومين\b': 'يومي',
    r'\bضغط الهواء\b': 'ضاغط الهواء',
    r'\bضاقة الهواء\b': 'ضاغط الهواء',
    r'\bالسيانة\b': 'الصيانة',
    r'\bسيانة\b': 'صيانة',
    r'\bصيامة\b': 'صيانة',
    r'\bتصرب\b': 'تسرب',
    r'\bتجغيل\b': 'تشغيل',
    r'\bتشريل\b': 'تشغيل',
    r'\bللفخص\b': 'للفحص',
    r'\bالفخص\b': 'الفحص',
    r'\bأدات\b': 'أداة',
    r'\bمعايرت\b': 'معايرة',
    r'\bالإسلاح\b': 'الإصلاح',
    r'\bللسيانة\b': 'للصيانة',
    r'\bالمعيدة\b': 'المعدة',
    r'\bالفدمة\b': 'الخدمة',
    r'\bفلتري\b': 'فلتر',
    r'\bاسناد\b': 'إسناد',
    r'\bخرارة\b': 'حرارة',
    r'\bتشهيم\b': 'تشحيم',
    r'\bالمستودة\b': 'المستودع',
    r'\bفارج\b': 'خارج',
    r'\bمطبوط\b': 'مضبوط',
    r'\bتجنيع\b': 'تجميع',
    r'\bالفحصة\b': 'الفحص',
    r'\bصخيخ\b': 'صحيح',
    r'\bاتفاع\b': 'ارتفاع',
    r'\bاستدال\b': 'استبدال',
    r'\bأمبوب\b': 'أنبوب',
    r'\bسشيه\b': 'ساشيه',
    r'\bسداد\b': 'انسداد',
    r'\bتلكيب\b': 'تركيب',
    r'\bالمستودعي\b': 'المستودع',
    r'\bالأُتُكلف\b': 'الأوتوكلاف',
    r'\bالأتكلف\b': 'الأوتوكلاف',
    r'\bالكمبلي صور\b': 'الكمبريسور',
    r'\bالكمبري صور\b': 'الكمبريسور',
    r'\bبلستر\b': 'بليستر',
    r'\bقطعة الغيار\b': 'قطعة غيار',
    r'\bتقريروا\b': 'تقرير',
    r'\bسيانات\b': 'صيانة',
    r'\bمصاحة\b': 'مساحة',
    r'\bفريط\b': 'فريق',
    r'\bالسيانات\b': 'الصيانة',
    r'\bجهز\b': 'جاهز',
    r'\bانخفادوا\b': 'انخفاض',
    r'\bضغطي\b': 'ضغط',
    r'\bامرسيانا\b': 'أمر الصيانة',
    r'\bفكوا\b': 'فك',
    r'\bأت\b': 'آلة',
}

def apply_rules(text):
    for pattern, replacement in FINAL_RULES_REGEX.items():
        text = re.sub(pattern, replacement, text)
    return text

def normalize(text):
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\.{2,}', '.', text)
    return text

def find_corrections(raw, final):
    raw_words = raw.split()
    final_words = final.split()
    corrections = []
    i, j = 0, 0
    while i < len(raw_words) and j < len(final_words):
        if raw_words[i] != final_words[j]:
            corrections.append((raw_words[i], final_words[j]))
        i += 1
        j += 1
    return corrections

st.set_page_config(
    page_title="نظام تحويل الصوت إلى نص",
    page_icon="🎙️",
    layout="wide"
)

st.markdown("""
<style>
    .main { direction: rtl; text-align: right; }
    .stTextArea textarea { direction: rtl; text-align: right; font-size: 18px; }
    h1, h2, h3 { text-align: right; }
</style>
""", unsafe_allow_html=True)

st.title("🎙️ نظام تحويل الصوت إلى نص")
st.markdown("#### تقارير الصيانة اليومية - لهجة يمنية")
st.markdown("---")

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 🎤 سجّل جملتك")
    audio_file = st.audio_input("اضغط للتسجيل")
    
    if audio_file is not None:
        if st.button("🔍 تحويل إلى نص", type="primary", use_container_width=True):
            with st.spinner("⏳ جاري المعالجة... (قد يستغرق 10-30 ثانية)"):
                try:
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                        tmp.write(audio_file.read())
                        audio_path = tmp.name
                    
                    start = time.time()
                    segments, info = model.transcribe(audio_path, language="ar", beam_size=5)
                    raw_text = " ".join(s.text for s in segments).strip()
                    after_rules = apply_rules(raw_text)
                    final_text = normalize(after_rules)
                    elapsed = time.time() - start
                    
                    os.unlink(audio_path)
                    
                    st.session_state['raw'] = raw_text
                    st.session_state['final'] = final_text
                    st.session_state['elapsed'] = elapsed
                    st.session_state['corrections'] = find_corrections(raw_text, final_text)
                except Exception as e:
                    st.error(f"❌ خطأ: {str(e)}")

with col2:
    if 'raw' in st.session_state:
        st.markdown("### 📝 النص الخام (قبل التصحيح)")
        st.text_area("raw", st.session_state['raw'], height=100, key="raw_out", label_visibility="collapsed")
        
        st.markdown("### ✨ النص النهائي (بعد التصحيح)")
        st.text_area("final", st.session_state['final'], height=100, key="final_out", label_visibility="collapsed")
        
        st.markdown("### 🔧 التصحيحات المُطبَّقة")
        corrections = st.session_state['corrections']
        if corrections:
            corr_text = " | ".join([f"{w} ← {r}" for w, r in corrections[:15]])
        else:
            corr_text = "لا توجد تصحيحات"
        st.text_area("corr", corr_text, height=80, key="corr_out", label_visibility="collapsed")
        
        st.markdown("### 📊 الإحصائيات")
        stats = f"⏱️ زمن المعالجة: {st.session_state['elapsed']:.2f} ثانية\n📊 عدد التصحيحات: {len(corrections)}"
        st.text_area("stats", stats, height=80, key="stats_out", label_visibility="collapsed")
    else:
        st.info("👈 سجّل صوتك من الجهة اليمنى، ثم اضغط **تحويل إلى نص**")
