#!/usr/bin/env python3
import subprocess
import os
import sys
import pandas as pd

# --- CONFIGURATION ---
SIRIL_CLI_PATH = "/Applications/siril.app/Contents/MacOS/siril-cli"


def get_dynamic_filename(fits_image_path):
    """
    Extracts the base name of the FITS file and creates a safe output file name.
    Example: '/path/M42 Orion.fits' -> 'siril_metrics_M42_Orion.txt'
    """
    base_file = os.path.basename(fits_image_path)
    name_part, _ = os.path.splitext(base_file)
    # Replace spaces with underscores just for the output file naming safety
    safe_name = name_part.replace(" ", "_")
    return f"siril_metrics_{safe_name}.txt"


def run_siril_analysis(fits_image_path, output_filename):
    """
    Spawns Siril CLI. Sets Siril's working directory to the FITS location 
    to safely load the image, but outputs the metrics back to your current terminal folder.
    """
    if not os.path.exists(fits_image_path):
        print(f"[-] Error: The target file '{fits_image_path}' does not exist.")
        return False

    # Break path components down cleanly
    abs_fits_path = os.path.abspath(fits_image_path)
    fits_dir = os.path.dirname(abs_fits_path)
    fits_filename = os.path.basename(abs_fits_path)
    
    # Point the target file path directly to the Current Working Directory
    current_working_dir = os.getcwd()
    full_output_path = os.path.join(current_working_dir, output_filename)

    # Clean out any old matching metrics file if it exists in the current folder
    if os.path.exists(full_output_path):
        os.remove(full_output_path)

    # To pass a path with potential spaces to the -out flag, Siril requires
    # the entire argument string to be quoted: "-out=path"
    out_flag = f'"-out={full_output_path}"'

    siril_commands = (
        f"requires 1.2.0\n"
        f"cd \"{fits_dir}\"\n"
        f"load \"{fits_filename}\"\n"
        f"autostretch\n"
        f"findstar -layer=1 {out_flag}\n"
        f"close\n"
    )

    print(f"[*] Sending instructions to Siril. Streaming application logs below:")
    print("-" * 60)
    
    try:
        process = subprocess.Popen(
            [SIRIL_CLI_PATH, "-s", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(input=siril_commands)
        
        # Display Siril logs directly to user console
        print(stdout)
        if stderr:
            print(stderr)
        print("-" * 60)

        if "Found 0" in stdout or "No stars found" in stdout:
            print("[-] Detection Alert: Siril ran successfully but found 0 stars in this image frame.")
            return False
            
        if process.returncode != 0:
            print("[-] Error: Siril core process encountered a runtime crash.")
            return False
            
        return True

    except Exception as e:
        print(f"[-] Subprocess operational crash: {e}")
        return False


def parse_and_display_metrics(output_filename):
    """
    Parses the generated Siril file layout by skipping comment lines,
    calculates global averages, and isolates exactly 10 stars sitting
    closest to the median image brightness (magnitude).
    """
    current_working_dir = os.getcwd()
    full_output_path = os.path.join(current_working_dir, output_filename)

    if not os.path.exists(full_output_path):
        print(f"[-] Error: Siril finished processing but the data file was not found at:\n    {full_output_path}")
        return

    # Define the exact layout based on your Siril version's layout line
    custom_headers = [
        "star_id", "layer", "B", "A", "beta", "X", "Y", 
        "fwhm_x_px", "fwhm_y_px", "fwhm_x_arcsec", "fwhm_y_arcsec", 
        "angle", "rmse", "mag", "sat", "profile", "ra", "dec"
    ]

    try:
        # Parsed via whitespace separator while ignoring '#' comment rows
        df = pd.read_csv(
            full_output_path, 
            sep=r'\s+', 
            comment='#', 
            names=custom_headers,
            header=None
        )
    except Exception as e:
        print(f"[-] Error trying to parse the space-separated values: {e}")
        return

    if df.empty:
        print("[-] Error: The data file exists but contains 0 detected star data rows.")
        return

    # Force columns to numeric values, converting bad entries into NaN
    numeric_cols = ["fwhm_x_px", "fwhm_y_px", "fwhm_x_arcsec", "fwhm_y_arcsec", "X", "Y", "mag"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Drop any rows that failed to parse into numbers for core dimensions
    df = df.dropna(subset=["fwhm_x_px", "fwhm_y_px", "mag"])

    # Calculate Axis-Specific Averages across ALL stars
    avg_x_px = df["fwhm_x_px"].mean()
    avg_y_px = df["fwhm_y_px"].mean()
    avg_x_as = df["fwhm_x_arcsec"].mean()
    avg_y_as = df["fwhm_y_arcsec"].mean()
    roundness_ratio = avg_y_px / avg_x_px if avg_x_px != 0 else 0

    print("=" * 75)
    print("      TRUE GLOBAL AXIS-SPECIFIC AVERAGES (ALL STARS)")
    print("=" * 75)
    print(f"Total Stars Processed : {len(df)}")
    print(f"Average FWHM X-Axis   : {avg_x_px:.4f} px  ({avg_x_as:.4f} arcsec)")
    print(f"Average FWHM Y-Axis   : {avg_y_px:.4f} px  ({avg_y_as:.4f} arcsec)")
    print(f"Aspect Ratio (Y/X)    : {roundness_ratio:.4f} (1.0 = Perfect Circle)")
    
    # --- MEDIAN BRIGHTNESS ISOLATION WORKFLOW ---
    median_mag = df["mag"].median()
    df["dist_from_median"] = (df["mag"] - median_mag).abs()
    
    # Sort ascending by proximity to median and pick the top 10
    median_stars_df = df.sort_values(by="dist_from_median").head(10)
    median_stars_df = median_stars_df.sort_values(by="star_id")

    print("\n" + "=" * 75)
    print(f"      DETAILED MATRIX: 10 STARS CLOSEST TO MEDIAN BRIGHTNESS ({median_mag:.2f} mag)")
    print("=" * 75)
    
    # Format and slice display columns
    detailed_view = median_stars_df[["star_id", "X", "Y", "mag", "fwhm_x_px", "fwhm_y_px", "fwhm_x_arcsec", "fwhm_y_arcsec"]].copy()
    detailed_view.columns = ["ID", "X_Pos", "Y_Pos", "Magnitude", "FWHMx[px]", "FWHMy[px]", "FWHMx[\"]", "FWHMy[\"]"]
    
    print(detailed_view.to_string(index=False))
    print("=" * 75)
    print(f"\n[+] Processing complete. Analysis metrics file saved to current directory:\n    {full_output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 siril_psf_analyzer.py /path/to/your_image.fits")
        sys.exit(1)

    target_image = sys.argv[1]
    
    # Generate the dynamic name linked to the FITS image name
    dynamic_export_name = get_dynamic_filename(target_image)
    
    if run_siril_analysis(target_image, dynamic_export_name):
        parse_and_display_metrics(dynamic_export_name)

