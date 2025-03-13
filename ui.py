import streamlit as st
import requests

st.title("💡 پیش‌بینی موفقیت باروری")
st.write("🔢 لطفاً اطلاعات زیر را وارد کنید:")

# 📌 دسته‌بندی ویژگی‌ها برای راحتی کاربر
st.header("👩‍⚕️ اطلاعات عمومی زن و مرد")
user_data = {
    "woman_age": st.number_input("👩 سن زن (سال)", min_value=18, max_value=50, value=30),
    "man_age": st.number_input("👨 سن مرد (سال)", min_value=18, max_value=70, value=35),
    "woman_height": st.number_input("📏 قد زن (سانتی‌متر)", min_value=130, max_value=200, value=160),
    "man_height": st.number_input("📏 قد مرد (سانتی‌متر)", min_value=130, max_value=210, value=175),
    "woman_weight": st.number_input("⚖️ وزن زن (کیلوگرم)", min_value=40, max_value=150, value=60),
    "man_weight": st.number_input("⚖️ وزن مرد (کیلوگرم)", min_value=50, max_value=200, value=80),
    "woman_bmi": st.number_input("🔢 BMI زن", min_value=15.0, max_value=40.0, value=22.0),
    "man_bmi": st.number_input("🔢 BMI مرد", min_value=15.0, max_value=40.0, value=24.0)
}

st.header("⚕️ وضعیت پزشکی و بیماری‌ها")
medical_features = [
    "tubal_factors", "infertility_duration", "menstrual_disorders", "unexplained_infertility",
    "severe_pelvic_adhesion", "woman_endometriosis", "woman_diabetes", "woman_hypertension",
    "man_diabetes", "man_hypertension", "woman_hypothyroidism", "man_hypothyroidism",
    "woman_anemia", "man_anemia", "woman_hepatitis", "man_hepatitis",
    "endometrioma_history", "intramural_uterine_myoma", "subserosal_uterine_myoma",
    "submucosal_uterine_myoma", "woman_high_risk_job", "man_high_risk_job"
]
for feature in medical_features:
    user_data[feature] = st.radio(f"🩺 {feature.replace('_', ' ').title()}?", [0, 1])

st.header("🧪 آزمایشات هورمونی")
hormonal_features = ["woman_baseline_fsh", "woman_baseline_lh", "baseline_prl", "baseline_amh", "man_fsh"]
for feature in hormonal_features:
    user_data[feature] = st.number_input(f"🧪 {feature.replace('_', ' ').title()}", min_value=0.0, max_value=100.0, value=10.0)

st.header("🩸 آزمایشات و شرایط بالینی")
clinical_features = [
    "cyst_aspiration", "diagnostic_hysteroscopy", "woman_therapeutic_laparoscopy",
    "therapeutic_hysteroscopy", "pco", "hsg_uterine_cavity", "hydrosalpinx",
    "total_afc", "male_factor", "testicular_biopsy", "tese_outcome", "man_karyotype",
    "salpingitis", "varicocele_surgery", "mother_smoking_and_opiates",
    "father_smoking_and_opiates", "father_alcohol_consumption",
    "mother_lupus_and_antiphospholipid_syndrome", "man_covid", "woman_covid",
    "man_covid_vaccination_history", "adenomyosis", "dfi", "man_vitamin_d",
    "woman_vitamin_d", "Endometrial_thickness", "endometrial_pattern", "pap_smear"
]
for feature in clinical_features:
    user_data[feature] = st.radio(f"🩺 {feature.replace('_', ' ').title()}?", [0, 1])

st.header("👶 وضعیت باروری و IVF")
fertility_features = [
    "man_primary_infertility", "woman_laparotomy","woman_primary_infertility", "man_secondary_infertility", "woman_secondary_infertility",
    "retrieved_oocytes_count", "transferred_embryos_count", "embryo_quality",
    "embryo_freezing_status", "embryo_morphology", "embryo_transfer_day"
]
for feature in fertility_features:
    user_data[feature] = st.number_input(f"👶 {feature.replace('_', ' ').title()}", min_value=0, max_value=50, value=5)

# **ایجاد دکمه برای ارسال اطلاعات به سرور**
if st.button("📊 پیش‌بینی موفقیت"):
    response = requests.post("http://127.0.0.1:8000/predict/", json=user_data)

    if response.status_code == 200:
        result = response.json()
        st.success(f"✅ **درصد موفقیت:** {result['success_rate']}%")
        st.error(f"❌ **درصد ناموفق:** {result['failure_rate']}%")
    else:
        st.error("❌ خطا در پردازش داده‌ها! لطفاً دوباره تلاش کنید.")
