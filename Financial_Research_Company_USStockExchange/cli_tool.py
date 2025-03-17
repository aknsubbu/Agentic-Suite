#!/usr/bin/env python3
"""
Stock Report Generator CLI - Generate beautiful PDF stock reports from stock analysis data.
"""
import argparse
import os
import sys
import json
from InfoFetch import StockAnalyzer
from ReportGeneration import StockReportGenerator

def main():
    parser = argparse.ArgumentParser(description="Generate stock analysis PDF reports")
    parser.add_argument("ticker", help="Stock ticker symbol (e.g., AAPL)")
    parser.add_argument("-i", "--input", help="Path to the input JSON file (optional, if not provided will generate new data)")
    parser.add_argument("-o", "--output-dir", default="reports", help="Directory to save the generated report")
    parser.add_argument("--skip-analysis", action="store_true", help="Skip analysis and use existing data file")
    
    args = parser.parse_args()
    ticker = args.ticker.upper()
    
    print(f"Processing stock report for {ticker}...")
    
    # Create the report output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize report generator
    report_gen = StockReportGenerator(ticker, output_dir=args.output_dir)
    
    # Determine if we need to generate analysis data or use existing file
    if args.skip_analysis and args.input:
        # Use existing data file
        input_file = args.input
        if not os.path.exists(input_file):
            print(f"Error: Input file {input_file} not found.")
            sys.exit(1)
            
        print(f"Using existing data from {input_file}")
        if not report_gen.load_data(input_file):
            print("Failed to load data from the input file.")
            sys.exit(1)
    else:
        # Generate fresh analysis data
        print(f"Fetching latest data for {ticker}...")
        try:
            # Initialize the stock analyzer
            analyzer = StockAnalyzer()
            
            # Get the analysis data
            analysis = analyzer.analyze_stock(ticker)
            
            if not analysis:
                print(f"Failed to analyze {ticker}. Check logs for details.")
                sys.exit(1)
                
            print(f"Successfully fetched data for {ticker}")
            
            # Store analysis data in output directory for reference
            output_file = os.path.join(args.output_dir, f"{ticker}_analysis_data.json")
            with open(output_file, 'w') as f:
                json.dump(analysis, f, indent=2)
            print(f"Saved analysis data to {output_file}")
            
            # Set the data directly without loading from file
            report_gen.set_data(analysis)
            
        except Exception as e:
            print(f"Error during analysis: {str(e)}")
            sys.exit(1)
    
    # Generate the report
    print(f"Generating PDF report for {ticker}...")
    pdf_file = report_gen.generate_report()
    print(f"Report successfully generated: {pdf_file}")


if __name__ == "__main__":
    main()