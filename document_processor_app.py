import streamlit as st
import pandas as pd
import io
import pdfplumber
import re
from datetime import datetime

st.set_page_config(page_title="Document Processor", page_icon="📄", layout="wide")

st.sidebar.title("📄 MENU")
client = st.sidebar.selectbox("Select Client", ["Customer A", "Customer B", "Customer C", "Customer D"], key="client_select")

ref_manual = ""
des_manual = ""

if client == "Customer B":
    st.sidebar.write("---")
    st.sidebar.subheader("📝 Customer B Fixed Data")
    ref_manual = st.sidebar.text_input("Reference (PHC)", placeholder="e.g., FW24-001")
    des_manual = st.sidebar.text_input("Designation (PHC)", placeholder="e.g., Product Name")
    st.sidebar.caption("These values will be applied to all rows in the file.")

if client == "Customer A":
    st.sidebar.write("---")
    st.sidebar.subheader("📝 Customer A — PHC References")
    if st.session_state.get("customer_models"):
        for model in st.session_state["customer_models"]:
            st.sidebar.caption(model)
            st.sidebar.text_input("Reference (PHC)", key=f"ref_{model}", placeholder="e.g., AW24-001")
            st.sidebar.text_input("Designation (PHC)", key=f"des_{model}", placeholder="e.g., Product Tee")
    else:
        st.sidebar.caption("Upload a file and click Analyse File.")

tab1, tab2, tab3 = st.tabs(["📦 Converter", "💰 Financial Control", "ℹ️ Help"])

SKIP_LINES = ["TOTAL QTY", "FIRST/MAKE", "SUB-TOTAL", "TOTAL COST", "QTY COST TOTAL"]
COLOR_JUNK = {
    "JERSEY", "MICRO", "RIB", "SHORT", "SLEEVE", "NECK", "VEST", "HENLEY",
    "COTTON", "BRANDED", "BOXY", "FIT", "T-SHIRT", "QTY", "COST", "TOTAL",
    "FIRST", "MAKE", "-", "–", "SORIN", "VOTAN", "LAY", "SCOOP",
    "PRODUCTION", "MADE", "LOCATION", "UNITED", "KINGDOM", "KOREA", "SOUTH",
    "PRINTED", "REG", "OFFICE", "VAT", "PAGE"
}
MODEL_RE = re.compile(r"(SNW|SNM|SN)\s*[-–]\s*\d+", re.IGNORECASE)

def extract_code(text: str) -> str:
    m = re.search(r"(S[NW]W?\s*[-–]\s*\d+|SN\s*[-–]\s*\d+)", text, re.IGNORECASE)
    return re.sub(r"\s*[-–]\s*", "-", m.group(1)).upper() if m else ""

def parse_quantities_pdf(pdf_file) -> list:
    rows = []
    current_dest  = "See PDF"
    current_code  = ""
    current_model = ""
    current_sizes = []
    log = []

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text  = page.extract_text() or ""
            lines = text.split("\n")

            for idx, line in enumerate(lines):
                l_up = line.upper().strip()
                if not l_up:
                    continue

                if l_up.startswith("SHIP TO"):
                    dest_raw = re.sub(r"^SHIP\s+TO\s*", "", line, flags=re.I)
                    dest_raw = re.sub(r"Ship\s+To:.*$", "", dest_raw, flags=re.I).strip()
                    if " - " in dest_raw:
                        dest_raw = dest_raw.split(" - ")[-1].strip()
                    if len(dest_raw) < 3 and idx + 1 < len(lines):
                        dest_raw = lines[idx + 1].strip()
                    if dest_raw:
                        current_dest = dest_raw
                    log.append(f"DEST → {current_dest}")
                    continue

                if MODEL_RE.search(line):
                    current_code  = extract_code(line)
                    current_model = re.split(r"\s+Qty\b", line, flags=re.I)[0].strip()
                    current_sizes = []
                    log.append(f"MODEL → {current_code} | {current_model}")
                    continue

                if re.search(r"UK\s*\d+", line, re.IGNORECASE) and re.search(r"IT\s*\d+", line, re.IGNORECASE):
                    raw = re.sub(r"\s+", "", line.upper())
                    current_sizes = re.findall(r"UK\d+/IT\d+", raw)
                    log.append(f"SIZES → {current_sizes}")
                    continue

                if any(skip in l_up for skip in SKIP_LINES):
                    continue

                if not current_code or not current_sizes:
                    continue

                PRODUCT_WORDS = {"JERSEY", "KNIT", "WOVEN", "DENIM", "FLEECE", "TWILL"}
                first_word = l_up.split()[0] if l_up.split() else ""
                if first_word not in PRODUCT_WORDS:
                    continue

                before_euro = line.split("€")[0] if "€" in line else line
                normalized  = re.sub(r"(?<!\w)[-–](?!\w)", " ", before_euro)
                nums = re.findall(r"\b(\d+)\b", normalized)
                qty_values = [int(n) for n in nums][:-1] if len(nums) > 1 else [int(n) for n in nums]

                before_nums = re.split(r"\s+\d", normalized)[0]
                color_tokens = [
                    t for t in before_nums.split()
                    if t.upper().strip("–-") not in COLOR_JUNK
                    and not re.match(r"^[\d.,/]+$", t)
                    and len(t) > 1
                ]
                color = " ".join(color_tokens[-2:]).upper() if color_tokens else ""

                if not color or not qty_values:
                    continue

                offset = len(current_sizes) - len(qty_values)
                for i, size in enumerate(current_sizes):
                    i2 = i - offset
                    if i2 >= 0 and qty_values[i2] > 0:
                        rows.append({
                            "code":        current_code,
                            "model":       current_model,
                            "color":       color,
                            "size":        size,
                            "qty":         qty_values[i2],
                            "destination": current_dest,
                        })

        with st.expander("🐛 Debug", expanded=False):
            for entry in log:
                st.text(entry)

    return rows

cols = [
    "Referência", "Designação", "Quant.", "Pr.Unit.",
    "Pr.Unit.Moeda", "Tabela de IVA", "Cor", "Tamanho",
    "TOTAL", "Destino", "Nº CPO", "Nº SPO",
    "Valor Unit. Fornecedor", "Total Fornecedor",
    "Data Envio Cliente", "Data Envio Fornecedor", "Notas",
]

def make_row(ref="", des="", qty=0, price=0.0, vat=4, color="", size="",
             dest="", cpo="", spo="", supp_val="", supp_total="",
             client_date="", supp_date="", currency=0, notas=""):
    total = qty * price
    return {
        "Referência":             ref,
        "Designação":             des,
        "Quant.":                 qty,
        "Pr.Unit.":               price,
        "Pr.Unit.Moeda":         currency,
        "Tabela de IVA":          vat,
        "Cor":                    color,
        "Tamanho":                size,
        "TOTAL":                  total,
        "Destino":                dest,
        "Nº CPO":                 cpo,
        "Nº SPO":                 spo,
        "Valor Unit. Fornecedor": supp_val,
        "Total Fornecedor":       supp_total,
        "Data Envio Cliente":     client_date,
        "Data Envio Fornecedor":  supp_date,
        "Notas":                  notas,
    }

def make_excel(df_final, group_col):
    if df_final.empty:
        raise ValueError("No valid data to generate Excel. Please check the file.")
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        for val in df_final[group_col].unique():
            safe = re.sub(r"[\[\]*:?/\\]", "", str(val))[:31]
            output_cols = [c for c in cols if c in df_final.columns]
            df_final[df_final[group_col] == val][output_cols].to_excel(
                writer, index=False, sheet_name=safe if safe else "Sheet1"
            )
    return out.getvalue()

with tab1:
    st.title(f"📦 Converter: {client}")

    if client == "Customer A":
        uploaded_file = st.file_uploader("Upload file", type=["xlsx"])

        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                
                if "Model" in df.columns:
                    models = df["Model"].unique().tolist()
                    st.session_state["customer_models"] = models
                    st.success(f"✅ Detected {len(models)} models")
                    
                    st.subheader("📋 Data Preview")
                    st.dataframe(df.head(10))
                else:
                    st.warning("⚠️ 'Model' column not found")
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")

    elif client == "Customer B":
        st.info("Upload your PDF document for conversion")
        uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

        if uploaded_file:
            try:
                rows = parse_quantities_pdf(uploaded_file)
                
                if rows:
                    data_list = []
                    for row in rows:
                        data_list.append(make_row(
                            ref   = ref_manual or row.get("code", ""),
                            des   = des_manual or row.get("model", ""),
                            qty   = row.get("qty", 0),
                            color = row.get("color", ""),
                            size  = row.get("size", ""),
                            dest  = row.get("destination", ""),
                        ))
                    
                    df_final = pd.DataFrame(data_list)
                    st.dataframe(df_final)
                    
                    excel_data = make_excel(df_final, "Destino")
                    st.download_button(
                        "⬇️ Download Excel",
                        excel_data,
                        "IMPORT_CustomerB.xlsx",
                        key="dl_customer_b"
                    )
                else:
                    st.warning("⚠️ No data extracted from PDF")
            except Exception as e:
                st.error(f"❌ Error: {e}")

    elif client == "Customer C":
        st.info("Fill in the table below and click Download to generate the Excel file.")

        empty_row = {
            "Referência":    "",
            "Designação":    "",
            "Quant.":        0,
            "Pr.Unit.":      0.0,
            "Tabela de IVA": 23,
            "Cor":           "",
            "Tamanho":       "",
            "Delivery Date": "",
            "Nº SPO":        "",
            "Supplier":      "",
        }

        if "customer_c_df" not in st.session_state:
            st.session_state["customer_c_df"] = pd.DataFrame([empty_row] * 5)

        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("➕ Add Row"):
                st.session_state["customer_c_df"] = pd.concat(
                    [st.session_state["customer_c_df"], pd.DataFrame([empty_row])],
                    ignore_index=True
                )
            if st.button("🗑️ Clear All"):
                st.session_state["customer_c_df"] = pd.DataFrame([empty_row] * 5)

        edited_df = st.data_editor(
            st.session_state["customer_c_df"],
            use_container_width=True,
            num_rows="dynamic",
        )
        st.session_state["customer_c_df"] = edited_df

        valid = edited_df[pd.to_numeric(edited_df["Quant."], errors="coerce").fillna(0) > 0].copy()

        if not valid.empty:
            data_list = []
            for _, row in valid.iterrows():
                qty   = pd.to_numeric(row["Quant."], errors="coerce") or 0
                price = pd.to_numeric(row["Pr.Unit."], errors="coerce") or 0
                data_list.append(make_row(
                    ref        = row["Referência"],
                    des        = row["Designação"],
                    qty        = qty,
                    price      = price,
                    vat        = row["Tabela de IVA"],
                    color      = row["Cor"],
                    size       = row["Tamanho"],
                    dest       = row["Supplier"],
                    spo        = row["Nº SPO"],
                    client_date= row["Delivery Date"],
                ))

            df_final = pd.DataFrame(data_list)
            out = io.BytesIO()
            with pd.ExcelWriter(out, engine="openpyxl") as writer:
                df_final[cols].to_excel(writer, index=False, sheet_name="CustomerC")

            st.download_button(
                f"⬇️ Download PHC Excel ({len(data_list)} rows)",
                out.getvalue(),
                "IMPORT_CustomerC.xlsx",
                key="dl_customer_c"
            )

    elif client == "Customer D":
        st.info("Fill in the table below and click Download to generate the Excel file.")

        empty_row = {
            "Referência":    "",
            "Designação":    "",
            "Quant.":        0,
            "Pr.Unit.":      0.0,
            "Tabela de IVA": 23,
            "Cor":           "",
            "Tamanho":       "",
            "Delivery Date": "",
            "Nº SPO":        "",
            "Supplier":      "",
        }

        if "customer_d_df" not in st.session_state:
            st.session_state["customer_d_df"] = pd.DataFrame([empty_row] * 5)

        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("➕ Add Row", key="add_customer_d"):
                st.session_state["customer_d_df"] = pd.concat(
                    [st.session_state["customer_d_df"], pd.DataFrame([empty_row])],
                    ignore_index=True
                )
            if st.button("🗑️ Clear All", key="clear_customer_d"):
                st.session_state["customer_d_df"] = pd.DataFrame([empty_row] * 5)

        edited_df = st.data_editor(
            st.session_state["customer_d_df"],
            use_container_width=True,
            num_rows="dynamic",
        )
        st.session_state["customer_d_df"] = edited_df

        valid = edited_df[pd.to_numeric(edited_df["Quant."], errors="coerce").fillna(0) > 0].copy()

        if not valid.empty:
            data_list = []
            for _, row in valid.iterrows():
                qty   = pd.to_numeric(row["Quant."], errors="coerce") or 0
                price = pd.to_numeric(row["Pr.Unit."], errors="coerce") or 0
                data_list.append(make_row(
                    ref        = row["Referência"],
                    des        = row["Designação"],
                    qty        = qty,
                    price      = price,
                    vat        = row["Tabela de IVA"],
                    color      = row["Cor"],
                    size       = row["Tamanho"],
                    dest       = row["Supplier"],
                    spo        = row["Nº SPO"],
                    client_date= row["Delivery Date"],
                ))

            df_final = pd.DataFrame(data_list)
            out = io.BytesIO()
            with pd.ExcelWriter(out, engine="openpyxl") as writer:
                df_final[cols].to_excel(writer, index=False, sheet_name="CustomerD")

            st.download_button(
                f"⬇️ Download PHC Excel ({len(data_list)} rows)",
                out.getvalue(),
                "IMPORT_CustomerD.xlsx",
                key="dl_customer_d"
            )

with tab2:
    st.title("💰 Financial Control - Resumo CPO/SPO")

    st.info("📤 Carregue o seu Excel. As colunas serão agrupadas por CPO/SPO com totais de quantidades.")

    uploaded_file = st.file_uploader("Upload seu Excel financeiro", type=["xlsx"], key="financial_upload")

    if uploaded_file:
        try:
            excel_file = pd.ExcelFile(uploaded_file, engine="openpyxl")
            
            if len(excel_file.sheet_names) > 1:
                all_sheets = {sheet: pd.read_excel(uploaded_file, sheet_name=sheet) for sheet in excel_file.sheet_names}
                df_combined = pd.concat([df.assign(Source_Sheet=sheet) for sheet, df in all_sheets.items()], ignore_index=True)
            else:
                df_combined = pd.read_excel(uploaded_file, sheet_name=0)
            
            st.subheader("📋 Colunas Detectadas")
            st.write(df_combined.columns.tolist())
            
            cols_disponíveis = df_combined.columns.tolist()
            
            col_cpo = None
            col_spo = None
            col_qty = None
            
            for col in cols_disponíveis:
                col_lower = col.lower()
                if 'cpo' in col_lower and col_cpo is None:
                    col_cpo = col
                if 'spo' in col_lower and col_spo is None:
                    col_spo = col
                if ('qty' in col_lower or 'quant' in col_lower) and col_qty is None:
                    col_qty = col
            
            if not col_cpo or not col_spo:
                st.error("❌ Colunas CPO ou SPO não encontradas!")
                st.write(f"Colunas disponíveis: {cols_disponíveis}")
            else:
                st.success(f"✅ CPO: {col_cpo}, SPO: {col_spo}, QTY: {col_qty}")
                
                if st.button("🔄 Processar Dados", type="primary"):
                    try:
                        df_proc = df_combined.copy()
                        
                        # Converter colunas numéricas
                        if col_qty and col_qty in df_proc.columns:
                            df_proc[col_qty] = pd.to_numeric(df_proc[col_qty], errors='coerce').fillna(0)
                        
                        # Identificar colunas numéricas e de texto
                        numeric_cols = df_proc.select_dtypes(include=['number']).columns.tolist()
                        text_cols = [c for c in df_proc.columns if c not in numeric_cols and c != col_cpo and c != col_spo]
                        
                        # Preparar agg_dict
                        agg_dict = {}
                        
                        # Somar colunas numéricas
                        for col in numeric_cols:
                            if col != col_cpo and col != col_spo:
                                agg_dict[col] = 'sum'
                        
                        # Primeiro valor para colunas texto
                        for col in text_cols:
                            agg_dict[col] = 'first'
                        
                        # Agrupar por CPO e SPO
                        summary = df_proc.groupby([col_cpo, col_spo], as_index=False).agg(agg_dict)
                        
                        # Reordenar colunas
                        cols_ordem = [col_cpo, col_spo] + [c for c in cols_disponíveis if c not in [col_cpo, col_spo]]
                        cols_ordem = [c for c in cols_ordem if c in summary.columns]
                        summary = summary[cols_ordem]
                        
                        st.subheader(f"📋 Resumo CPO/SPO ({len(summary)} combinações)")
                        st.dataframe(summary, use_container_width=True, hide_index=True)
                        
                        st.subheader("📊 Estatísticas")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total CPOs", summary[col_cpo].nunique())
                        with col2:
                            st.metric("Total SPOs", summary[col_spo].nunique())
                        with col3:
                            if col_qty and col_qty in summary.columns:
                                total_qty = summary[col_qty].sum()
                                st.metric("Total QTY", f"{total_qty:,.0f}")
                        
                        st.subheader("⬇️ Descarregar")
                        
                        out = io.BytesIO()
                        with pd.ExcelWriter(out, engine="openpyxl") as writer:
                            summary.to_excel(writer, index=False, sheet_name="Sheet1", startrow=0)
                        
                        filename = f"Financial_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                        st.download_button("📥 Download Relatório", out.getvalue(), filename, type="primary")
                        st.success("✅ Pronto!")
                        
                    except Exception as e:
                        st.error(f"❌ Erro: {e}")
                        import traceback
                        st.write(traceback.format_exc())
        
        except Exception as e:
            st.error(f"❌ Erro ao ler ficheiro: {e}")

with tab3:
    st.title("ℹ️ Como Usar")
    
    st.markdown("""
    ### 📦 Converter Tab
    Selecione o cliente e faça upload do ficheiro para converter para Excel PHC.
    
    ### 💰 Financial Control Tab
    1. Carregue o Excel preenchido
    2. Click "Processar Dados"
    3. Download relatório **agrupado por CPO/SPO** com:
       - Totais de quantidades (soma)
       - Todas as outras colunas (primeira ocorrência)
    """)
