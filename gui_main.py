"""
2K Historical Draft Picker - GUI Version
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import os

from core import (
    get_current_year, save_current_year, increment_year,
    load_draft_weights, save_draft_weights, reset_weights,
    is_all_weights_zero, PseudoRandomPicker, random_lose_player,
    NBA_TEAMS, POSITIONS, COOL_DOWN_PERIOD, NUM_PLAYERS_TO_LOSE,
    INITIAL_SIMULATION_YEAR,
)
from i18n import t, set_language, get_language, SUPPORTED_LANGUAGES


class DraftApp:
    def __init__(self, root):
        self.root = root
        self.root.title(t("app_title"))
        self.root.geometry("800x600")

        style = ttk.Style()
        style.theme_use('clam')

        self.setup_ui()
        self.update_display()

    def setup_ui(self):
        # Main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title row with language switcher
        title_frame = ttk.Frame(self.main_frame)
        title_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        title_frame.columnconfigure(0, weight=1)

        self.title_label = ttk.Label(title_frame, text=t("app_title"),
                                     font=('Arial', 16, 'bold'))
        self.title_label.grid(row=0, column=0, sticky=tk.W)

        # Language switcher
        lang_frame = ttk.Frame(title_frame)
        lang_frame.grid(row=0, column=1, sticky=tk.E)

        self.lang_label = ttk.Label(lang_frame, text=t("language_label"))
        self.lang_label.grid(row=0, column=0, padx=(0, 5))

        self.lang_var = tk.StringVar(value=get_language())
        self.lang_combo = ttk.Combobox(lang_frame, textvariable=self.lang_var,
                                       values=SUPPORTED_LANGUAGES, width=5,
                                       state="readonly")
        self.lang_combo.grid(row=0, column=1)
        self.lang_combo.bind("<<ComboboxSelected>>", self.on_language_change)

        # Status frame
        self.status_frame = ttk.LabelFrame(self.main_frame, text=t("status_frame"), padding="10")
        self.status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        self.year_label = ttk.Label(self.status_frame, text=t("sim_year_loading"))
        self.year_label.grid(row=0, column=0, sticky=tk.W)

        self.available_label = ttk.Label(self.status_frame, text=t("available_count_loading"))
        self.available_label.grid(row=1, column=0, sticky=tk.W)

        self.cooling_label = ttk.Label(self.status_frame, text=t("cooling_count_loading"))
        self.cooling_label.grid(row=2, column=0, sticky=tk.W)

        # Button frame
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=(0, 10))

        self.run_draft_btn = ttk.Button(button_frame, text=t("btn_run_draft"),
                                        command=self.run_draft, width=15)
        self.run_draft_btn.grid(row=0, column=0, padx=5, pady=5)

        self.view_years_btn = ttk.Button(button_frame, text=t("btn_view_years"),
                                         command=self.view_available_years, width=15)
        self.view_years_btn.grid(row=0, column=1, padx=5, pady=5)

        self.reset_all_btn = ttk.Button(button_frame, text=t("btn_reset_all"),
                                        command=self.reset_all, width=15)
        self.reset_all_btn.grid(row=0, column=2, padx=5, pady=5)

        self.quit_btn = ttk.Button(button_frame, text=t("btn_quit"),
                                   command=self.quit_app, width=15)
        self.quit_btn.grid(row=0, column=3, padx=5, pady=5)

        # Result frame
        self.result_frame = ttk.LabelFrame(self.main_frame, text=t("draft_result_frame"), padding="10")
        self.result_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        self.result_text = scrolledtext.ScrolledText(self.result_frame,
                                                     height=15,
                                                     width=70,
                                                     font=('Courier New', 10))
        self.result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Years info
        self.years_frame = ttk.LabelFrame(self.main_frame, text=t("years_info_frame"), padding="10")
        self.years_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        self.years_info = ttk.Label(self.years_frame, text="")
        self.years_info.grid(row=0, column=0, sticky=tk.W)

        # Grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(2, weight=1)
        self.main_frame.rowconfigure(3, weight=1)
        self.result_frame.columnconfigure(0, weight=1)
        self.result_frame.rowconfigure(0, weight=1)

    def on_language_change(self, event=None):
        new_lang = self.lang_var.get()
        set_language(new_lang)
        self.refresh_all_text()

    def refresh_all_text(self):
        self.root.title(t("app_title"))
        self.title_label.config(text=t("app_title"))
        self.lang_label.config(text=t("language_label"))
        self.status_frame.config(text=t("status_frame"))
        self.run_draft_btn.config(text=t("btn_run_draft"))
        self.view_years_btn.config(text=t("btn_view_years"))
        self.reset_all_btn.config(text=t("btn_reset_all"))
        self.quit_btn.config(text=t("btn_quit"))
        self.result_frame.config(text=t("draft_result_frame"))
        self.years_frame.config(text=t("years_info_frame"))
        self.update_display()

    def update_display(self):
        current_year = get_current_year()
        self.year_label.config(text=t("sim_year", year=current_year))

        weights = load_draft_weights()
        available_years = [year for year, data in weights.items() if data['available'] == 1]
        cooling_years = [year for year, data in weights.items()
                         if data['available'] == 0 and data['last_used_year'] is not None]

        self.available_label.config(text=t("available_count", count=len(available_years)))
        self.cooling_label.config(text=t("cooling_count", count=len(cooling_years)))

        if available_years:
            if len(available_years) <= 10:
                detail = ", ".join(map(str, sorted(available_years)))
            else:
                detail = t("available_years_count", count=len(available_years))
            years_text = t("available_years_label", min=min(available_years),
                          max=max(available_years), detail=detail)
        else:
            years_text = t("no_available_years")

        self.years_info.config(text=years_text)

    def run_draft(self):
        try:
            current_sim_year = get_current_year()

            draft_weights = load_draft_weights()

            if is_all_weights_zero(draft_weights):
                messagebox.showinfo(t("auto_reset_title"), t("auto_reset"))
                draft_weights = reset_weights()

            available_years = [year for year, data in draft_weights.items() if data['available'] == 1]

            if not available_years:
                messagebox.showwarning(t("no_available_title"), t("no_available_msg"))
                return

            team_picker = PseudoRandomPicker(NBA_TEAMS)
            position_picker = PseudoRandomPicker(POSITIONS)
            year_picker = PseudoRandomPicker(available_years)

            selected_year = year_picker.pick()

            draft_weights[selected_year]['available'] = 0
            draft_weights[selected_year]['last_used_year'] = current_sim_year
            save_draft_weights(draft_weights)

            selected_players = []
            for _ in range(NUM_PLAYERS_TO_LOSE):
                team, position = random_lose_player(team_picker, position_picker)
                selected_players.append((team, position))

            selected_players.sort(key=lambda x: x[0])

            teams_dict = t("teams")
            positions_dict = t("positions")

            result_text = f"{t('draft_header')}\n"
            result_text += f"{t('selected_year', year=selected_year)}\n\n"
            result_text += t('year_used_cooldown', year=selected_year, cooldown=COOL_DOWN_PERIOD,
                             available_year=current_sim_year + COOL_DOWN_PERIOD) + "\n\n"

            result_text += f"{t('players_header', count=NUM_PLAYERS_TO_LOSE)}\n"
            for i, (team, position) in enumerate(selected_players):
                team_display = teams_dict.get(team, team)
                pos_display = positions_dict.get(position, position)
                result_text += t('player_line', index=i+1, team=team_display,
                                 position=pos_display, team_en=team) + "\n"

            new_sim_year = increment_year()
            result_text += t('time_advance', year=new_sim_year) + "\n"

            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, result_text)

            self.update_display()

        except Exception as e:
            messagebox.showerror(t("err_draft_title"), t("err_draft", error=str(e)))

    def view_available_years(self):
        try:
            weights = load_draft_weights()
            current_sim_year = get_current_year()

            available_years = []
            cooling_years = []

            for year, data in sorted(weights.items()):
                if data['available'] == 1:
                    available_years.append(str(year))
                elif data['last_used_year'] is not None:
                    remaining_years = COOL_DOWN_PERIOD - (current_sim_year - data['last_used_year'])
                    if remaining_years > 0:
                        cooling_years.append(t('cooling_year_item', year=year, remaining=remaining_years))

            result_text = f"{t('sim_year', year=current_sim_year)}\n\n"
            result_text += t('available_years_header') + "\n"
            if available_years:
                result_text += ", ".join(available_years) + "\n"
            else:
                result_text += t('no_available_years') + "\n"

            if cooling_years:
                result_text += f"\n{t('cooling_years_header', cooldown=COOL_DOWN_PERIOD)}\n"
                result_text += ", ".join(cooling_years) + "\n"

            result_text += f"\n{t('year_summary_short', available=len(available_years), cooling=len(cooling_years))}"

            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, result_text)

        except Exception as e:
            messagebox.showerror(t("err_draft_title"), t("err_view_years", error=str(e)))

    def reset_all(self):
        try:
            current_year = get_current_year()
            default_reset_year = int(os.environ.get('SIMULATION_START_YEAR', INITIAL_SIMULATION_YEAR))

            reset_year = simpledialog.askinteger(
                t("reset_dialog_title"),
                t("reset_dialog_prompt"),
                initialvalue=default_reset_year,
                parent=self.root
            )

            if reset_year is None:
                return

            confirm_message = t("confirm_reset_body", current_year=current_year, reset_year=reset_year)

            if messagebox.askyesno(t("confirm_reset_title"), confirm_message):
                weights = reset_weights()
                save_current_year(reset_year)

                messagebox.showinfo(t("reset_success_title"),
                                    t("reset_success_body", reset_year=reset_year))

                self.update_display()

                available_years = [year for year, data in weights.items() if data['available'] == 1]

                years_text = t("reset_after_years", year=reset_year) + "\n"
                if available_years:
                    years_text += ", ".join(map(str, sorted(available_years)))
                else:
                    years_text += t("no_available_years")

                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(tk.END, years_text)

        except Exception as e:
            messagebox.showerror(t("err_draft_title"), t("err_reset", error=str(e)))

    def quit_app(self):
        if messagebox.askyesno(t("quit_title"), t("quit_confirm")):
            self.root.destroy()

def main():
    root = tk.Tk()
    app = DraftApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
