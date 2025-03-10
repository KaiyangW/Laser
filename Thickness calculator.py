import numpy as np
from scipy.optimize import root
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk  # type: ignore # For modern-looking widgets

def calculate_cutoff_thickness(wavelength, n2, n1=1.52, n3=1.0):
    """
    Calculate the cut-off thickness for an organic laser waveguide for both TE0 and TE1 modes.
    
    Parameters:
    wavelength (float): The wavelength (λ₀) in nanometers
    n2 (float): Refractive index of organic gain medium layer
    n1 (float): Refractive index of glass substrate (default: 1.52)
    n3 (float): Refractive index of air (default: 1.0)
    
    Returns:
    tuple: Cut-off thickness (h_c) in nanometers for both TE0 and TE1 modes
    """
    try:
        # Validate inputs
        if n2 <= n1 or n1 <= n3:
            raise ValueError("Refractive indices must satisfy n2 > n1 > n3")
        if wavelength <= 0:
            raise ValueError("Wavelength must be positive")
            
        # Calculate common term
        term1 = wavelength / (2 * np.pi * np.sqrt(n2**2 - n1**2))
        sqrt_term = np.sqrt((n1**2 - n3**2)/(n2**2 - n1**2))
        
        # Calculate TE0 mode
        term2_TE0 = np.arctan(sqrt_term)
        h_c_TE0 = term1 * term2_TE0
        
        # Calculate TE1 mode
        term2_TE1 = np.arctan(sqrt_term) + np.pi
        h_c_TE1 = term1 * term2_TE1
        
        return h_c_TE0, h_c_TE1
    except ValueError as e:
        raise e
    except Exception as e:
        raise ValueError(f"Calculation error: {str(e)}")

def equation(neff, d, k0, n1, n2, n3):
    """
    Implicit equation F(neff, d) = 0 for waveguide mode solution
    """
    term1 = k0 * d * np.sqrt(n2**2 - neff**2)
    term2 = np.arctan(np.sqrt((neff**2 - n1**2) / (n2**2 - neff**2)))
    term3 = np.arctan(np.sqrt((neff**2 - n3**2) / (n2**2 - neff**2)))
    return term1 - term2 - term3

def neff_vs_d(d_values, wavelength, n1, n2, n3):
    """
    Calculate n_eff for a range of thickness values
    """
    k0 = 2 * np.pi / (wavelength * 1e-9)  # Convert wavelength to meters
    neff_results = []
    
    for d in d_values:
        d_meters = d * 1e-9  # Convert nm to meters
        neff_guess = (n1 + n2) / 2
        result = root(equation, neff_guess, args=(d_meters, k0, n1, n2, n3))
        
        if result.success:
            neff_results.append(result.x[0])
        else:
            neff_results.append(np.nan)
    
    return np.array(neff_results)

def find_optimal_thickness(wavelength, n2, n1=1.52, n3=1.0, grating_period=350):
    """
    Find the optimal thickness where n_eff matches the grating condition
    """
    # Calculate target n_eff from grating period
    n_eff_target = wavelength / grating_period
    
    # Get cutoff thicknesses
    d_TE0, d_TE1 = calculate_cutoff_thickness(wavelength, n2, n1, n3)
    
    # Create thickness array between TE0 and TE1
    d_values = np.linspace(d_TE0, d_TE1, 200)  # 200 points for good resolution
    
    # Calculate n_eff for each thickness
    neff_values = neff_vs_d(d_values, wavelength, n1, n2, n3)
    
    # Find thickness where n_eff is closest to target
    valid_indices = ~np.isnan(neff_values)
    if not np.any(valid_indices):
        raise ValueError("No valid solutions found")
    
    diff = np.abs(neff_values[valid_indices] - n_eff_target)
    best_idx = np.argmin(diff)
    
    d_optimal = d_values[valid_indices][best_idx]
    n_eff_achieved = neff_values[valid_indices][best_idx]
    
    return d_optimal, n_eff_achieved, n_eff_target

class CutoffCalculatorGUI:
    def __init__(self):
        # Set up the main window
        self.root = ctk.CTk()
        self.root.title("DFB Organic Laser Calculator")
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate window size (scaled for 4K)
        window_width = int(screen_width * 0.35)
        window_height = int(screen_height * 0.65)
        
        # Center the window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Configure scaling for 4K
        scaling_factor = min(screen_width/1920, screen_height/1080)
        ctk.set_widget_scaling(scaling_factor)
        
        self.create_widgets()

    def create_widgets(self):
        # Create main frame
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(padx=20, pady=20, fill='both', expand=True)
        
        # Title
        title_label = ctk.CTkLabel(main_frame, 
                                 text="DFB Organic Laser Calculator",
                                 font=("Calibri", 22))
        title_label.pack(pady=10)
        
        # Input frame
        input_frame = ctk.CTkFrame(main_frame)
        input_frame.pack(padx=10, pady=10, fill='x')
        
        # Wavelength input
        wavelength_label = ctk.CTkLabel(input_frame, text="ASE Wavelength (nm):", font=("Calibri", 18))
        wavelength_label.pack(pady=5)
        self.wavelength_entry = ctk.CTkEntry(input_frame, placeholder_text="Enter wavelength", font=("Calibri", 18))
        self.wavelength_entry.pack(pady=5)
        
        # n2 input
        n2_label = ctk.CTkLabel(input_frame, text="n₂ (organic medium):", font=("Calibri", 18))
        n2_label.pack(pady=5)
        self.n2_entry = ctk.CTkEntry(input_frame, placeholder_text="Enter n₂", font=("Calibri", 18))
        self.n2_entry.pack(pady=5)
        
        # Fixed values display
        fixed_values_frame = ctk.CTkFrame(main_frame)
        fixed_values_frame.pack(padx=10, pady=10, fill='x')
        
        fixed_values_text = "Fixed Values:\nn₁ (glass) = 1.52\nn₃ (air) = 1.0\nGrating Period = 350 nm"
        fixed_values_label = ctk.CTkLabel(fixed_values_frame, text=fixed_values_text, font=("Calibri", 18))
        fixed_values_label.pack(pady=5)
        
        # Calculate button
        self.calc_button = ctk.CTkButton(main_frame, text="Calculate", font=("Calibri", 18), command=self.calculate)
        self.calc_button.pack(pady=10)
        
        # Results frame
        results_frame = ctk.CTkFrame(main_frame)
        results_frame.pack(padx=10, pady=10, fill='x')
        
        # Result labels
        self.te0_label = ctk.CTkLabel(results_frame, text="", font=("Calibri", 16))
        self.te0_label.pack(pady=5)
        
        self.te1_label = ctk.CTkLabel(results_frame, text="", font=("Calibri", 16))
        self.te1_label.pack(pady=5)
        
        self.thickness_range_label = ctk.CTkLabel(results_frame, text="", font=("Calibri", 16))
        self.thickness_range_label.pack(pady=5)
        
        # DFB optimization results
        self.neff_target_label = ctk.CTkLabel(results_frame, text="", font=("Calibri", 16))
        self.neff_target_label.pack(pady=5)
        
        self.optimal_thickness_label = ctk.CTkLabel(results_frame, text="", font=("Calibri", 16))
        self.optimal_thickness_label.pack(pady=5)
        
        self.neff_achieved_label = ctk.CTkLabel(results_frame, text="", font=("Calibri", 16))
        self.neff_achieved_label.pack(pady=5)

    def calculate(self):
        try:
            # Get and validate inputs
            wavelength = float(self.wavelength_entry.get())
            n2 = float(self.n2_entry.get())
            
            # Calculate cutoff thicknesses
            h_c_TE0, h_c_TE1 = calculate_cutoff_thickness(wavelength, n2)
            
            # Calculate optimal thickness and effective indices
            d_optimal, n_eff_achieved, n_eff_target = find_optimal_thickness(wavelength, n2)
            
            # Display results
            self.te0_label.configure(text=f"TE₀ cut-off thickness: {h_c_TE0:.2f} nm")
            self.te1_label.configure(text=f"TE₁ cut-off thickness: {h_c_TE1:.2f} nm")
            self.thickness_range_label.configure(
                text=f"Single-mode range: {h_c_TE0:.2f} nm to {h_c_TE1:.2f} nm"
            )
            
            # Display DFB optimization results
            self.neff_target_label.configure(
                text=f"Target n_eff (grating): {n_eff_target:.4f}"
            )
            self.optimal_thickness_label.configure(
                text=f"Optimal thickness: {d_optimal:.2f} nm"
            )
            self.neff_achieved_label.configure(
                text=f"Achieved n_eff: {n_eff_achieved:.4f}"
            )
            
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = CutoffCalculatorGUI()
    app.run()