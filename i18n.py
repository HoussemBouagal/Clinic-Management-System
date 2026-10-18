# i18n.py
# ملف الترجمات لثلاث لغات: العربية / الإنجليزية / الفرنسية

TRANSLATIONS = {
    # ═══════════════════════════════════════════════════════════
    #                          العربية
    # ═══════════════════════════════════════════════════════════
    "ar": {
        # App
        "app": "نظام إدارة العيادة الطبية",
        "clinic_name": "عيادة النور الطبية",
        "dashboard": "لوحة التحكم", "patients": "المرضى", "appointments": "المواعيد",
        "records": "الملفات الطبية", "billing": "الفواتير", "inventory": "المخزون",
        "expenses": "المصروفات", "reports": "التقارير", "settings": "الإعدادات",
        "language": "Français", "logout": "تسجيل الخروج",

        # Login
        "login_title": "تسجيل الدخول",
        "login_subtitle": "يرجى إدخال بيانات الدخول للمتابعة",
        "username": "اسم المستخدم", "password": "كلمة المرور",
        "login": "دخول", "exit": "خروج",
        "login_error": "اسم المستخدم أو كلمة المرور غير صحيحة.",
        "login_empty": "يرجى إدخال اسم المستخدم وكلمة المرور.",
        "show_password": "إظهار كلمة المرور",
        "welcome_back": "مرحبًا بك",

        # Generic
        "id": "الرقم", "name": "الاسم الكامل", "phone": "الهاتف", "birth": "تاريخ الميلاد",
        "address": "العنوان", "notes": "ملاحظات", "save": "حفظ", "cancel": "إلغاء",
        "delete": "حذف", "edit": "تعديل", "add": "إضافة", "search": "بحث",
        "date": "التاريخ", "time": "الوقت", "status": "الحالة", "total": "الإجمالي",
        "actions": "إجراءات", "close": "إغلاق", "print": "طباعة", "export": "تصدير",
        "confirm_delete": "هل أنت متأكد من الحذف؟",
        "select_row": "يرجى تحديد سجل أولًا.",
        "saved": "تم الحفظ بنجاح.", "updated": "تم التحديث بنجاح.",
        "required_name": "يرجى إدخال الاسم.",
        "no_patients": "لا يوجد مرضى مسجلون.",

        # Dashboard
        "welcome": "مرحبًا بك في نظام إدارة العيادة",
        "patient_count": "إجمالي المرضى",
        "today_count": "مواعيد اليوم",
        "income": "إيرادات اليوم",
        "stock_alert": "تنبيهات المخزون",
        "expired_items": "أدوية منتهية",
        "month_revenue": "إيرادات الشهر",
        "net_profit": "الربح الصافي (اليوم)",
        "total_expenses": "مصروفات اليوم",
        "quick_stats": "إحصائيات سريعة",

        # Patients
        "add_patient": "إضافة مريض",
        "edit_patient": "تعديل بيانات المريض",
        "search_patients": "ابحث بالاسم أو الهاتف...",
        "blood_type": "فصيلة الدم", "allergies": "الحساسية",
        "chronic_diseases": "الأمراض المزمنة",

        # Appointments
        "add_appointment": "حجز موعد", "patient": "المريض",
        "reason": "سبب الزيارة", "conflict": "هذا الموعد يتعارض مع موعد آخر.",
        "appointment_saved": "تم حفظ الموعد.",
        "scheduled": "مجدول", "completed": "مكتمل", "cancelled": "ملغى",

        # Records
        "add_record": "إضافة ملف طبي", "edit_record": "تعديل ملف طبي",
        "visit_date": "تاريخ الزيارة", "diagnosis": "التشخيص",
        "prescription": "الوصفة الطبية", "blood_pressure": "ضغط الدم",
        "temperature": "الحرارة (°C)", "weight": "الوزن (kg)",
        "sugar_level": "السكر (mg/dL)", "heart_rate": "نبضات القلب",
        "view_record": "عرض التفاصيل", "record_saved": "تم حفظ الملف الطبي.",
        "select_patient_first": "يرجى اختيار مريض أولًا.",
        "patient_history": "سجل المريض الطبي",

        # Inventory
        "add_item": "إضافة عنصر", "edit_item": "تعديل عنصر",
        "item_name": "اسم الدواء", "category": "الفئة",
        "quantity": "الكمية", "min_quantity": "الحد الأدنى",
        "purchase_price": "سعر الشراء", "sale_price": "سعر البيع",
        "expiry_date": "تاريخ الانتهاء", "supplier": "المورد",
        "batch_number": "رقم الدفعة",
        "low_stock": "مخزون منخفض", "expired": "منتهي الصلاحية",
        "item_saved": "تم حفظ العنصر.",
        "category_med": "أدوية", "category_supplies": "مستلزمات",
        "category_equipment": "أجهزة",

        # Billing
        "new_invoice": "فاتورة جديدة", "invoice_date": "تاريخ الفاتورة",
        "subtotal": "المجموع الفرعي", "discount": "الخصم",
        "tax": "الضريبة", "paid": "المدفوع", "remaining": "المتبقي",
        "payment_method": "طريقة الدفع", "cash": "نقدًا", "card": "بطاقة",
        "transfer": "تحويل", "unpaid": "غير مدفوعة", "partial": "جزئية",
        "paid_status": "مدفوعة", "add_line": "إضافة بند",
        "remove_line": "حذف البند", "description": "الوصف",
        "unit_price": "سعر الوحدة", "line_total": "المجموع",
        "invoice_saved": "تم حفظ الفاتورة.", "invoice_details": "تفاصيل الفاتورة",

        # Expenses
        "add_expense": "إضافة مصروف", "edit_expense": "تعديل مصروف",
        "expense_date": "تاريخ المصروف", "expense_category": "الفئة",
        "amount": "المبلغ", "expense_saved": "تم حفظ المصروف.",
        "cat_rent": "إيجار", "cat_salary": "رواتب", "cat_utilities": "فواتير",
        "cat_supplies": "مستلزمات", "cat_maintenance": "صيانة", "cat_other": "أخرى",

        # Reports
        "reports_title": "التقارير والإحصائيات",
        "export_csv": "تصدير CSV",
        "total_revenue": "إجمالي الإيرادات",
        "total_invoices": "عدد الفواتير",
        "unpaid_amount": "مبالغ غير مدفوعة",
        "low_stock_items": "أدوية منخفضة",
        "top_patients": "أكثر المرضى زيارة",
        "monthly_revenue": "إيرادات آخر 30 يومًا",
        "gross_profit": "الربح الإجمالي",
        "net_profit_month": "الربح الصافي (30 يومًا)",
        "total_expenses_month": "مصروفات 30 يومًا",
        "exported": "تم التصدير بنجاح.",
        "from_date": "من تاريخ", "to_date": "إلى تاريخ",
        "filter": "تصفية",

        # Currency
        "currency": "د.ج",

        # Logout
        "logout_confirm": "هل تريد تسجيل الخروج؟",

        # Settings
        "settings_title": "الإعدادات",
        "change_language": "تغيير اللغة",
        "backup_db": "نسخ احتياطي لقاعدة البيانات",
        "backup_done": "تم إنشاء النسخة الاحتياطية.",

        # Protected
        "delete_blocked": "لا يمكن الحذف لوجود سجلات مرتبطة.",

        # ═══════════════════════════════════════════════
        # Charts (لوحة التحكم)
        # ═══════════════════════════════════════════════
        "chart_revenue_expenses": "الإيرادات مقابل المصروفات (7 أيام)",
        "chart_invoice_status": "حالة الفواتير",
        "chart_stock": "حالة المخزون",
        "chart_appointments_week": "مواعيد الأسبوع",
        "revenue": "الإيرادات",
        "expenses_label": "المصروفات",
        "paid_inv": "مدفوعة",
        "partial_inv": "جزئية",
        "unpaid_inv": "غير مدفوعة",
        "ok_stock": "سليم",
        "low_stock_label": "منخفض",
        "expired_label": "منتهي",
        "no_data": "لا توجد بيانات",
    },

    # ═══════════════════════════════════════════════════════════
    #                          English
    # ═══════════════════════════════════════════════════════════
    "en": {
        # App
        "app": "Medical Clinic Management System",
        "clinic_name": "Al-Nour Medical Clinic",
        "dashboard": "Dashboard", "patients": "Patients", "appointments": "Appointments",
        "records": "Medical Records", "billing": "Billing", "inventory": "Inventory",
        "expenses": "Expenses", "reports": "Reports", "settings": "Settings",
        "language": "العربية", "logout": "Logout",

        # Login
        "login_title": "Login", "login_subtitle": "Please enter your credentials to continue",
        "username": "Username", "password": "Password",
        "login": "Login", "exit": "Exit",
        "login_error": "Invalid username or password.",
        "login_empty": "Please enter username and password.",
        "show_password": "Show password", "welcome_back": "Welcome back",

        # Generic
        "id": "ID", "name": "Full Name", "phone": "Phone", "birth": "Date of Birth",
        "address": "Address", "notes": "Notes", "save": "Save", "cancel": "Cancel",
        "delete": "Delete", "edit": "Edit", "add": "Add", "search": "Search",
        "date": "Date", "time": "Time", "status": "Status", "total": "Total",
        "actions": "Actions", "close": "Close", "print": "Print", "export": "Export",
        "confirm_delete": "Are you sure you want to delete?",
        "select_row": "Please select a row first.",
        "saved": "Saved successfully.", "updated": "Updated successfully.",
        "required_name": "Please enter a name.",
        "no_patients": "No registered patients.",

        # Dashboard
        "welcome": "Welcome to the clinic management system",
        "patient_count": "Total Patients", "today_count": "Today's Appointments",
        "income": "Today's Revenue", "stock_alert": "Stock Alerts",
        "expired_items": "Expired Items", "month_revenue": "Month Revenue",
        "net_profit": "Net Profit (Today)", "total_expenses": "Today's Expenses",
        "quick_stats": "Quick Stats",

        # Patients
        "add_patient": "Add Patient", "edit_patient": "Edit Patient",
        "search_patients": "Search by name or phone...",
        "blood_type": "Blood Type", "allergies": "Allergies",
        "chronic_diseases": "Chronic Diseases",

        # Appointments
        "add_appointment": "New Appointment", "patient": "Patient",
        "reason": "Reason", "conflict": "This time slot conflicts with another appointment.",
        "appointment_saved": "Appointment saved.",
        "scheduled": "Scheduled", "completed": "Completed", "cancelled": "Cancelled",

        # Records
        "add_record": "Add Record", "edit_record": "Edit Record",
        "visit_date": "Visit Date", "diagnosis": "Diagnosis",
        "prescription": "Prescription", "blood_pressure": "Blood Pressure",
        "temperature": "Temperature (°C)", "weight": "Weight (kg)",
        "sugar_level": "Sugar Level (mg/dL)", "heart_rate": "Heart Rate",
        "view_record": "View Details", "record_saved": "Medical record saved.",
        "select_patient_first": "Please select a patient first.",
        "patient_history": "Patient Medical History",

        # Inventory
        "add_item": "Add Item", "edit_item": "Edit Item",
        "item_name": "Medication Name", "category": "Category",
        "quantity": "Quantity", "min_quantity": "Min Quantity",
        "purchase_price": "Purchase Price", "sale_price": "Sale Price",
        "expiry_date": "Expiry Date", "supplier": "Supplier",
        "batch_number": "Batch Number",
        "low_stock": "Low Stock", "expired": "Expired",
        "item_saved": "Item saved.",
        "category_med": "Medications", "category_supplies": "Supplies",
        "category_equipment": "Equipment",

        # Billing
        "new_invoice": "New Invoice", "invoice_date": "Invoice Date",
        "subtotal": "Subtotal", "discount": "Discount", "tax": "Tax",
        "paid": "Paid", "remaining": "Remaining",
        "payment_method": "Payment Method", "cash": "Cash", "card": "Card",
        "transfer": "Transfer", "unpaid": "Unpaid", "partial": "Partial",
        "paid_status": "Paid", "add_line": "Add Line", "remove_line": "Remove Line",
        "description": "Description", "unit_price": "Unit Price",
        "line_total": "Line Total", "invoice_saved": "Invoice saved.",
        "invoice_details": "Invoice Details",

        # Expenses
        "add_expense": "Add Expense", "edit_expense": "Edit Expense",
        "expense_date": "Expense Date", "expense_category": "Category",
        "amount": "Amount", "expense_saved": "Expense saved.",
        "cat_rent": "Rent", "cat_salary": "Salaries", "cat_utilities": "Utilities",
        "cat_supplies": "Supplies", "cat_maintenance": "Maintenance", "cat_other": "Other",

        # Reports
        "reports_title": "Reports & Statistics",
        "export_csv": "Export CSV",
        "total_revenue": "Total Revenue", "total_invoices": "Invoice Count",
        "unpaid_amount": "Unpaid Amount", "low_stock_items": "Low Stock",
        "top_patients": "Top Patients", "monthly_revenue": "Last 30 Days Revenue",
        "gross_profit": "Gross Profit", "net_profit_month": "Net Profit (30d)",
        "total_expenses_month": "Expenses (30d)",
        "exported": "Exported successfully.",
        "from_date": "From Date", "to_date": "To Date", "filter": "Filter",

        # Currency
        "currency": "DZD",

        # Logout
        "logout_confirm": "Are you sure you want to logout?",

        # Settings
        "settings_title": "Settings", "change_language": "Change Language",
        "backup_db": "Backup Database", "backup_done": "Backup created successfully.",

        # Protected
        "delete_blocked": "Cannot delete: related records exist.",

        # ═══════════════════════════════════════════════
        # Charts (Dashboard)
        # ═══════════════════════════════════════════════
        "chart_revenue_expenses": "Revenue vs Expenses (7 days)",
        "chart_invoice_status": "Invoice Status",
        "chart_stock": "Stock Status",
        "chart_appointments_week": "Appointments This Week",
        "revenue": "Revenue",
        "expenses_label": "Expenses",
        "paid_inv": "Paid",
        "partial_inv": "Partial",
        "unpaid_inv": "Unpaid",
        "ok_stock": "OK",
        "low_stock_label": "Low",
        "expired_label": "Expired",
        "no_data": "No data",
    },

    # ═══════════════════════════════════════════════════════════
    #                          Français
    # ═══════════════════════════════════════════════════════════
    "fr": {
        # App
        "app": "Système de gestion de clinique médicale",
        "clinic_name": "Clinique Médicale Al-Nour",
        "dashboard": "Tableau de bord", "patients": "Patients", "appointments": "Rendez-vous",
        "records": "Dossiers médicaux", "billing": "Facturation", "inventory": "Stock",
        "expenses": "Dépenses", "reports": "Rapports", "settings": "Paramètres",
        "language": "English", "logout": "Déconnexion",

        # Login
        "login_title": "Connexion", "login_subtitle": "Veuillez saisir vos identifiants",
        "username": "Nom d'utilisateur", "password": "Mot de passe",
        "login": "Se connecter", "exit": "Quitter",
        "login_error": "Nom d'utilisateur ou mot de passe incorrect.",
        "login_empty": "Veuillez saisir le nom d'utilisateur et le mot de passe.",
        "show_password": "Afficher le mot de passe", "welcome_back": "Bienvenue",

        # Generic
        "id": "ID", "name": "Nom complet", "phone": "Téléphone", "birth": "Date de naissance",
        "address": "Adresse", "notes": "Notes", "save": "Enregistrer", "cancel": "Annuler",
        "delete": "Supprimer", "edit": "Modifier", "add": "Ajouter", "search": "Rechercher",
        "date": "Date", "time": "Heure", "status": "Statut", "total": "Total",
        "actions": "Actions", "close": "Fermer", "print": "Imprimer", "export": "Exporter",
        "confirm_delete": "Confirmez-vous la suppression ?",
        "select_row": "Veuillez sélectionner une ligne.",
        "saved": "Enregistré avec succès.", "updated": "Mis à jour avec succès.",
        "required_name": "Veuillez saisir un nom.",
        "no_patients": "Aucun patient enregistré.",

        # Dashboard
        "welcome": "Bienvenue dans le système de gestion de la clinique",
        "patient_count": "Total des patients", "today_count": "RDV du jour",
        "income": "Revenus du jour", "stock_alert": "Alertes stock",
        "expired_items": "Articles expirés", "month_revenue": "Revenus du mois",
        "net_profit": "Bénéfice net (aujourd'hui)", "total_expenses": "Dépenses du jour",
        "quick_stats": "Statistiques rapides",

        # Patients
        "add_patient": "Ajouter un patient", "edit_patient": "Modifier le patient",
        "search_patients": "Rechercher par nom ou téléphone...",
        "blood_type": "Groupe sanguin", "allergies": "Allergies",
        "chronic_diseases": "Maladies chroniques",

        # Appointments
        "add_appointment": "Nouveau rendez-vous", "patient": "Patient",
        "reason": "Motif", "conflict": "Ce créneau chevauche un autre rendez-vous.",
        "appointment_saved": "Rendez-vous enregistré.",
        "scheduled": "Planifié", "completed": "Terminé", "cancelled": "Annulé",

        # Records
        "add_record": "Ajouter un dossier", "edit_record": "Modifier le dossier",
        "visit_date": "Date de visite", "diagnosis": "Diagnostic",
        "prescription": "Ordonnance", "blood_pressure": "Tension artérielle",
        "temperature": "Température (°C)", "weight": "Poids (kg)",
        "sugar_level": "Glycémie (mg/dL)", "heart_rate": "Fréquence cardiaque",
        "view_record": "Voir détails", "record_saved": "Dossier enregistré.",
        "select_patient_first": "Veuillez choisir un patient.",
        "patient_history": "Historique médical du patient",

        # Inventory
        "add_item": "Ajouter un article", "edit_item": "Modifier l'article",
        "item_name": "Nom du médicament", "category": "Catégorie",
        "quantity": "Quantité", "min_quantity": "Seuil minimum",
        "purchase_price": "Prix d'achat", "sale_price": "Prix de vente",
        "expiry_date": "Date d'expiration", "supplier": "Fournisseur",
        "batch_number": "Numéro de lot",
        "low_stock": "Stock faible", "expired": "Expiré",
        "item_saved": "Article enregistré.",
        "category_med": "Médicaments", "category_supplies": "Fournitures",
        "category_equipment": "Équipement",

        # Billing
        "new_invoice": "Nouvelle facture", "invoice_date": "Date de facture",
        "subtotal": "Sous-total", "discount": "Remise", "tax": "Taxe",
        "paid": "Payé", "remaining": "Restant",
        "payment_method": "Mode de paiement", "cash": "Espèces", "card": "Carte",
        "transfer": "Virement", "unpaid": "Impayée", "partial": "Partielle",
        "paid_status": "Payée", "add_line": "Ajouter une ligne", "remove_line": "Retirer la ligne",
        "description": "Description", "unit_price": "Prix unitaire",
        "line_total": "Total ligne", "invoice_saved": "Facture enregistrée.",
        "invoice_details": "Détails de la facture",

        # Expenses
        "add_expense": "Ajouter une dépense", "edit_expense": "Modifier la dépense",
        "expense_date": "Date de dépense", "expense_category": "Catégorie",
        "amount": "Montant", "expense_saved": "Dépense enregistrée.",
        "cat_rent": "Loyer", "cat_salary": "Salaires", "cat_utilities": "Factures",
        "cat_supplies": "Fournitures", "cat_maintenance": "Maintenance", "cat_other": "Autre",

        # Reports
        "reports_title": "Rapports et statistiques",
        "export_csv": "Exporter CSV",
        "total_revenue": "Revenus totaux", "total_invoices": "Nombre de factures",
        "unpaid_amount": "Montants impayés", "low_stock_items": "Stock faible",
        "top_patients": "Patients fréquents", "monthly_revenue": "Revenus 30 derniers jours",
        "gross_profit": "Bénéfice brut", "net_profit_month": "Bénéfice net (30j)",
        "total_expenses_month": "Dépenses (30j)",
        "exported": "Exportation réussie.",
        "from_date": "Du", "to_date": "Au", "filter": "Filtrer",

        # Currency
        "currency": "DA",

        # Logout
        "logout_confirm": "Voulez-vous vous déconnecter ?",

        # Settings
        "settings_title": "Paramètres", "change_language": "Changer la langue",
        "backup_db": "Sauvegarde de la base", "backup_done": "Sauvegarde créée.",

        # Protected
        "delete_blocked": "Suppression impossible : enregistrements liés.",

        # ═══════════════════════════════════════════════
        # Charts (Tableau de bord)
        # ═══════════════════════════════════════════════
        "chart_revenue_expenses": "Revenus vs Dépenses (7 jours)",
        "chart_invoice_status": "Statut des factures",
        "chart_stock": "État du stock",
        "chart_appointments_week": "Rendez-vous de la semaine",
        "revenue": "Revenus",
        "expenses_label": "Dépenses",
        "paid_inv": "Payée",
        "partial_inv": "Partielle",
        "unpaid_inv": "Impayée",
        "ok_stock": "OK",
        "low_stock_label": "Faible",
        "expired_label": "Expiré",
        "no_data": "Aucune donnée",
    },
}


# ═══════════════════════════════════════════════════════════
#                  فئة إدارة الترجمات
# ═══════════════════════════════════════════════════════════
class I18N:
    def __init__(self, lang="ar"):
        self.lang = lang

    def set(self, lang):
        if lang in TRANSLATIONS:
            self.lang = lang

    def t(self, key):
        return TRANSLATIONS.get(self.lang, TRANSLATIONS["ar"]).get(key, key)

    def currency(self):
        return TRANSLATIONS[self.lang].get("currency", "DZD")