# output_handler.py
def handle_output(display_option, symbol, stock_data, rating, csv_writer=None):
    """
    Handle the output of stock analysis based on the selected display option.
    """
    if display_option == "console":
        print(f"\n=== Analysis for {symbol} ===")
        print("=== Stock Information ===")
        for key, value in stock_data.items():
            print(f"{key.capitalize()}: {value}")
        print("\n=== Rating ===")
        print(f"The rating for {symbol} is: {rating}\n")
    elif display_option == "multiple":
        output_file = f"{symbol}_analysis.txt"
        with open(output_file, "w") as file:
            file.write("=== Stock Information ===\n")
            for key, value in stock_data.items():
                file.write(f"{key.capitalize()}: {value}\n")
            file.write("\n=== Rating ===\n")
            file.write(f"The rating for {symbol} is: {rating}\n\n")
        print(f"Analysis for {symbol} has been saved to {output_file}.")
    elif display_option == "one":
        with open("stock_analysis.txt", "a") as file:
            file.write(f"=== Analysis for {symbol} ===\n")
            file.write("=== Stock Information ===\n")
            for key, value in stock_data.items():
                file.write(f"{key.capitalize()}: {value}\n")
            file.write("\n=== Rating ===\n")
            file.write(f"The rating for {symbol} is: {rating}\n\n")
        print(f"Analysis for {symbol} has been added to stock_analysis.txt.")
    elif display_option == "csv" and csv_writer:
        csv_writer.writerow([
            stock_data.get("symbol", "N/A"),
            stock_data.get("long_name", "N/A"),
            stock_data.get("sector", "N/A"),
            stock_data.get("industry", "N/A"),
            stock_data.get("market_cap", "N/A"),
            stock_data.get("pe_ratio", "N/A"),
            stock_data.get("dividend_yield", "N/A"),
            stock_data.get("current_price", "N/A"),
            stock_data.get("recent_quarter", "N/A"),
            rating,
        ])
        print(f"Analysis for {symbol} has been added to stock_analysis.csv.")