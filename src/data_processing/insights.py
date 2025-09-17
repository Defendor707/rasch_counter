import io
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

def compute_advanced_insights(results_df: pd.DataFrame, data_df: pd.DataFrame | None, beta_values: np.ndarray | None):
    insights = {}

    # Growth trend (approximate): moving average over sorted Standard Score
    if 'Standard Score' in results_df.columns:
        ss = results_df['Standard Score'].astype(float).sort_values().reset_index(drop=True)
        window = max(3, len(ss)//10) if len(ss) > 0 else 3
        growth = ss.rolling(window=window, min_periods=1).mean()
        insights['growth_series'] = growth.values.tolist()
        insights['growth_window'] = window
        insights['growth_start'] = float(growth.iloc[0]) if len(growth) else 0.0
        insights['growth_end'] = float(growth.iloc[-1]) if len(growth) else 0.0
        insights['growth_change'] = insights['growth_end'] - insights['growth_start']

    # Question fit diagnostics using difficulty and correctness
    if data_df is not None and beta_values is not None and len(beta_values) > 0:
        correctness = []
        for i in range(min(len(beta_values), data_df.shape[1]-1)):
            col = data_df.columns[i+1]
            total = len(data_df)
            correct = float(data_df[col].sum()) if total > 0 else 0.0
            p = (correct / total) if total > 0 else 0.0
            correctness.append(p)
        # Fit residual (simple heuristic): expected ~ logistic(-beta) baseline
        betas = np.array(beta_values[:len(correctness)], dtype=float)
        expected = 1.0/(1.0 + np.exp(betas))
        residual = np.array(correctness) - expected
        insights['question_fit'] = list(zip(range(1, len(residual)+1), betas.tolist(), residual.tolist()))
        insights['question_summary'] = [
            (int(i+1), float(betas[i]), float(correctness[i]*100.0), float(residual[i]))
            for i in range(len(correctness))
        ]
        # Top problematic (mismatch) and ideal (residual ~ 0)
        if len(residual) > 0:
            order = np.argsort(np.abs(residual))
            insights['ideal_questions'] = [(int(i+1), float(betas[i]), float(residual[i])) for i in order[:5]]
            worst = np.argsort(-np.abs(residual))
            insights['problem_questions'] = [(int(i+1), float(betas[i]), float(residual[i])) for i in worst[:5]]

    # Student outliers: z-scores of Standard Score
    if 'Standard Score' in results_df.columns:
        s = results_df['Standard Score'].astype(float)
        if len(s) > 1:
            z = (s - s.mean())/ (s.std(ddof=1) if s.std(ddof=1) > 0 else 1.0)
            results_df = results_df.copy()
            results_df['z'] = z
            # Top performers and at-risk
            top = results_df.sort_values('z', ascending=False).head(5)
            low = results_df.sort_values('z', ascending=True).head(5)
            insights['top_students'] = list(zip(top.get('Student ID', top.index).astype(str), top['Standard Score'].round(2).tolist(), top['z'].round(2).tolist()))
            insights['at_risk_students'] = list(zip(low.get('Student ID', low.index).astype(str), low['Standard Score'].round(2).tolist(), low['z'].round(2).tolist()))

    return insights


def build_insights_pdf(results_df: pd.DataFrame,
                       insights: dict,
                       title: str = "TAHLIL VA MASLAHATLAR") -> io.BytesIO:
    from reportlab.lib.units import mm
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import io as _io

    pdf_data = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_data, pagesize=landscape(A4),
        rightMargin=10*mm, leftMargin=10*mm, topMargin=15*mm, bottomMargin=15*mm,
        title=title
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, alignment=TA_CENTER, spaceAfter=10, textColor=colors.HexColor("#1F497D"))
    h2 = ParagraphStyle('H2', parent=styles['Heading2'], alignment=TA_LEFT)
    normal = styles['Normal']

    elements = []
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 6*mm))

    # Growth section
    if 'growth_series' in insights and len(insights['growth_series']) > 1:
        elements.append(Paragraph("O'sish sur'ati (harakatlanuvchi o'rtacha)", h2))
        buf = _io.BytesIO()
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.plot(insights['growth_series'], color='#1E88E5', linewidth=2)
        ax.set_xlabel('Talabalar (tartiblangan)')
        ax.set_ylabel('Standart ball (MA)')
        ax.set_title(f"O'sish: {insights['growth_change']:.2f}")
        plt.tight_layout()
        fig.savefig(buf, format='png', dpi=150)
        plt.close(fig)
        buf.seek(0)
        elements.append(Image(buf, width=160*mm, height=80*mm))
        elements.append(Spacer(1, 4*mm))

    # Recommendations based on question fit
    if 'question_fit' in insights:
        elements.append(Paragraph("Maslahatlar (savollar bo'yicha)", h2))
        tips = []
        if insights.get('problem_questions'):
            pq = ", ".join([f"Q{q} (rez={res:.2f})" for q, b, res in insights['problem_questions']])
            tips.append(f"Muammo ehtimoli yuqori savollar: {pq}. Shkalani qayta ko'rib chiqing yoki keyslarni tekshiring.")
        if insights.get('ideal_questions'):
            iq = ", ".join([f"Q{q} (rez={res:.2f})" for q, b, res in insights['ideal_questions']])
            tips.append(f"Ideal savollar (moslik yuqori): {iq}. Shunga o'xshash savollarni ko'paytirish mumkin.")
        if not tips:
            tips.append("Savollar mosligi yetarlicha barqaror ko'rinmoqda.")
        for t in tips:
            elements.append(Paragraph(f"• {t}", normal))
        elements.append(Spacer(1, 4*mm))

    # Question percent-correct chart
    if insights.get('question_summary'):
        elements.append(Paragraph("Savollar bo'yicha to'g'ri javoblar (%)", h2))
        buf = _io.BytesIO()
        fig, ax = plt.subplots(figsize=(7, 3))
        qs = [q for q, b, pc, r in insights['question_summary']]
        pcs = [pc for q, b, pc, r in insights['question_summary']]
        ax.bar(qs, pcs, color='#2E7D32')
        ax.set_xlabel('Savol #')
        ax.set_ylabel('To\'g\'ri (%)')
        ax.set_ylim(0, 100)
        plt.tight_layout()
        fig.savefig(buf, format='png', dpi=150)
        plt.close(fig)
        buf.seek(0)
        elements.append(Image(buf, width=180*mm, height=75*mm))
        elements.append(Spacer(1, 4*mm))

    # Question summary table (top 15 by absolute residual)
    if insights.get('question_summary'):
        elements.append(Paragraph("Savollar bo'yicha ko'rsatkichlar (Top 15 reziduala ko'ra)", h2))
        sorted_q = sorted(insights['question_summary'], key=lambda x: abs(x[3]), reverse=True)[:15]
        rows = [["Savol", "Qiyinlik (β)", "To'g'ri (%)", "Rezidual"]]
        for q, b, pc, r in sorted_q:
            rows.append([f"Q{q}", f"{b:.2f}", f"{pc:.1f}", f"{r:.2f}"])
        t2 = Table(rows, colWidths=[25*mm, 40*mm, 35*mm, 30*mm])
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        elements.append(t2)

    # Student-level insights
    elements.append(Paragraph("Talabalar bo'yicha kuzatuvlar", h2))
    table_rows = [["Tip", "Ism", "Standart ball", "Z-score"]]
    for label, key in [("TOP", 'top_students'), ("Risk", 'at_risk_students')]:
        for sid, sc, z in insights.get(key, []) or []:
            table_rows.append([label, str(sid), f"{float(sc):.2f}", f"{float(z):.2f}"])
    t = Table(table_rows, colWidths=[25*mm, 70*mm, 30*mm, 25*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    elements.append(t)

    doc.build(elements)
    pdf_data.seek(0)
    return pdf_data


