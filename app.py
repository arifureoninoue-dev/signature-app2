import base64
import datetime
import os
from io import BytesIO

import requests
from flask import (Flask, Response, redirect, render_template, request,
                   url_for)
from fpdf import FPDF
from PIL import Image

# --- Path Configuration ---
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, template_folder=os.path.join(basedir, 'templates'))

# --- Configuration ---
SECRET_TOKEN = os.environ.get("SECRET_TOKEN", "ajs")
BLOB_READ_WRITE_TOKEN = os.environ.get("BLOB_READ_WRITE_TOKEN")
FONT_FILE = os.path.join(basedir, "NotoSansJP-Regular.ttf")

# --- Data ---
JAPANESE_TEXT = {
    "title": "生活オリエンテーションの確認書",
    "items": [
        "１ 私の日本での生活一般に関する事項",
        "２ 私が出入国管理及び難民認定法第１９条の１６その他の法令の規定により履行しなければならない又は履行すべき国又は地方公共団体の機関に対する届出その他の手続に関する事項",
        "３ 私が把握しておくべき、特定技能所属機関又は当該特定技能所属機関から契約により私の支援の実施の委託を受けた者において相談又は苦情の申出に対応することとされている者の連絡先及びこれらの相談又は苦情の申出をすべき国又は地方公共団体の機関の連絡先",
        "４ 私が十分に理解することができる言語により医療を受けることができる医療機関に関する事項",
        "５ 防災及び防犯に関する事項並びに急病その他の緊急時における対応に必要な事項",
        "６ 出入国又は労働に関する法令の規定に違反していることを知ったときの対応方法その他私の法的保護に必要な事項"
    ]
}
TRANSLATIONS = {
    "en": {
        "title": "Confirmation of Living Orientation",
        "items": [
            "1. Matters concerning my general life in Japan.",
            "2. Matters concerning notifications and other procedures to national and local government organizations that I must or should perform under the provisions of the Immigration Control and Refugee Recognition Act and other laws and regulations.",
            "3. Contact information for persons designated by the organization of affiliation for specified skilled workers or a person entrusted by said organization to handle consultations or complaints, and contact information for national or local government organizations where such consultations or complaints should be made.",
            "4. Matters concerning medical institutions where I can receive medical care in a language I can fully understand.",
            "5. Matters concerning disaster prevention and crime prevention, as well as necessary responses in case of sudden illness or other emergencies.",
            "6. How to respond upon learning of a violation of the provisions of laws and regulations concerning immigration or labor, and other matters necessary for my legal protection."
        ],
        "signature_label": "Signature of the Specified Skilled Worker",
        "agree_checkbox": "I confirm and agree to all the contents above.",
        "submit_button": "Submit Signature and Proceed"
    },
    "id": {
        "title": "Konfirmasi Orientasi Kehidupan",
        "items": [
            "1. Hal-hal mengenai kehidupan umum saya di Jepang.",
            "2. Hal-hal mengenai pemberitahuan dan prosedur lain kepada organisasi pemerintah pusat dan daerah yang harus atau sebaiknya saya lakukan berdasarkan ketentuan Undang-Undang Kontrol Imigrasi dan Pengakuan Pengungsi serta hukum dan peraturan lainnya.",
            "3. Informasi kontak orang yang ditunjuk oleh organisasi afiliasi untuk pekerja terampil spesifik atau orang yang dipercaya oleh organisasi tersebut untuk menangani konsultasi atau keluhan, dan informasi kontak organisasi pemerintah pusat atau daerah tempat konsultasi atau keluhan tersebut harus diajukan.",
            "4. Hal-hal mengenai institusi medis di mana saya dapat menerima perawatan medis dalam bahasa yang dapat saya pahami sepenuhnya.",
            "5. Hal-hal mengenai pencegahan bencana dan kejahatan, serta respons yang diperlukan dalam keadaan darurat seperti sakit mendadak.",
            "6. Cara merespons setelah mengetahui adanya pelanggaran terhadap ketentuan hukum dan peraturan mengenai imigrasi atau ketenagakerjaan, dan hal-hal lain yang diperlukan untuk perlindungan hukum saya."
        ],
        "signature_label": "Tanda Tangan Pekerja Berketerampilan Spesifik",
        "agree_checkbox": "Saya mengonfirmasi dan menyetujui semua isi di atas.",
        "submit_button": "Kirim Tanda Tangan dan Lanjutkan"
    },
    "my": {
        "title": "နေထိုင်မှုဆိုင်ရာ အခြေခံသင်တန်း အတည်ပြုလွှာ",
        "items": [
            "၁။ ဂျပန်နိုင်ငံတွင် ကျွန်ုပ်၏ ယေဘုယျဘဝနေထိုင်မှုနှင့် သက်ဆိုင်သော အချက်များ။",
            "၂။ လူဝင်မှုကြီးကြပ်ရေးနှင့် ဒုက္ခသည်များဆိုင်ရာ အသိအမှတ်ပြုခြင်း အက်ဥပဒေနှင့် အခြားဥပဒေများပါ ပြဋ္ဌာန်းချက်များအရ ကျွန်ုပ်လိုက်နာဆောင်ရွက်ရမည့် သို့မဟုတ် ဆောင်ရွက်သင့်သည့် နိုင်ငံတော် သို့မဟုတ် ဒေသဆိုင်ရာ အစိုးရအဖွဲ့အစည်းများသို့ အကြောင်းကြားချက်များနှင့် အခြားလုပ်ထုံးလုပ်နည်းများဆိုင်ရာ အချက်များ။",
            "၃။ သတ်မှတ်ထားသော ကျွမ်းကျင်လုပ်သားများအတွက် လက်ခံအဖွဲ့အစည်း သို့မဟုတ် အဆိုပါအဖွဲ့အစည်းမှ တိုင်ပင်ဆွေးနွေးမှုများ သို့မဟုတ် တိုင်ကြားချက်များကို ကိုင်တွယ်ရန် တာဝန်ပေးအပ်ထားသူ၏ ဆက်သွယ်ရန် အချက်အလက်နှင့် အဆိုပါတိုင်ပင်ဆွေးနွေးမှုများ သို့မဟုတ် တိုင်ကြားချက်များကို တင်ပြသင့်သည့် နိုင်ငံတော် သို့မဟုတ် ဒေသဆိုင်ရာ အစိုးရအဖွဲ့အစည်းများ၏ ဆက်သွယ်ရန် အချက်အလက်များ။",
            "၄။ ကျွန်ုပ်အပြည့်အဝနားလည်နိုင်သော ဘာသာစကားဖြင့် ဆေးကုသမှုခံယူနိုင်သည့် ဆေးဘက်ဆိုင်ရာ အဖွဲ့အစည်းများဆိုင်ရာ အချက်များ။",
            "၅။ ဘေးအန္တရာယ်ကာကွယ်ရေးနှင့် ရာဇဝတ်မှုကာကွယ်ရေးဆိုင်ရာ အချက်များအပြင် ရုတ်တရက်ဖျားနာမှု သို့မဟုတ် အခြားအရေးပေါ်အခြေအနေများတွင် လိုအပ်သော တုံ့ပြန်ဆောင်ရွက်မှုများဆိုင်ရာ အချက်များ။",
            "၆။ လူဝင်မှုကြီးကြပ်ရေး သို့မဟုတ် အလုပ်သမားရေးရာ ဥပဒေပြဋ္ဌာန်းချက်များကို ချိုးဖောက်ကြောင်း သိရှိလာသည့်အခါ တုံ့ပြန်ဆောင်ရွက်ရမည့် နည်းလမ်းနှင့် ကျွန်ုပ်၏ တရားဝင်အကာအကွယ်အတွက် လိုအပ်သောအခြားအချက်များ။"
        ],
        "signature_label": "သတ်မှတ်ထားသော ကျွမ်းကျင်လုပ်သား၏ လက်မှတ်",
        "agree_checkbox": "အထက်ပါ အကြောင်းအရာအားလုံးကို ကျွန်ုပ် အတည်ပြုပြီး သဘောတူပါသည်။",
        "submit_button": "လက်မှတ်ထိုးပြီး ဆက်လက်ဆောင်ရွက်ပါ"
    },
    "vi": {
        "title": "Giấy xác nhận về Buổi hướng dẫn Sinh hoạt",
        "items": [
            "1. Các vấn đề liên quan đến đời sống chung của tôi tại Nhật Bản.",
            "2. Các vấn đề liên quan đến thông báo và các thủ tục khác cho các cơ quan chính phủ quốc gia và địa phương mà tôi phải hoặc nên thực hiện theo quy định của Luật Kiểm soát Xuất nhập cảnh và Công nhận Người tị nạn và các luật lệ khác.",
            "3. Thông tin liên lạc của người được chỉ định bởi tổ chức tiếp nhận lao động kỹ năng đặc định hoặc người được tổ chức đó ủy thác để xử lý các cuộc tư vấn hoặc khiếu nại, và thông tin liên lạc của các cơ quan chính phủ quốc gia hoặc địa phương nơi nên đưa ra các cuộc tư vấn hoặc khiếu nại đó.",
            "4. Các vấn đề liên quan đến các cơ sở y tế nơi tôi có thể nhận được sự chăm sóc y tế bằng ngôn ngữ mà tôi có thể hiểu đầy đủ.",
            "5. Các vấn đề liên quan đến phòng chống thiên tai và phòng chống tội phạm, cũng như các biện pháp ứng phó cần thiết trong trường hợp khẩn cấp như bệnh đột ngột.",
            "6. Cách ứng phó khi biết về hành vi vi phạm các quy định của pháp luật về xuất nhập cảnh hoặc lao động, và các vấn đề khác cần thiết cho sự bảo vệ pháp lý của tôi."
        ],
        "signature_label": "Chữ ký của Người lao động Kỹ năng Đặc định",
        "agree_checkbox": "Tôi xác nhận và đồng ý với tất cả các nội dung trên.",
        "submit_button": "Gửi chữ ký và Tiếp tục"
    },
    "th": {
        "title": "เอกสารยืนยันการปฐมนิเทศการใช้ชีวิต",
        "items": [
            "1. เรื่องที่เกี่ยวกับชีวิตทั่วไปของฉันในประเทศญี่ปุ่น",
            "2. เรื่องที่เกี่ยวกับการแจ้งเตือนและขั้นตอนอื่น ๆ ต่อหน่วยงานของรัฐบาลกลางและท้องถิ่นที่ฉันต้องหรือควรปฏิบัติภายใต้บทบัญญัติของพระราชบัญญัติควบคุมคนเข้าเมืองและผู้ลี้ภัยและกฎหมายและข้อบังคับอื่น ๆ",
            "3. ข้อมูลติดต่อของบุคคลที่ได้รับมอบหมายจากองค์กรต้นสังกัดสำหรับแรงงานทักษะเฉพาะหรือบุคคลที่ได้รับความไว้วางใจจากองค์กรดังกล่าวในการจัดการกับการให้คำปรึกษาหรือข้อร้องเรียน และข้อมูลติดต่อของหน่วยงานของรัฐบาลกลางหรือท้องถิ่นที่ควรยื่นคำปรึกษาหรือข้อร้องเรียนดังกล่าว",
            "4. เรื่องที่เกี่ยวกับสถาบันทางการแพทย์ที่ฉันสามารถรับการรักษาพยาบาลในภาษาที่ฉันสามารถเข้าใจได้อย่างถ่องแท้",
            "5. เรื่องที่เกี่ยวกับการป้องกันภัยพิบัติและการป้องกันอาชญากรรม ตลอดจนการตอบสนองที่จำเป็นในกรณีฉุกเฉิน เช่น การเจ็บป่วยกะทันหัน",
            "6. วิธีตอบสนองเมื่อทราบถึงการละเมิดบทบัญญัติของกฎหมายและข้อบังคับเกี่ยวกับการเข้าเมืองหรือแรงงาน และเรื่องอื่น ๆ ที่จำเป็นสำหรับการคุ้มครองทางกฎหมายของฉัน"
        ],
        "signature_label": "ลายมือชื่อของแรงงานทักษะเฉพาะ",
        "agree_checkbox": "ข้าพเจ้ายืนยันและยอมรับเนื้อหาทั้งหมดข้างต้น",
        "submit_button": "ส่งลายมือชื่อและดำเนินการต่อ"
    }
}
EXPLAINERS = {
    "vi": ["PHAM VAN THINH", "HOANG ANH NAM"],
    "id": ["PETRI SURYANI", "IMELDA SARIHUTAJULU", "FEBRI SAHRULLAH AHDIN", "MARISYA UTARI", "MOHAMMAD FARID HIDAYATULLAH", "VANESSA KOBAYASHI", "ANDI PRANATA"],
    "my": ["PYO EAINDRAY MIN", "PHYOWAI ZAW"],
    "jp": ["西野 宏", "土屋 雛子"],
    "en": ["土屋 雛子"]
}

# --- Routes (変更なし) ---
@app.route('/')
def language_select():
    provided_token = request.args.get('token')
    if provided_token != SECRET_TOKEN:
        return "アクセス権がありません。", 403
    return render_template('language_select.html', token=provided_token)

@app.route('/guidance', methods=['POST'])
def guidance_page():
    provided_token = request.form.get('token')
    lang = request.form.get('lang')
    if provided_token != SECRET_TOKEN:
        return "アクセス権がありません。", 403
    if not lang or lang not in TRANSLATIONS:
        return "言語が選択されていません。", 400
    return render_template(
        'index.html',
        token=provided_token,
        lang=lang,
        translations=TRANSLATIONS[lang],
        japanese_text=JAPANESE_TEXT
    )

@app.route('/sign', methods=['POST'])
def sign():
    provided_token = request.form.get('token')
    lang = request.form.get('lang')
    if provided_token != SECRET_TOKEN:
        return "不正なアクセスです。", 403
    signature_data_url = request.form.get('signature_data')
    if not signature_data_url:
        return redirect(url_for('language_select', token=provided_token))
    timestamp = datetime.datetime.now()
    filename = f"signature_living_orientation_{timestamp.strftime('%Y%m%d_%H%M%S')}.png"
    try:
        header, encoded = signature_data_url.split(",", 1)
        image_data = base64.b64decode(encoded)
        headers = {
            'Authorization': f'Bearer {BLOB_READ_WRITE_TOKEN}',
            'Content-Type': 'image/png'
        }
        upload_url = f"https://blob.vercel-storage.com/{filename}"
        response = requests.put(upload_url, data=image_data, headers=headers)
        response.raise_for_status()
        public_url = response.json().get('url')
        if not public_url:
            raise Exception("Blob upload response did not contain a URL.")
    except Exception as e:
        print(f"Error uploading signature to Blob: {e}")
        return "署名画像のアップロードに失敗しました。", 500
    return redirect(url_for('download_page', signature_url=public_url, lang=lang))

@app.route('/download')
def download_page():
    signature_url = request.args.get('signature_url')
    lang = request.args.get('lang')
    if not signature_url or not lang:
        return "必要な情報が不足しています。", 400
    available_explainers = EXPLAINERS.get(lang, []) + EXPLAINERS.get('jp', [])
    unique_explainers = list(set(available_explainers))
    return render_template(
        'download.html',
        signature_url=signature_url,
        explainers=unique_explainers
    )

# --- PDF生成関数 (最終レイアウト調整版) ---
@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    signature_url = request.form.get('signature_url')
    explainer_name = request.form.get('explainer_name')
    if not signature_url or not explainer_name:
        return "必要な情報が不足しています。", 400

    try:
        response = requests.get(signature_url)
        response.raise_for_status()
        signature_image_data = response.content
        signature_image = Image.open(BytesIO(signature_image_data))
        temp_signature_path = f"/tmp/{os.path.basename(signature_url)}"
        signature_image.save(temp_signature_path)
    except Exception as e:
        print(f"Error downloading signature from Blob: {e}")
        return "署名画像の取得に失敗しました。", 404

    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('NotoSansJP', '', FONT_FILE)

    # --- PDFレイアウト ---
    pdf.set_font('NotoSansJP', '', 10)
    pdf.set_xy(pdf.l_margin, 10)
    pdf.cell(0, 10, '参考様式第５－８号', align='L')

    pdf.set_xy(0, 25)
    pdf.set_font('NotoSansJP', '', 16)
    pdf.cell(0, 10, '生 活 オ リ エ ン テ ー シ ョ ン の 確 認 書', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(10)

    pdf.set_font('NotoSansJP', '', 10.5)
    list_items = [
        ("１", JAPANESE_TEXT["items"][0][2:]),
        ("２", JAPANESE_TEXT["items"][1][2:]),
        ("３", JAPANESE_TEXT["items"][2][2:]),
        ("４", JAPANESE_TEXT["items"][3][2:]),
        ("５", JAPANESE_TEXT["items"][4][2:]),
        ("６", JAPANESE_TEXT["items"][5][2:])
    ]
    initial_x = pdf.get_x()
    for number, text in list_items:
        pdf.set_x(initial_x)
        pdf.cell(8, 5, number, align='L')
        pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin - 8, 5, text, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    pdf.set_font_size(11)
    pdf.ln(5)
    pdf.multi_cell(0, 8, 'について、')
    pdf.ln(1)
    
    today = datetime.date.today()
    date_time_str = f"{today.year}年{today.month}月{today.day}日　13時00分から17時00分まで"
    text_width = pdf.get_string_width(date_time_str)
    start_x = (pdf.w - text_width) / 2
    pdf.cell(0, 8, date_time_str, new_x="LMARGIN", new_y="NEXT", align='C')
    y_pos = pdf.get_y()
    pdf.line(start_x, y_pos - 1, start_x + text_width, y_pos - 1)
    pdf.ln(6)

    underline_length = 80
    line_start_x_right = pdf.w - pdf.r_margin - underline_length

    # 特定技能所属機関 (中央配置に修正)
    pdf.cell(0, 8, '特定技能所属機関（又は登録支援機関）の氏名又は名称', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(1)
    text_to_underline = 'アジア人材サポート協同組合'
    text_width = pdf.get_string_width(text_to_underline)
    text_start_x = line_start_x_right + (underline_length - text_width) / 2
    pdf.set_x(text_start_x)
    pdf.cell(text_width, 8, text_to_underline, new_x="LMARGIN", new_y="NEXT")
    y_pos = pdf.get_y()
    pdf.line(line_start_x_right, y_pos - 1, pdf.w - pdf.r_margin, y_pos - 1)
    pdf.ln(6)

    # 説明者の氏名 (中央配置に修正)
    pdf.cell(0, 8, '説明者の氏名', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(1)
    text_width = pdf.get_string_width(explainer_name)
    text_start_x = line_start_x_right + (underline_length - text_width) / 2
    pdf.set_x(text_start_x)
    pdf.cell(text_width, 8, explainer_name, new_x="LMARGIN", new_y="NEXT")
    y_pos = pdf.get_y()
    pdf.line(line_start_x_right, y_pos - 1, pdf.w - pdf.r_margin, y_pos - 1)
    pdf.ln(6)

    pdf.multi_cell(0, 8, 'から説明を受け、内容を十分に理解しました。')
    
    # 署名欄 (位置を微調整)
    date_str = f"{today.year}年{today.month}月{today.day}日"
    sig_y_pos = pdf.h - 45 # Y座標を少し上げる
    pdf.set_y(sig_y_pos)
    pdf.cell(0, 8, date_str, align='R')
    pdf.ln(5)
    pdf.set_x(pdf.l_margin)
    pdf.cell(45, 8, '特定技能外国人の署名')
    line_start_x = pdf.get_x()
    line_end_x = line_start_x + 65
    pdf.line(line_start_x, sig_y_pos + 12, line_end_x, sig_y_pos + 12)
    pdf.image(temp_signature_path, x=line_start_x + 5, y=sig_y_pos - 8, w=55, h=20) # Y座標を調整

    pdf_output = bytes(pdf.output())

    try:
        pdf_filename = os.path.splitext(os.path.basename(signature_url))[0] + '.pdf'
        headers = {
            'Authorization': f'Bearer {BLOB_READ_WRITE_TOKEN}',
            'Content-Type': 'application/pdf'
        }
        upload_url = f"https://blob.vercel-storage.com/{pdf_filename}"
        response = requests.put(upload_url, data=pdf_output, headers=headers)
        response.raise_for_status()
        print(f"Successfully uploaded PDF to Blob: {pdf_filename}")
    except Exception as e:
        print(f"Error uploading completed PDF to Blob: {e}")

    os.remove(temp_signature_path)

    return Response(
        pdf_output,
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment;filename=living_orientation_signed.pdf"}

    )
