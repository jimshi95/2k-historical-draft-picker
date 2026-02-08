import sys
import os

from core import (
    get_current_year, save_current_year, increment_year,
    load_draft_weights, save_draft_weights, reset_weights,
    is_all_weights_zero, PseudoRandomPicker, random_lose_player,
    NBA_TEAMS, POSITIONS, COOL_DOWN_PERIOD, NUM_PLAYERS_TO_LOSE,
    INITIAL_SIMULATION_YEAR,
)
from i18n import t


def print_draft_weights(weights):
    current_sim_year = get_current_year()
    print(f"\n{t('sim_year', year=current_sim_year)}")
    print(t('available_years_header'))

    available_years = []
    cooling_years = []

    for year, data in sorted(weights.items()):
        if data['available'] == 1:
            available_years.append(str(year))
        elif data['last_used_year'] is not None:
            remaining_years = COOL_DOWN_PERIOD - (current_sim_year - data['last_used_year'])
            if remaining_years > 0:
                cooling_years.append(t('cooling_year_item', year=year, remaining=remaining_years))

    if available_years:
        print(t('available_label') + ", ".join(available_years))
    else:
        print(t('no_available_years'))

    if cooling_years:
        print(t('cooling_label') + ", ".join(cooling_years))

    print(t('year_summary', available=len(available_years), cooling=len(cooling_years), cooldown=COOL_DOWN_PERIOD))


def show_menu():
    current_sim_year = get_current_year()
    reset_year = os.environ.get('SIMULATION_START_YEAR') or INITIAL_SIMULATION_YEAR
    print(f"\n{t('menu_header', sim_year=current_sim_year)}")
    print(t('menu_run_draft'))
    print(t('menu_reset_all'))
    print(t('menu_view_years'))
    print(t('menu_reset_year', reset_year=reset_year))
    print(t('menu_quit'))
    choice = input(t('menu_prompt'))
    return choice


def run_draft():
    current_sim_year = get_current_year()

    draft_weights = load_draft_weights()

    if is_all_weights_zero(draft_weights):
        print(t('auto_reset'))
        draft_weights = reset_weights()

    available_years = [year for year, data in draft_weights.items() if data['available'] == 1]

    if not available_years:
        print(t('no_available_msg'))
        return

    team_picker = PseudoRandomPicker(NBA_TEAMS)
    position_picker = PseudoRandomPicker(POSITIONS)
    year_picker = PseudoRandomPicker(available_years)

    try:
        selected_year = year_picker.pick()
        print(f"\n{t('draft_header')}")
        print(t('selected_year', year=selected_year))

        draft_weights[selected_year]['available'] = 0
        draft_weights[selected_year]['last_used_year'] = current_sim_year
        print(t('year_used_cooldown', year=selected_year, cooldown=COOL_DOWN_PERIOD,
                available_year=current_sim_year + COOL_DOWN_PERIOD))

        print(f"\n{t('players_header', count=NUM_PLAYERS_TO_LOSE)}")
        selected_players = []
        for _ in range(NUM_PLAYERS_TO_LOSE):
            team, position = random_lose_player(team_picker, position_picker)
            selected_players.append((team, position))

        selected_players.sort(key=lambda x: x[0])

        teams_dict = t('teams')
        positions_dict = t('positions')
        for i, (team, position) in enumerate(selected_players):
            team_display = teams_dict.get(team, team)
            pos_display = positions_dict.get(position, position)
            print(t('player_line', index=i+1, team=team_display, position=pos_display, team_en=team))

        save_draft_weights(draft_weights)

        new_sim_year = increment_year()
        print(t('time_advance', year=new_sim_year))

        print_draft_weights(draft_weights)

    except ValueError as e:
        print(t('err_draft_fallback', error=e))
        print(t('err_draft_auto_reset'))
        reset_weights()


def main():
    while True:
        choice = show_menu()

        if choice == '1':
            run_draft()
            input(t('press_enter'))
        elif choice == '2':
            reset_weights()
            print(t('reset_success'))
            print_draft_weights(load_draft_weights())
            input(t('press_enter'))
        elif choice == '3':
            print_draft_weights(load_draft_weights())
            input(t('press_enter'))
        elif choice == '4':
            default_reset_year = int(os.environ.get('SIMULATION_START_YEAR', INITIAL_SIMULATION_YEAR))
            year_input = input(t('reset_year_prompt', default_year=default_reset_year)).strip()
            if year_input:
                try:
                    reset_year = int(year_input)
                except ValueError:
                    print(t('invalid_year'))
                    input(t('press_enter'))
                    continue
            else:
                reset_year = default_reset_year
            save_current_year(reset_year)
            reset_weights()
            print(t('year_reset_done', year=reset_year))
            input(t('press_enter'))
        elif choice == '0':
            print(t('goodbye'))
            sys.exit(0)
        else:
            print(t('invalid_choice'))

if __name__ == '__main__':
    main()
