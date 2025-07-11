import random
import streamlit as st
import matplotlib.pyplot as plt
import csv
import os
from datetime import datetime
from collections import defaultdict
import openpyxl
from io import BytesIO
from fpdf import FPDF

FILENAME = "expenses.csv"


def is_valid_amount(amount):
    try:
        float(amount)
        return True
    except ValueError:
        return False


def read_expenses():
    if not os.path.exists(FILENAME):
        return []
    with open(FILENAME, mode='r') as file:
        return list(csv.reader(file))


def write_expenses(expenses):
    with open(FILENAME, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(expenses)


def generate_excel(expenses):
    output = BytesIO()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Expenses"
    ws.append(["Date", "Amount", "Category", "Note"])
    for row in expenses:
        ws.append(row)
    wb.save(output)
    output.seek(0)
    return output


def generate_pdf(expenses):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Expense Report", ln=True, align='C')
    pdf.ln(10)
    for row in expenses:
        line = f"Date: {row[0]}, Amount: R{row[1]}, Category: {row[2]}, Note: {row[3]}"
        pdf.multi_cell(0, 10, line)
    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    return output


def financial_feedback(total, budget=None):
    if total == 0:
        return "No expenses recorded. Start tracking to understand your habits."
    feedback = ""
    if total < 1000:
        feedback += "You're doing great! Keep up the low spending habits."
    elif total < 5000:
        feedback += "You're managing fairly well, but review any non-essentials."
    elif total < 10000:
        feedback += "Consider budgeting more strictly and cutting excesses."
    else:
        feedback += "Warning: High spending! Analyze where most of your money is going."

    if budget:
        if total > budget:
            feedback += f" You have exceeded your budget of R{budget:.2f}. Consider cutting back next month."
        else:
            feedback += f" You are within your budget of R{budget:.2f}. Well done!"
    return feedback


def show_random_tip():
    tips = [
        "Track your spending daily to avoid surprises.",
        "Group similar expenses to understand patterns.",
        "Always categorize your income separately.",
        "Try to save at least 10% of your monthly income.",
        "Review your top 3 expense categories weekly.",
        "Use the summary graph to find spending leaks.",
        "Avoid emotional spending — pause before buying."
    ]
    return random.choice(tips)


def tip_based_on_expenses(expenses):
    if not expenses:
        return "Start logging your expenses to get personalized tips!"
    tips = [
        "Have you considered using separate categories for fixed vs variable expenses?",
        "Look at your most frequent category — is there a way to reduce it?",
        "Use spending caps per category to better control your budget.",
        "Consider using cash for categories where you overspend digitally.",
        "High spending in one area? Try a weekly spending freeze for it."
    ]
    return random.choice(tips)


def main():
    st.title("Financial Expense Tracker")

    # --- Salary Setup ---
    if "salary" not in st.session_state:
        st.session_state.salary = None

    st.sidebar.markdown("### Enter Monthly Salary")
    salary_input = st.sidebar.number_input(
        "Your monthly salary (R)", min_value=0.0, format="%.2f")
    if salary_input:
        st.session_state.salary = salary_input
        st.sidebar.success(f"Salary recorded: R{salary_input:.2f}")

    # --- Menu Options ---
    menu = [
        "Add Expense", "View Expenses", "View Total", "Delete Expense",
        "Edit Expense", "Filter Expenses", "Sort Expenses",
        "Summary by Category", "Export to Excel", "Visualize Category Breakdown",
        "Financial Management Report"
    ]
    choice = st.sidebar.selectbox("Choose Action", menu)

    if choice == "Add Expense":
        st.subheader("Add a New Expense")
        amount = st.number_input("Amount (R)", min_value=0.0, format="%.2f")
        category = st.text_input("Category")
        note = st.text_input("Note")
        if st.button("Add Expense"):
            date = datetime.now().strftime("%Y-%m-%d %H:%M")
            with open(FILENAME, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([date, amount, category, note])
            st.success("Expense added!")

    elif choice == "View Expenses":
        expenses = read_expenses()
        if expenses:
            st.subheader("Expense Records")
            st.table(expenses)
            col1, col2 = st.columns(2)
            with col1:
                excel_data = generate_excel(expenses)
                st.download_button("Download as Excel",
                                   excel_data, file_name="expenses.xlsx")
            with col2:
                pdf_data = generate_pdf(expenses)
                st.download_button("Download as PDF", pdf_data,
                                   file_name="expenses.pdf")
        else:
            st.info("No expenses recorded yet.")

    elif choice == "View Total":
        expenses = read_expenses()
        total = sum(float(row[1]) for row in expenses)
        st.metric("Total Expenses", f"R{total:.2f}")

        if st.session_state.salary:
            salary = st.session_state.salary
            percent_used = (total / salary) * 100
            st.write(
                f"You've spent **{percent_used:.2f}%** of your salary (R{salary:.2f}).")
            if percent_used > 70:
                st.warning(
                    "Over 70% of your income spent. Consider adjusting your expenses.")
            else:
                st.success("You're within a safe spending range.")
        else:
            st.info("Please enter your salary in the sidebar to see usage insights.")

        st.info("" + show_random_tip())

    elif choice == "Delete Expense":
        expenses = read_expenses()
        if expenses:
            for i, row in enumerate(expenses):
                st.write(f"{i}: {row}")
            idx = st.number_input(
                "Enter ID to delete", min_value=0, max_value=len(expenses)-1, step=1)
            if st.button("Delete"):
                removed = expenses.pop(idx)
                write_expenses(expenses)
                st.success(f"Deleted: {removed}")
        else:
            st.info("No expenses to delete.")

    elif choice == "Edit Expense":
        expenses = read_expenses()
        if expenses:
            for i, row in enumerate(expenses):
                st.write(f"{i}: {row}")
            idx = st.number_input(
                "Enter ID to edit", min_value=0, max_value=len(expenses)-1, step=1)
            date, amount, category, note = expenses[idx]
            new_amount = st.text_input("Amount (R)", value=str(amount))
            new_category = st.text_input("Category", value=category)
            new_note = st.text_input("Note", value=note)
            if st.button("Save Changes"):
                if is_valid_amount(new_amount):
                    expenses[idx] = [date, float(
                        new_amount), new_category, new_note]
                    write_expenses(expenses)
                    st.success("Expense updated.")
                else:
                    st.error("Invalid amount entered.")
        else:
            st.info("No expenses to edit.")

    elif choice == "Filter Expenses":
        expenses = read_expenses()
        filter_type = st.radio("Filter by", ("Category", "Date"))
        if filter_type == "Category":
            category = st.text_input("Enter category to filter")
            filtered = [e for e in expenses if e[2].lower() ==
                        category.lower()]
        else:
            date = st.text_input("Enter date (YYYY-MM-DD)")
            filtered = [e for e in expenses if e[0].startswith(date)]
        st.table(filtered)

    elif choice == "Sort Expenses":
        expenses = read_expenses()
        sort_by = st.radio("Sort by", ("Date", "Amount"))
        if sort_by == "Date":
            expenses.sort(key=lambda x: datetime.strptime(
                x[0], "%Y-%m-%d %H:%M"))
        else:
            expenses.sort(key=lambda x: float(x[1]))
        st.table(expenses)

    elif choice == "Summary by Category":
        expenses = read_expenses()
        summary = defaultdict(float)
        for row in expenses:
            summary[row[2]] += float(row[1])
        for category, total in summary.items():
            st.write(f"{category}: R{total:.2f}")

    elif choice == "Export to Excel":
        expenses = read_expenses()
        if expenses:
            excel_data = generate_excel(expenses)
            st.download_button("Download as Excel",
                               excel_data, file_name="expenses.xlsx")
        else:
            st.info("No expenses to export.")

    elif choice == "Visualize Category Breakdown":
        expenses = read_expenses()
        if expenses:
            category_totals = defaultdict(float)
            for row in expenses:
                category_totals[row[2]] += float(row[1])
            labels = list(category_totals.keys())
            sizes = list(category_totals.values())
            fig, ax = plt.subplots()
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            st.pyplot(fig)
        else:
            st.info("No data to visualize.")

    elif choice == "Financial Management Report":
        expenses = read_expenses()
        if expenses:
            time_range = st.radio(
                "Evaluate for", ["This Month", "This Year", "All Time"])
            budget = st.number_input(
                "Enter your budget (R)", min_value=0.0, format="%.2f")
            now = datetime.now()
            if time_range == "This Month":
                filtered = [e for e in expenses if datetime.strptime(
                    e[0], "%Y-%m-%d %H:%M").month == now.month and datetime.strptime(e[0], "%Y-%m-%d %H:%M").year == now.year]
            elif time_range == "This Year":
                filtered = [e for e in expenses if datetime.strptime(
                    e[0], "%Y-%m-%d %H:%M").year == now.year]
            else:
                filtered = expenses

            total = sum(float(row[1]) for row in filtered)
            feedback = financial_feedback(total, budget=budget)
            st.subheader("Financial Report")
            st.write(f"**Total Spending ({time_range})**: R{total:.2f}")
            st.info(feedback)

            if st.session_state.salary:
                salary = st.session_state.salary
                percent_used = (total / salary) * 100
                st.write(
                    f"You've spent **{percent_used:.2f}%** of your monthly salary (R{salary:.2f}).")
                if percent_used > 70:
                    st.warning(
                        "Spending exceeds 70% of income. Consider budgeting more strictly.")
                else:
                    st.success("You're within a responsible range.")
            else:
                st.info(
                    "Please enter your salary in the sidebar to evaluate your financial health.")

            st.info("" + tip_based_on_expenses(filtered))
        else:
            st.info("No data to evaluate.")


if __name__ == "__main__":
    main()
