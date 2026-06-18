
from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from pathlib import Path
import sqlite3, datetime, csv, io

BASE_DIR = Path(__file__).resolve().parent
DB = BASE_DIR / "ipgms_final_system.db"
BACKUP_DIR = BASE_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.secret_key = "ipgms-web-portal-secret"

PROJECT_STATUS = ["تخطيط","إحالة","تنفيذ","استلام جزئي","استلام أولي","ضمن الصيانة","استلام نهائي","منجز","مغلق","ملغى","قيد التنفيذ","محال","مدرج","معلن"]
PROJECT_CONDITION = ["طبيعي","متأخر","متلكئ","متوقف","ضمن الخطة","متقدم عن الخطة","حرج","مسحوب من المقاول"]
IMPORTANCE = ["اعتيادي","مهم","استراتيجي","برنامج حكومي","مشروع حرج"]

TABLE_LABELS = {
"projects_master":"المشاريع الرئيسية","contracts":"التعاقدات ومعايير التأهيل","execution_projects":"المشاريع قيد التنفيذ",
"monitoring":"المراقبة والسيطرة","critical_factors":"تقييم العوامل الحرجة 18","oversight":"الرقابة المالية والنزاهة",
"lab_tests":"الفحوصات المختبرية","variations":"أوامر الغيار والتمديدات","payments":"المستخلصات والمدفوعات",
"claims":"المطالبات والنزاعات","risks":"المخاطر","maintenance":"الصيانة","documents":"الوثائق والكتب الرسمية",
"project_files":"إدارة الوثائق والملفات","gis":"GIS","funding_allocations":"التمويل والتخصيصات",
"land":"الأراضي والاستملاك LRI","listed_projects":"المشاريع المدرجة","indicators":"المؤشرات الذكية",
"meetings":"سجل الاجتماعات","site_visits":"سجل الزيارات الميدانية","decisions":"القرارات التنفيذية","lessons":"الدروس المستفادة"
}
DISPLAY_TABLES = list(TABLE_LABELS.keys())
FIELD_LABELS = {'id': 'المعرف',
 'project_id': 'المشروع',
 'created_at': 'تاريخ الإنشاء',
 'updated_at': 'تاريخ التحديث',
 'last_login': 'آخر دخول',
 'is_active': 'فعال',
 'username': 'اسم المستخدم',
 'password': 'كلمة المرور',
 'role': 'الدور',
 'governorate_scope': 'صلاحية المحافظة',
 'entity_scope': 'صلاحية الجهة',
 'project_seq': 'التسلسل',
 'project_no': 'رقم المشروع',
 'project_name': 'اسم المشروع',
 'sector': 'القطاع',
 'governorate': 'المحافظة',
 'executing_entity': 'الجهة المنفذة',
 'beneficiary_entity': 'الجهة المستفيدة',
 'funding_source': 'مصدر التمويل',
 'project_status': 'حالة المشروع',
 'project_condition': 'موقف المشروع',
 'importance_level': 'الأهمية',
 'estimated_cost': 'الكلفة التخمينية',
 'consultant': 'الاستشاري',
 'contractor': 'الشركة المنفذة',
 'notes': 'ملاحظات',
 'plot_no': 'رقم القطعة',
 'district_land': 'المقاطعة',
 'qadha': 'القضاء',
 'subdistrict': 'الناحية',
 'area': 'المساحة',
 'ownership_status': 'حالة الملكية',
 'encroachments': 'التجاوزات',
 'utilities_conflict': 'تعارض الخدمات',
 'legal_cases': 'الدعاوى القانونية',
 'acquisition_status': 'حالة الاستملاك',
 'security_conflict': 'تعارض أمني',
 'lri_score': 'مؤشر جاهزية الأرض LRI %',
 'lri_status': 'حالة LRI',
 'project_plan_no': 'رقم المشروع بالخطة',
 'execution_duration': 'مدة التنفيذ',
 'financial_allocation': 'التخصيص المالي',
 'listed_status': 'حالة الإدراج',
 'year': 'السنة',
 'allocation_amount': 'مبلغ التخصيص',
 'spent_amount': 'المبلغ المصروف',
 'remaining_amount': 'المبلغ المتبقي',
 'funding_status': 'حالة التمويل',
 'prequalification_required': 'هل يوجد تأهيل مسبق',
 'prequalification_no': 'رقم وثيقة التأهيل المسبق',
 'prequalification_date': 'تاريخ التأهيل المسبق',
 'prequalification_result': 'نتيجة التأهيل المسبق',
 'annual_revenue': 'الإيراد السنوي',
 'cash_liquidity': 'السيولة النقدية',
 'financial_efficiency': 'الكفاءة المالية',
 'final_accounts': 'الحسابات الختامية',
 'specialized_experience': 'الخبرة التخصصية',
 'similar_works_count': 'عدد الأعمال المماثلة',
 'similar_works_amount': 'مبلغ الأعمال المماثلة',
 'staff': 'الكوادر',
 'equipment': 'المعدات',
 'contract_method': 'أسلوب التعاقد',
 'execution_method': 'أسلوب التنفيذ',
 'referral_date': 'تاريخ الإحالة',
 'referral_amount': 'مبلغ الإحالة',
 'implementation_duration': 'مدة التنفيذ',
 'contract_duration': 'مدة العقد',
 'contract_cost': 'كلفة العقد',
 'contract_sign_date': 'تاريخ توقيع العقد',
 'commencement_date': 'تاريخ المباشرة',
 'planned_completion_date': 'تاريخ الإنجاز المخطط',
 'qualification_status': 'حالة التأهيل',
 'cri_score': 'مؤشر مخاطر التأهيل CRI %',
 'time_progress': 'نسبة الإنجاز الزمني %',
 'financial_progress': 'نسبة الإنجاز المالي %',
 'financial_deviation': 'الانحراف المالي %',
 'time_deviation': 'الانحراف الزمني %',
 'payment_status': 'حالة المستخلصات',
 'resident_engineer_name': 'اسم المهندس المقيم',
 'resident_engineer_mobile': 'هاتف المهندس المقيم',
 'spi': 'مؤشر الجدول SPI',
 'cpi': 'مؤشر الكلفة CPI',
 'quality_index': 'مؤشر الجودة',
 'risk_index': 'مؤشر المخاطر',
 'variation_index': 'مؤشر أوامر الغيار',
 'extension_index': 'مؤشر التمديدات',
 'payments_index': 'مؤشر المستخلصات',
 'factors_total': 'تقييم العوامل الحرجة',
 'phi': 'مؤشر صحة المشروع PHI %',
 'early_warning': 'الإنذار المبكر',
 'recommendation': 'التوصية',
 'test_type': 'نوع الفحص',
 'tested_material': 'المادة المفحوصة',
 'sampling_method': 'طريقة النمذجة',
 'testing_laboratory': 'المختبر الفاحص',
 'test_request_book_no': 'رقم كتاب طلب الفحص',
 'test_request_book_date': 'تاريخ كتاب طلب الفحص',
 'test_result': 'نتيجة الفحص',
 'result_book_no': 'رقم كتاب النتيجة',
 'result_book_date': 'تاريخ كتاب النتيجة',
 'compliance_percentage': 'نسبة المطابقة %',
 'test_status': 'حالة الفحص',
 'variation_no': 'رقم أمر الغيار',
 'variation_date': 'تاريخ أمر الغيار',
 'variation_reason': 'سبب أمر الغيار',
 'original_cost': 'الكلفة الأصلية',
 'requested_cost': 'الكلفة المطلوبة',
 'cost_increase_percentage': 'نسبة زيادة الكلفة %',
 'requested_extension': 'التمديد المطلوب',
 'approval_entity': 'جهة الموافقة',
 'approval_book_no': 'رقم كتاب الموافقة',
 'approval_date': 'تاريخ المصادقة',
 'request_status': 'حالة الطلب',
 'vii_score': 'مؤشر أوامر الغيار VII %',
 'certificate_no': 'رقم المستخلص',
 'submit_date': 'تاريخ التقديم',
 'payment_date': 'تاريخ الصرف',
 'amount': 'المبلغ',
 'payment_delay_days': 'مدة تأخر الصرف/يوم',
 'claim_type': 'نوع المطالبة',
 'dispute_party': 'طرف النزاع',
 'claim_amount': 'مبلغ المطالبة',
 'claim_days': 'أيام المطالبة',
 'claim_status': 'حالة المطالبة',
 'description': 'الوصف',
 'decision': 'القرار',
 'risk_no': 'رقم الخطر',
 'risk_type': 'نوع الخطر',
 'risk_description': 'وصف الخطر',
 'probability': 'الاحتمالية',
 'impact': 'التأثير',
 'risk_level': 'مستوى الخطورة',
 'mitigation_plan': 'خطة المعالجة',
 'responsible': 'المسؤول',
 'status': 'الحالة',
 'preliminary_handover_date': 'تاريخ الاستلام الأولي',
 'final_handover_date': 'تاريخ الاستلام النهائي',
 'contractual_maintenance_months': 'مدة الصيانة التعاقدية/شهر',
 'maintenance_end_date': 'تاريخ انتهاء الصيانة',
 'maintenance_status': 'حالة الصيانة',
 'preventive_details': 'تفاصيل الصيانة الوقائية',
 'planned_details': 'تفاصيل الصيانة المخططة',
 'emergency_details': 'تفاصيل الصيانة الطارئة',
 'compliance': 'نسبة الالتزام %',
 'availability': 'نسبة الجاهزية %',
 'doc_type': 'نوع الوثيقة',
 'book_no': 'رقم الكتاب',
 'book_date': 'تاريخ الكتاب',
 'issuing_entity': 'الجهة الصادرة',
 'receiving_entity': 'الجهة المستلمة',
 'subject': 'الموضوع',
 'file_path': 'مسار الملف',
 'file_type': 'نوع الملف',
 'file_title': 'عنوان الملف',
 'file_no': 'رقم الملف',
 'file_date': 'تاريخ الملف',
 'file_category': 'تصنيف الملف',
 'archive_location': 'موقع الأرشفة',
 'meeting_no': 'رقم الاجتماع',
 'meeting_date': 'تاريخ الاجتماع',
 'meeting_type': 'نوع الاجتماع',
 'attendees': 'الحاضرون',
 'minutes': 'محضر الاجتماع',
 'actions': 'الإجراءات',
 'visit_no': 'رقم الزيارة',
 'visit_date': 'تاريخ الزيارة',
 'visit_team': 'فريق الزيارة',
 'visit_purpose': 'غرض الزيارة',
 'findings': 'الملاحظات الميدانية',
 'corrective_actions': 'الإجراءات التصحيحية',
 'latitude': 'خط العرض Latitude',
 'longitude': 'خط الطول Longitude',
 'location_notes': 'ملاحظات الموقع',
 'inquiry_entity': 'جهة الاستفسار',
 'inquiry_type': 'نوع الاستفسار',
 'inquiry_book_no': 'رقم كتاب الاستفسار',
 'inquiry_book_date': 'تاريخ كتاب الاستفسار',
 'inquiry_subject': 'موضوع الاستفسار',
 'answer_book_no': 'رقم كتاب الجواب',
 'answer_book_date': 'تاريخ كتاب الجواب',
 'answer_summary': 'ملخص الجواب',
 'followup_status': 'موقف المتابعة',
 'factor_no': 'رقم العامل',
 'factor_name': 'العامل الحرج',
 'score': 'التقييم'}

def label(c):
    if c in FIELD_LABELS:
        return FIELD_LABELS[c]
    fallback = str(c).replace("_", " ")
    return "حقل " + fallback
def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con
def columns(table):
    con=db(); cols=[r["name"] for r in con.execute(f"PRAGMA table_info({table})")]; con.close(); return cols
def pk_col(table):
    cols=columns(table)
    if table=="projects_master" and "project_id" in cols: return "project_id"
    if "id" in cols: return "id"
    return cols[0]
def table_exists(table):
    con=db(); row=con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?",(table,)).fetchone(); con.close(); return row is not None
def project_options():
    con=db(); rows=con.execute("SELECT project_id, project_no, project_name FROM projects_master ORDER BY CAST(project_seq AS INTEGER)").fetchall(); con.close(); return rows
def build_filter_sql(alias="pm"):
    wh=[]; vals=[]; p=alias+"."
    for key,col in [("project_no","project_no"),("governorate","governorate"),("sector","sector"),("project_status","project_status"),("project_condition","project_condition"),("importance_level","importance_level")]:
        val=request.args.get(key,"").strip()
        if val:
            if key=="project_no": wh.append(f"{p}{col} LIKE ?"); vals.append("%"+val+"%")
            else: wh.append(f"{p}{col}=?"); vals.append(val)
    q=request.args.get("q","").strip()
    if q:
        wh.append(f"({p}project_no LIKE ? OR {p}project_name LIKE ? OR {p}executing_entity LIKE ?)")
        vals += ["%"+q+"%"]*3
    return (" WHERE "+" AND ".join(wh) if wh else ""), vals

def require_login():
    if not session.get("user"): return redirect(url_for("login"))

@app.context_processor
def inject():
    return dict(TABLE_LABELS=TABLE_LABELS, DISPLAY_TABLES=DISPLAY_TABLES, label=label, PROJECT_STATUS=PROJECT_STATUS, PROJECT_CONDITION=PROJECT_CONDITION, IMPORTANCE=IMPORTANCE)

@app.route("/")
def index():
    return redirect(url_for("dashboard") if session.get("user") else url_for("login"))

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        con=db()
        u=con.execute("SELECT * FROM users WHERE username=? AND password=? AND (is_active=1 OR is_active='1' OR is_active IS NULL)",(request.form.get("username",""),request.form.get("password",""))).fetchone()
        con.close()
        if u:
            session["user"]=u["username"]; session["role"]=u["role"]; return redirect(url_for("dashboard"))
        flash("اسم المستخدم أو كلمة المرور غير صحيحة")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if not session.get("user"): return redirect(url_for("login"))
    con=db()
    total=con.execute("SELECT COUNT(*) n FROM projects_master").fetchone()["n"]
    cost=con.execute("SELECT COALESCE(SUM(estimated_cost),0) s FROM projects_master").fetchone()["s"]
    status_rows=con.execute("SELECT project_status,COUNT(*) n FROM projects_master GROUP BY project_status").fetchall()
    projects=con.execute("""SELECT pm.project_seq,pm.project_no,pm.project_name,pm.project_status,pm.project_condition,
    COALESCE(e.time_progress,0) time_progress,COALESCE(e.financial_progress,0) financial_progress,COALESCE(m.phi,0) phi
    FROM projects_master pm LEFT JOIN execution_projects e ON pm.project_id=e.project_id
    LEFT JOIN monitoring m ON pm.project_id=m.project_id ORDER BY CAST(pm.project_seq AS INTEGER)""").fetchall()
    con.close()
    return render_template("dashboard.html",total=total,cost=cost,status_rows=status_rows,projects=projects)

@app.route("/table/<table>")
def table_view(table):
    if not session.get("user"): return redirect(url_for("login"))
    if table not in DISPLAY_TABLES or not table_exists(table): return "Not found",404
    con=db()
    if table=="projects_master":
        wh,vals=build_filter_sql("pm")
        rows=con.execute("SELECT pm.* FROM projects_master pm "+wh+" ORDER BY CAST(pm.project_seq AS INTEGER)",vals).fetchall()
        cols=columns(table)
    elif "project_id" in columns(table):
        wh,vals=build_filter_sql("pm")
        rows=con.execute(f"""SELECT t.*, pm.project_seq,pm.project_no,pm.project_name,pm.sector,pm.governorate,pm.executing_entity,pm.project_status,pm.project_condition,pm.importance_level
        FROM {table} t JOIN projects_master pm ON t.project_id=pm.project_id {wh} ORDER BY CAST(pm.project_seq AS INTEGER), t.{pk_col(table)}""",vals).fetchall()
        base=["project_seq","project_no","project_name","sector","governorate","executing_entity","project_status","project_condition","importance_level"]
        cols=base+[c for c in columns(table) if c not in ("project_id",) and c not in base]
    else:
        rows=con.execute(f"SELECT * FROM {table}").fetchall(); cols=columns(table)
    con.close()
    return render_template("table.html",table=table,rows=rows,cols=cols,pk=pk_col(table),projects=project_options())

@app.route("/edit/<table>/<rid>", methods=["GET","POST"])
def edit_record(table,rid):
    if not session.get("user"): return redirect(url_for("login"))
    cols=columns(table); pk=pk_col(table); con=db()
    if request.method=="POST":
        editable=[c for c in cols if c!=pk and c not in ("created_at","updated_at")]
        vals=[request.form.get(c,"") for c in editable]
        if "updated_at" in cols:
            sql=f"UPDATE {table} SET "+",".join([f"{c}=?" for c in editable])+",updated_at=? WHERE "+pk+"=?"
            vals += [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), rid]
        else:
            sql=f"UPDATE {table} SET "+",".join([f"{c}=?" for c in editable])+" WHERE "+pk+"=?"; vals.append(rid)
        con.execute(sql,vals); con.commit(); con.close(); flash("تم التحديث"); return redirect(url_for("table_view",table=table))
    row=con.execute(f"SELECT * FROM {table} WHERE {pk}=?",(rid,)).fetchone(); con.close()
    return render_template("edit.html",table=table,row=row,cols=cols,pk=pk,projects=project_options())

@app.route("/new/<table>", methods=["GET","POST"])
def new_record(table):
    if not session.get("user"): return redirect(url_for("login"))
    cols=columns(table); pk=pk_col(table); con=db()
    if request.method=="POST":
        editable=[c for c in cols if c!=pk and c not in ("created_at","updated_at")]
        vals=[request.form.get(c,"") for c in editable]
        if "created_at" in cols:
            editable += ["created_at","updated_at"]; vals += [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")]*2
        con.execute(f"INSERT INTO {table}({','.join(editable)}) VALUES({','.join(['?']*len(editable))})",vals)
        con.commit(); con.close(); flash("تمت الإضافة"); return redirect(url_for("table_view",table=table))
    return render_template("edit.html",table=table,row=None,cols=cols,pk=pk,projects=project_options())

@app.route("/delete/<table>/<rid>", methods=["POST"])
def delete_record(table,rid):
    if not session.get("user"): return redirect(url_for("login"))
    con=db(); con.execute(f"DELETE FROM {table} WHERE {pk_col(table)}=?",(rid,)); con.commit(); con.close(); flash("تم الحذف"); return redirect(url_for("table_view",table=table))

@app.route("/backup")
def backup():
    if not session.get("user"): return redirect(url_for("login"))
    target=BACKUP_DIR/("ipgms_web_backup_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S")+".db")
    src=sqlite3.connect(DB); dst=sqlite3.connect(target); src.backup(dst); dst.close(); src.close()
    return send_file(target,as_attachment=True)

@app.route("/export/<table>")
def export_csv(table):
    if not session.get("user"): return redirect(url_for("login"))
    con=db(); rows=con.execute(f"SELECT * FROM {table}").fetchall(); cols=columns(table); con.close()
    output=io.StringIO(); w=csv.writer(output); w.writerow([label(c) for c in cols])
    for r in rows: w.writerow([r[c] for c in cols])
    return send_file(io.BytesIO(output.getvalue().encode("utf-8-sig")),mimetype="text/csv",as_attachment=True,download_name=f"{table}.csv")


CRITICAL_FACTOR_NAMES = ['جاهزية الأرض ورفع التجاوزات', 'اكتمال التصاميم النهائية', 'وثائق المناقصة والمواصفات', 'دراسة الجدوى والقيمة مقابل المال', 'طريقة التعاقد والتنفيذ', 'الخبرة المماثلة للمقاول', 'الكفاءة المالية والسيولة', 'جاهزية التخصيصات والتمويل', 'متابعة البرنامج الزمني', 'مراقبة التدفق النقدي', 'حيادية وكفاءة الاستشاري', 'وضوح الصلاحيات الإدارية', 'مراقبة انحراف الكلفة', 'كفاءة قيادة المشروع', 'التنسيق المؤسسي', 'سرعة حسم المطالبات والنزاعات', 'سرعة صرف المستخلصات', 'خطط الطوارئ وإدارة المخاطر']

def cfi_status_value(cfi):
    try: v=float(cfi)
    except Exception: v=0
    if v>=80: return "ممتاز"
    if v>=60: return "جيد"
    if v>=40: return "يحتاج متابعة"
    return "عالي الخطورة"

def calculate_cfi(project_id, con=None):
    own=False
    if con is None:
        con=db(); own=True
    row=con.execute("SELECT SUM(COALESCE(score,0)*COALESCE(weight,1)) s, SUM(5*COALESCE(weight,1)) m FROM critical_factors WHERE project_id=?", (project_id,)).fetchone()
    s=row["s"] or 0; m=row["m"] or 0
    cfi=round((float(s)/float(m))*100,2) if m else 0
    mon=con.execute("SELECT id FROM monitoring WHERE project_id=? ORDER BY id DESC LIMIT 1", (project_id,)).fetchone()
    if mon:
        try:
            con.execute("UPDATE monitoring SET factors_total=? WHERE id=?", (cfi, mon["id"]))
            con.commit()
        except Exception:
            pass
    if own: con.close()
    return cfi

@app.route("/critical-factors", methods=["GET","POST"])
def critical_factors_page():
    if not session.get("user"): return redirect(url_for("login"))
    con=db()
    projects=con.execute("SELECT project_id, project_no, project_name, sector, governorate, project_status, project_condition FROM projects_master ORDER BY CAST(project_seq AS INTEGER)").fetchall()
    pid=request.values.get("project_id")
    if not pid and projects:
        pid=str(projects[0]["project_id"])

    if request.method=="POST":
        action=request.form.get("action")
        pid=request.form.get("project_id")
        if action=="generate":
            for i,name in enumerate(CRITICAL_FACTOR_NAMES,1):
                row=con.execute("SELECT id FROM critical_factors WHERE project_id=? AND factor_no=?", (pid,i)).fetchone()
                if not row:
                    con.execute("INSERT INTO critical_factors(project_id,factor_no,factor_name,score,weight,result,status,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,datetime('now'),datetime('now'))", (pid,i,name,3,1,3,"متوسط",""))
                else:
                    con.execute("UPDATE critical_factors SET factor_name=?, weight=COALESCE(weight,1), result=COALESCE(score,0)*COALESCE(weight,1) WHERE id=?", (name,row["id"]))
            con.commit()
            flash("تم إدراج/تحديث العوامل الـ18")
        elif action=="save":
            ids=request.form.getlist("id")
            for fid in ids:
                score=request.form.get(f"score_{fid}","3")
                weight=request.form.get(f"weight_{fid}","1")
                status=request.form.get(f"status_{fid}","متوسط")
                notes=request.form.get(f"notes_{fid}","")
                try: result=float(score)*float(weight)
                except Exception: result=0
                con.execute("UPDATE critical_factors SET score=?, weight=?, result=?, status=?, notes=?, updated_at=datetime('now') WHERE id=?", (score,weight,result,status,notes,fid))
            con.commit()
            flash("تم حفظ تقييم العوامل")
        cfi=calculate_cfi(pid, con)
        con.commit()
        return redirect(url_for("critical_factors_page", project_id=pid))

    rows=[]
    cfi=0
    if pid:
        rows=con.execute("SELECT * FROM critical_factors WHERE project_id=? ORDER BY factor_no", (pid,)).fetchall()
        cfi=calculate_cfi(pid, con)
    con.close()
    return render_template("critical_factors.html", projects=projects, selected_project_id=str(pid), rows=rows, cfi=cfi, cfi_status=cfi_status_value(cfi))

if __name__=="__main__":
    app.run(debug=True,host="127.0.0.1",port=5000)
