"""
Compiler Coding Activity No.2 — Problem 1
Streaming subscription monthly bill (plan, country, data used, loyalty discount, tax).
"""

from decimal import Decimal, ROUND_HALF_UP


def money(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def main() -> None:
    try:
        plan = int(input("Plan Type (1-Basic, 2-Standard, 3-Premium): ").strip())
    except ValueError:
        print("Invalid Plan Selected. Exiting the program...")
        return

    if plan not in (1, 2, 3):
        print("Invalid Plan Selected. Exiting the program...")
        return

    try:
        country = int(input("Country Code (1-US, 2-UK, 3-PH, 4-OTHERS): ").strip())
    except ValueError:
        print("Invalid Country Code Selected. Exiting the program...")
        return

    if country not in (1, 2, 3, 4):
        print("Invalid Country Code Selected. Exiting the program...")
        return

    raw_data = input("Data Used (GB): ").strip()
    try:
        data_used = Decimal(raw_data)
    except Exception:
        print("Invalid Value for Data Used. Exiting the program...")
        return

    if data_used < 0 or data_used != data_used.to_integral_value():
        print("Invalid Value for Data Used. Exiting the program...")
        return

    base_prices = {1: Decimal("9.99"), 2: Decimal("15.99"), 3: Decimal("19.99")}
    tax_rates = {1: Decimal("0.08"), 2: Decimal("0.20"), 3: Decimal("0.12"), 4: Decimal("0.15")}
    tax_labels = {1: 8, 2: 20, 3: 12, 4: 15}

    base = base_prices[plan]
    if plan == 1 and data_used > 199:
        subtotal = money(base * Decimal("0.97"))
    elif plan == 2 and data_used > 299:
        subtotal = money(base * Decimal("0.95"))
    elif plan == 3 and data_used > 499:
        subtotal = money(base * Decimal("0.90"))
    else:
        subtotal = base

    tax_rate = tax_rates[country]
    total = money(subtotal * (Decimal("1") + tax_rate))

    print()
    print(f"Subtotal ($): {subtotal}")
    print(f"Tax Rate (%): {tax_labels[country]}")
    print(f"Total Monthly Bill ($): {total}")


if __name__ == "__main__":
    main()
