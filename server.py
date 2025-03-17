from fastapi import FastAPI
import torch
from torch.nn import functional as F
from pydantic import BaseModel
from model import TransformerClassification  # مدل را از `model.py` لود می‌کنیم

app = FastAPI()

# **ستون‌های موردنیاز برای مدل**
column_names =['woman_age',
 'man_age',
 'woman_height',
 'man_height',
 'woman_weight',
 'man_weight',
 'woman_bmi',
 'man_bmi',
 'tubal_factors',
 'infertility_duration',
 'menstrual_disorders',
 'unexplained_infertility',
 'severe_pelvic_adhesion',
 'woman_endometriosis',
 'woman_baseline_fsh',
 'woman_baseline_lh',
 'baseline_prl',
 'baseline_amh',
 'woman_diabetes',
 'woman_hypertension',
 'man_diabetes',
 'man_hypertension',
 'woman_hypothyroidism',
 'man_hypothyroidism',
 'woman_anemia',
 'woman_laparotomy',
 'cyst_aspiration',
 'diagnostic_hysteroscopy',
 'woman_therapeutic_laparoscopy',
 'therapeutic_hysteroscopy',
 'pco',
 'hsg_uterine_cavity',
 'hydrosalpinx',
 'total_afc',
 'male_factor',
 'woman_hepatitis',
 'man_hepatitis',
 'endometrioma_history',
 'intramural_uterine_myoma',
 'subserosal_uterine_myoma',
 'submucosal_uterine_myoma',
 'woman_high_risk_job',
 'man_anemia',
 'man_fsh',
 'testicular_biopsy',
 'tese_outcome',
 'man_karyotype',
 'man_primary_infertility',
 'woman_primary_infertility',
 'man_secondary_infertility',
 'woman_secondary_infertility',
 'retrieved_oocytes_count',
 'transferred_embryos_count',
 'embryo_quality',
 'embryo_freezing_status',
 'embryo_morphology',
 'embryo_transfer_day',
 'man_high_risk_job',
 'salpingitis',
 'varicocele_surgery',
 'mother_smoking_and_opiates',
 'father_smoking_and_opiates',
 'father_alcohol_consumption',
 'mother_lupus_and_antiphospholipid_syndrome',
 'man_covid',
 'woman_covid',
 'man_covid_vaccination_history',
 "woman_covid_vaccination_history",
 'adenomyosis',
 'dfi',
 'man_vitamin_d',
 'woman_vitamin_d',
 'Endometrial_thickness',
 'endometrial_pattern',
 ]

# **تعریف مدل ورودی برای دریافت داده‌ها از کاربر**
class InputData(BaseModel):
    woman_age:float
    man_age:float
    woman_height:float
    man_height:float
    woman_weight:float
    man_weight:float
    woman_bmi:float
    man_bmi:float
    tubal_factors:float
    infertility_duration:float
    menstrual_disorders:float
    unexplained_infertility:float
    severe_pelvic_adhesion:float
    woman_endometriosis:float
    woman_baseline_fsh:float
    woman_baseline_lh:float
    baseline_prl:float
    baseline_amh:float
    woman_diabetes:float
    woman_hypertension:float
    man_diabetes:float
    man_hypertension:float
    woman_hypothyroidism:float
    man_hypothyroidism:float
    woman_anemia:float
    woman_laparotomy:float
    cyst_aspiration:float
    diagnostic_hysteroscopy:float
    woman_therapeutic_laparoscopy:float
    therapeutic_hysteroscopy:float
    pco:float
    hsg_uterine_cavity:float
    hydrosalpinx:float
    total_afc:float
    male_factor:float
    woman_hepatitis:float
    man_hepatitis:float
    endometrioma_history:float
    intramural_uterine_myoma:float
    subserosal_uterine_myoma:float
    submucosal_uterine_myoma:float
    woman_high_risk_job:float
    man_anemia:float
    man_fsh:float
    testicular_biopsy:float
    tese_outcome:float
    man_karyotype:float
    man_primary_infertility:float
    woman_primary_infertility:float
    man_secondary_infertility:float
    woman_secondary_infertility:float
    retrieved_oocytes_count:float
    transferred_embryos_count:float
    embryo_quality:float
    embryo_freezing_status:float
    embryo_morphology:float
    embryo_transfer_day:float
    man_high_risk_job:float
    salpingitis:float
    varicocele_surgery:float
    mother_smoking_and_opiates:float
    father_smoking_and_opiates:float
    father_alcohol_consumption:float
    mother_lupus_and_antiphospholipid_syndrome:float
    man_covid:float
    woman_covid:float
    man_covid_vaccination_history:float
    woman_covid_vaccination_history:float
    adenomyosis:float
    dfi:float
    man_vitamin_d:float
    woman_vitamin_d:float
    Endometrial_thickness:float
    endometrial_pattern:float
    

# **بارگذاری مدل**
input_dim = len(column_names)
print("******************************",input_dim)
hidden_dim = input_dim
num_heads = 2
num_layers = 3
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = TransformerClassification(input_dim=input_dim, hidden_dim=hidden_dim, num_heads=num_heads, num_layers=num_layers).to(device)
model.load_state_dict(torch.load("best_model.pth", map_location=device))
model.eval()

@app.post("/predict/")
async def predict(data: InputData):
    try:
        # **تبدیل داده‌های ورودی به لیست و سپس `Tensor`**
        input_values = [getattr(data, col) for col in column_names]
        print(input_values)
        X_tensor = torch.tensor([input_values], dtype=torch.float32).to(device)

        # **پیش‌بینی مدل**
        with torch.no_grad():
            outputs = model(X_tensor)
            predictions = F.softmax(outputs, dim=1)[:, 1]  # احتمال موفقیت (برچسب 1)
            y_pred = (predictions > 0.5).int().cpu().numpy()

        # **محاسبه درصد موفقیت و عدم موفقیت**
        success_rate = predictions.item() * 100  # درصد موفقیت
        failure_rate = 100 - success_rate  # درصد عدم موفقیت

        return {
            "success_rate": round(success_rate, 2),
            "failure_rate": round(failure_rate, 2)
        }
    
    except Exception as e:
        return {"error": str(e)}

