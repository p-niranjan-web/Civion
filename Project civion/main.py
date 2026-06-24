from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
import os
import tempfile
import json
import io
import uuid
from fpdf import FPDF

from parser import parse_user_specification
from auditor import run_civion_audit
from database import IS456_MASTER
from config import get_groq_client

os.makedirs("downloads", exist_ok=True)

app = FastAPI(title="Civion AI API")

# Allow CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    messages: list
    audit_context: dict = None

@app.post("/api/audit")
async def audit_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    try:
        # Create a temporary file to save the uploaded PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            content = await file.read()
            temp_pdf.write(content)
            temp_pdf_path = temp_pdf.name
            
        # Run parsing
        extracted_json = parse_user_specification(temp_pdf_path)
        
        # Clean up temp file
        os.remove(temp_pdf_path)
        
        if "error" in extracted_json:
            raise HTTPException(status_code=500, detail=f"Parsing Error: {extracted_json['error']}")
            
        # Run audit
        audit_results = run_civion_audit(extracted_json, IS456_MASTER)
        
        # We can also return the extracted raw json for the chat context
        audit_results["raw_extracted_data"] = extracted_json
        
        return audit_results
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        client = get_groq_client()
        
        # Build the system prompt
        system_prompt = "You are Civion AI, a professional civil engineering compliance assistant."
        if request.audit_context:
            # Add context to system prompt
            context_str = json.dumps(request.audit_context, indent=2)
            system_prompt += f"\n\nYou are currently assisting the user with the following audit report context:\n{context_str}\n\nDo not use informal language or emojis. Provide clear, professional engineering guidance based on IS 456:2000."
            
        # Format messages for Groq API
        formatted_messages = [{"role": "system", "content": system_prompt}]
        
        for msg in request.messages:
            role = "user" if msg.get("role") == "user" else "assistant"
            formatted_messages.append({"role": role, "content": msg.get("content", "")})
            
        chat_completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=formatted_messages,
            temperature=0.3
        )
        
        response_text = chat_completion.choices[0].message.content
        return {"response": response_text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat Error: {str(e)}")

@app.post("/api/report/download")
async def download_report(payload: dict):
    try:
        counts = payload.get("counts", {})
        ledger = payload.get("ledger", [])
        traceability = payload.get("traceability", [])
        
        pdf = FPDF()
        pdf.add_page()
        
        # Add Logo
        logo_path = os.path.join("assets", "civion_logo.png")
        if os.path.exists(logo_path):
            pdf.image(logo_path, x=10, y=8, w=30)
            
        pdf.set_font("Helvetica", style="B", size=20)
        pdf.cell(40) # move right to make room for logo
        pdf.cell(0, 10, "Civion AI Compliance Report", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(20)
        
        # Summary Metrics
        pdf.set_font("Helvetica", style="B", size=14)
        pdf.cell(0, 10, "Quality Audit Summary", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=12)
        pdf.cell(0, 8, f"Total Checks: {counts.get('total', 0)}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 180, 80) # Green
        pdf.cell(0, 8, f"Passed: {counts.get('pass', 0)}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(220, 40, 80) # Red
        pdf.cell(0, 8, f"Failed: {counts.get('fail', 0)}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(220, 140, 0) # Orange
        pdf.cell(0, 8, f"Warnings: {counts.get('warning', 0)}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(10)
        
        def trunc(s, max_len=30):
            val = str(s).replace('\n', ' ').replace('\r', '')
            val = val.replace('\u2013', '-').replace('\u2014', '-').replace('\u2018', "'").replace('\u2019', "'").replace('\u201c', '"').replace('\u201d', '"')
            val = val.encode('latin-1', 'replace').decode('latin-1')
            return val[:max_len] + "..." if len(val) > max_len else val

        # Ledger Table
        pdf.set_font("Helvetica", style="B", size=14)
        pdf.cell(0, 10, "Compliance Ledger", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", style="B", size=10)
        
        col_widths = [50, 40, 60, 30]
        headers = ["Metric", "Extracted Value", "Requirement", "Status"]
        for i, h in enumerate(headers):
            pdf.cell(col_widths[i], 10, h, border=1)
        pdf.ln()
        
        pdf.set_font("Helvetica", size=9)
        for row in ledger:
            pdf.cell(col_widths[0], 8, trunc(row.get("Metric", ""), 35), border=1)
            pdf.cell(col_widths[1], 8, trunc(row.get("Extracted Value", row.get("ExtractedValue", "")), 25), border=1)
            pdf.cell(col_widths[2], 8, trunc(row.get("Requirement", ""), 45), border=1)
            pdf.cell(col_widths[3], 8, trunc(row.get("Status", ""), 15), border=1)
            pdf.ln()
            
        pdf.ln(10)
        
        # Traceability Table
        pdf.add_page()
        pdf.set_font("Helvetica", style="B", size=14)
        pdf.cell(0, 10, "Engineering Traceability", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", style="B", size=10)
        
        t_widths = [50, 40, 100]
        t_headers = ["Parameter", "Extracted Value", "Source Quote"]
        for i, h in enumerate(t_headers):
            pdf.cell(t_widths[i], 10, h, border=1)
        pdf.ln()
        
        pdf.set_font("Helvetica", size=9)
        for row in traceability:
            pdf.cell(t_widths[0], 8, trunc(row.get("Parameter", ""), 35), border=1)
            pdf.cell(t_widths[1], 8, trunc(row.get("Extracted Value", row.get("ExtractedValue", "")), 25), border=1)
            pdf.cell(t_widths[2], 8, trunc(row.get("Source Quote", row.get("SourceQuote", "")), 75), border=1)
            pdf.ln()
            
        pdf_bytes = pdf.output()
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=Civion_Compliance_Report.pdf"}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/optimize")
async def optimize_specs(payload: dict):
    raw_data = payload.get("raw_data", {})
    adjustments = payload.get("adjustments", {})
    
    optimized_data = raw_data.copy()
    for k, v in adjustments.items():
        optimized_data[k] = v
        
    audit_results = run_civion_audit(optimized_data, IS456_MASTER)
    audit_results["raw_extracted_data"] = optimized_data
    
    counts = audit_results.get("counts", {})
    total = counts.get("total", 0)
    score = (counts.get("pass", 0) / total * 100) if total > 0 else 0
    audit_results["score"] = round(score, 1)
    
    return audit_results

@app.post("/api/report/optimized")
async def report_optimized(payload: dict):
    try:
        original_ledger = payload.get("original_ledger", [])
        optimized_ledger = payload.get("optimized_ledger", [])
        
        pdf = FPDF()
        pdf.add_page()
        
        logo_path = os.path.join("assets", "civion_logo.png")
        if os.path.exists(logo_path):
            pdf.image(logo_path, x=10, y=8, w=30)
            
        pdf.set_font("Helvetica", style="B", size=18)
        pdf.cell(40)
        pdf.cell(0, 10, "RECTIFIED IDEAL SPECIFICATION", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(15)
        
        def trunc(s, max_len=30):
            val = str(s).replace('\n', ' ').replace('\r', '')
            val = val.replace('\u2013', '-').replace('\u2014', '-').replace('\u2018', "'").replace('\u2019', "'").replace('\u201c', '"').replace('\u201d', '"')
            val = val.encode('latin-1', 'replace').decode('latin-1')
            return val[:max_len] + "..." if len(val) > max_len else val

        pdf.set_font("Helvetica", style="B", size=10)
        col_widths = [50, 40, 50, 40]
        headers = ["Metric", "Original Value", "Optimized Value", "Status"]
        for i, h in enumerate(headers):
            pdf.cell(col_widths[i], 10, h, border=1)
        pdf.ln()
        
        pdf.set_font("Helvetica", size=9)
        opt_map = {row.get("Metric", ""): row for row in optimized_ledger}
        
        for orig_row in original_ledger:
            metric = orig_row.get("Metric", "")
            orig_val = orig_row.get("Extracted Value", orig_row.get("ExtractedValue", ""))
            opt_row = opt_map.get(metric, {})
            opt_val = opt_row.get("Extracted Value", opt_row.get("ExtractedValue", ""))
            status = opt_row.get("Status", "")
            
            pdf.cell(col_widths[0], 8, trunc(metric, 30), border=1)
            pdf.cell(col_widths[1], 8, trunc(orig_val, 25), border=1)
            
            if orig_val != opt_val:
                pdf.set_text_color(0, 150, 50)
                pdf.cell(col_widths[2], 8, trunc(opt_val, 30), border=1)
                pdf.set_text_color(0, 0, 0)
            else:
                pdf.cell(col_widths[2], 8, trunc(opt_val, 30), border=1)
                
            pdf.cell(col_widths[3], 8, trunc(status, 20), border=1)
            pdf.ln()
            
        file_id = str(uuid.uuid4())
        # Use /tmp for serverless functions compliance
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, f"{file_id}.pdf")
        
        pdf.output(file_path)
        
        # Return a relative download endpoint so it works correctly under Vercel routes
        return {"download_url": f"/api/downloads/{file_id}"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/downloads/{file_id}")
async def get_download(file_id: str):
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, f"{file_id}.pdf")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/pdf", filename="Optimized_Specification.pdf")
    raise HTTPException(status_code=404, detail="File not found")
