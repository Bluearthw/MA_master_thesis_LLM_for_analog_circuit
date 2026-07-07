import pymupdf4llm
import os
# Replace with the path to your 2-column thesis PDF
pdf_name = "Efficient Analog Circuit Sizing with Domain-Guided Sampling and_advpub_2025CDP0005.pdf"
pdf_path = r"material\\papers_found\\july\\" + pdf_name 
os.path.exists(pdf_path) or exit(f"❌ PDF not found at '{pdf_path}'. Please check the path.")
print("Processing layout and separating columns...")

# This extracts standard text, merges multi-columns into the true reading flow,
# and converts tables into clean Markdown markdown.
md_text = pymupdf4llm.to_markdown(pdf_path)

# Save to a clean markdown file
output_dir = os.path.join("material", "clean_md")
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, f"cleaned_{pdf_name.replace('.pdf', '')}.md")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(md_text)

print(f"🎉 Success! Column structure corrected. Open '{output_path}' to review.")