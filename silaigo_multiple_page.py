import tkinter as tk
from tkinter import ttk, messagebox
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PyPDF2 import PdfReader, PdfWriter
import io, os, tempfile
from datetime import datetime
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import textwrap
import subprocess
import sys
import sys
import os

# ---------------- BASE DIRECTORY ---------------- #
if getattr(sys, 'frozen', False):
    # Running as a bundled macOS app
    BASE_DIR = sys._MEIPASS
else:
    # Running in normal Python environment
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Paths for PDF template and font
PDF_TEMPLATE = os.path.join(BASE_DIR, "silaigo_invoice_final.pdf")
FONT_FILE = os.path.join(BASE_DIR, "segoeui.ttf")

# ---------------- PDF GENERATION ---------------- #

def generate_invoice(data, filename):
    """Generate multi-page invoice with static PDF layout"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(base_dir, "segoeui.ttf")
    pdfmetrics.registerFont(TTFont("SegoeUI", FONT_FILE))

    items_per_page = 10
    total_items = len(data["items"])
    total_pages = (total_items // items_per_page) + (1 if total_items % items_per_page else 0)
    if total_pages == 0:
        total_pages = 1

    output = PdfWriter()

    for page_no in range(total_pages):
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)
        can.setFont("SegoeUI", 12)

        # First page: header details
        if page_no == 0:
            can.drawString(130, 687, f"{data['invoice_no']}")
            can.drawString(90, 654, f"{data['date']}")
            can.drawString(400, 654, f"{data['payment_due']}")

            # Customer address
            text = can.beginText(295, 606)
            for line in data["bill_to"].split("\n"):
                text.textLine(line)
            can.drawText(text)

        # Items table for this page
        start = page_no * items_per_page
        end = start + items_per_page
        items_slice = data["items"][start:end]

        y = 480
        sr_no = start + 1
        for item in items_slice:
            desc, qty, rate, amount = item
            try:
                qty = int(qty)
            except:
                qty = 0
            try:
                rate = float(rate)
            except:
                rate = 0.0
            try:
                amount = float(amount)
            except:
                amount = 0.0

            can.drawString(78, y, str(sr_no))

            # Wrap description at ~8 words
            wrapped_lines = textwrap.wrap(str(desc), width=30)
            for line_count, line in enumerate(wrapped_lines):
                can.drawString(110, y - (line_count * 15), line)

            # Align qty, rate, amount with first line
            can.drawRightString(360, y, str(qty))
            can.drawRightString(450, y, f"{rate:.2f}")
            can.drawRightString(530, y, f"{amount:.2f}")

            y -= (30 * max(1, line_count + 1))
            sr_no += 1

        # Totals on last page only
        if page_no == total_pages - 1:
            can.drawRightString(540, 149, f"{data['subtotal']:.2f}")
            can.drawRightString(540, 124, f"{data['tax']:.2f}")
            can.drawRightString(540, 100, f"{data['total']:.2f}")
            can.drawRightString(540, 78, f"{data['advance']:.2f}")
            can.drawRightString(540, 53, f"{data['payment_due']:.2f}")
        else:
            can.drawRightString(540, 149, "NEXT PAGE")
            can.drawRightString(540, 124, "NEXT PAGE")
            can.drawRightString(540, 100, "NEXT PAGE")
            can.drawRightString(540, 78, "NEXT PAGE")
            can.drawRightString(540, 53, "NEXT PAGE")

        can.save()
        packet.seek(0)

        # Merge overlay with static layout
        existing_pdf_path = os.path.join(base_dir, "silaigo_invoice_final.pdf")
        existing_pdf = PdfReader(open(PDF_TEMPLATE, "rb"))
        overlay_pdf = PdfReader(packet)

        base_page = existing_pdf.pages[0]
        base_page.merge_page(overlay_pdf.pages[0])
        output.add_page(base_page)

    # Save final PDF
    with open(filename, "wb") as f:
        output.write(f)

# ---------------- GUI FUNCTIONS ---------------- #

def add_item():
    desc = entry_desc.get().strip()
    try:
        qty = int(entry_qty.get())
        rate = float(entry_rate.get())
    except ValueError:
        messagebox.showerror("Error", "Enter valid quantity and rate.")
        return
    amount = qty * rate

    sr_no = len(tree.get_children()) + 1
    tree.insert("", "end", values=(sr_no, desc, qty, rate, amount))

    entry_desc.delete(0, tk.END)
    entry_qty.delete(0, tk.END)
    entry_rate.delete(0, tk.END)
    update_totals()

def delete_item():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Warning", "Select an item to delete.")
        return
    for sel in selected:
        tree.delete(sel)
    for idx, child in enumerate(tree.get_children(), start=1):
        values = tree.item(child)["values"]
        values[0] = idx
        tree.item(child, values=values)
    update_totals()

def rebuild_items_from_tree():
    items = []
    for child in tree.get_children():
        items.append(tree.item(child)["values"][1:])
    return items

def update_totals():
    items = rebuild_items_from_tree()
    total = sum([float(i[3]) for i in items])

    if total > 0:
        subtotal = total / 1.05
        tax = total - subtotal
    else:
        subtotal = 0.0
        tax = 0.0

    try:
        advance = float(advance_entry.get())
    except ValueError:
        advance = 0.0

    payment_due = total - advance

    _set_readonly(entry_subtotal, f"{subtotal:.2f}")
    _set_readonly(entry_tax, f"{tax:.2f}")
    _set_readonly(entry_total, f"{total:.2f}")
    _set_readonly(entry_payment_due, f"{payment_due:.2f}")

def save_invoice():
    if not tree.get_children():
        messagebox.showerror("Error", "No items to generate invoice.")
        return
    data = collect_data()
    filename = f"invoice_{data['invoice_no']}.pdf"
    generate_invoice(data, filename)
    messagebox.showinfo("Success", f"Invoice saved as {filename}")

def open_file(path):
    """Open a file in the default app (macOS, Windows or Linux)."""
    if sys.platform.startswith("darwin"):
        subprocess.call(["open", path])
    elif os.name == "nt":
        os.startfile(path)
    else:
        # Linux xdg-open fallback
        try:
            subprocess.call(["xdg-open", path])
        except Exception:
            messagebox.showinfo("Info", f"Please open the file manually: {path}")

def preview_invoice():
    if not tree.get_children():
        messagebox.showerror("Error", "No items to preview.")
        return
    data = collect_data()
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp_file.close()
    generate_invoice(data, tmp_file.name)
    open_file(tmp_file.name)

def collect_data():
    return {
        "invoice_no": invoice_no_entry.get().strip(),
        "date": date_entry.get().strip(),
        "payment_due": payment_due_entry.get().strip(),
        "bill_to": bill_to_text.get("1.0", tk.END).strip(),
        "items": rebuild_items_from_tree(),
        "subtotal": float(entry_subtotal.get()),
        "tax": float(entry_tax.get()),
        "total": float(entry_total.get()),
        "advance": float(advance_entry.get() or 0.0),
        "payment_due": float(entry_payment_due.get()),
    }

def _set_readonly(widget, value):
    widget.config(state="normal")
    widget.delete(0, tk.END)
    widget.insert(0, value)
    widget.config(state="readonly")

# ---------------- GUI LAYOUT ---------------- #

root = tk.Tk()
root.title("Invoice Generator")

# Invoice details
frame_details = tk.LabelFrame(root, text="Invoice Details", padx=10, pady=10)
frame_details.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

tk.Label(frame_details, text="Invoice No").grid(row=0, column=0)
invoice_no_entry = tk.Entry(frame_details)
invoice_no_entry.grid(row=0, column=1)

tk.Label(frame_details, text="Date").grid(row=0, column=2)
date_entry = tk.Entry(frame_details)
date_entry.insert(0, datetime.today().strftime("%Y-%m-%d"))
date_entry.grid(row=0, column=3)

tk.Label(frame_details, text="Payment Due").grid(row=0, column=4)
payment_due_entry = tk.Entry(frame_details)
payment_due_entry.grid(row=0, column=5)

# Customer
frame_customer = tk.LabelFrame(root, text="Bill To", padx=10, pady=10)
frame_customer.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
bill_to_text = tk.Text(frame_customer, height=4, width=60)
bill_to_text.pack()

# Items
frame_items = tk.LabelFrame(root, text="Items", padx=10, pady=10)
frame_items.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

tk.Label(frame_items, text="Description").grid(row=0, column=0)
entry_desc = tk.Entry(frame_items, width=30)
entry_desc.grid(row=0, column=1)

tk.Label(frame_items, text="Qty").grid(row=0, column=2)
entry_qty = tk.Entry(frame_items, width=5)
entry_qty.grid(row=0, column=3)

tk.Label(frame_items, text="Rate").grid(row=0, column=4)
entry_rate = tk.Entry(frame_items, width=10)
entry_rate.grid(row=0, column=5)

tk.Button(frame_items, text="Add Item", command=add_item).grid(row=0, column=6, padx=5)
tk.Button(frame_items, text="Delete Item", command=delete_item).grid(row=0, column=7, padx=5)

tree = ttk.Treeview(frame_items, columns=("sr_no", "desc", "qty", "rate", "amount"), show="headings")
tree.heading("sr_no", text="Sr No")
tree.heading("desc", text="Description")
tree.heading("qty", text="Qty")
tree.heading("rate", text="Rate")
tree.heading("amount", text="Amount")
tree.grid(row=1, column=0, columnspan=8, pady=5)

# Totals
frame_totals = tk.LabelFrame(root, text="Totals", padx=10, pady=10)
frame_totals.grid(row=3, column=0, sticky="ew", padx=10, pady=5)

tk.Label(frame_totals, text="Subtotal").grid(row=0, column=0)
entry_subtotal = tk.Entry(frame_totals, state="readonly")
entry_subtotal.grid(row=0, column=1)

tk.Label(frame_totals, text="Tax (5%)").grid(row=1, column=0)
entry_tax = tk.Entry(frame_totals, state="readonly")
entry_tax.grid(row=1, column=1)

tk.Label(frame_totals, text="Total").grid(row=2, column=0)
entry_total = tk.Entry(frame_totals, state="readonly")
entry_total.grid(row=2, column=1)

tk.Label(frame_totals, text="Advance").grid(row=3, column=0)
advance_entry = tk.Entry(frame_totals)
advance_entry.grid(row=3, column=1)
advance_entry.insert(0, "0.00")
advance_entry.bind("<KeyRelease>", lambda e: update_totals())

tk.Label(frame_totals, text="Payment Due").grid(row=4, column=0)
entry_payment_due = tk.Entry(frame_totals, state="readonly")
entry_payment_due.grid(row=4, column=1)

# Buttons
frame_actions = tk.Frame(root, pady=10)
frame_actions.grid(row=4, column=0)

tk.Button(frame_actions, text="Preview PDF", command=preview_invoice, bg="orange", width=20).grid(row=0, column=0, padx=5)
tk.Button(frame_actions, text="Generate PDF", command=save_invoice, bg="green", fg="white", width=20).grid(row=0, column=1, padx=5)

# Initialize totals
_set_readonly(entry_subtotal, "0.00")
_set_readonly(entry_tax, "0.00")
_set_readonly(entry_total, "0.00")
_set_readonly(entry_payment_due, "0.00")

root.mainloop()